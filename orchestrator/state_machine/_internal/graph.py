"""自写状态机(Phase 0B)。Phase 0C PoC 验证后接 LangGraph,public API 不变。

状态机:
    CREATED → PM_PLANNING → (validator) → DISPATCH 循环 → ROLE_EXECUTING ↔ DISPATCH
                                                                                  → DONE
                                                                                  → ESCALATED_TO_OWNER
                                                                                  → BUDGET_EXCEEDED

关键约束(v2.4):
- PM 输出 validator:RETRY_PM(上限 retry_limits.pm_validator_retry_max)/ FATAL,不 autofix
- 同 (subtask, role) attempt 上限 retry_limits.role_attempt_max,超过 ATTEMPT_LIMIT_REACHED
- high signal 累计 ≥ 3 escalate(或 immediate_escalate_required=true 立即 escalate)
- budget 超限立即 escalate
"""

from __future__ import annotations

import yaml
from pathlib import Path

from orchestrator._shared import (
    Artifact,
    CompletedRole,
    ContextPack,
    DispatchPlan,
    RoleConfig,
    RoleInvocationInput,
    TaskState,
)
from orchestrator.artifact import (
    get_current_artifact,
    list_artifacts,
    mark_superseded,
    write_artifact,
)
from orchestrator.budget import add_cost, is_over_budget
from orchestrator.dispatcher import (
    find_next_ready_role,
    find_upstream_role,
    process_signals,
    validate_dispatch_plan,
)
from orchestrator.event_log import write_event
from orchestrator.roles import RoleExecutionError, make_runner


def _change_status(state: TaskState, new_status: str) -> None:
    old = state.status
    state.status = new_status  # type: ignore[assignment]
    write_event(
        state.task.task_id,
        "STATE_CHANGED",
        actor="orchestrator",
        payload={"from": old, "to": new_status},
    )


def _build_context_pack_for_pm(state: TaskState, previous_violation: dict | None) -> ContextPack:
    return ContextPack(
        task_context={
            "title": state.task.title,
            "owner_request": state.task.owner_request,
            "success_criteria": state.task.success_criteria,
            "constraints": state.task.constraints,
            "budget_usd": state.task.budget_usd,
        },
        project_memory={},
        role_specific_data={
            "project_context": {
                "roles": [{"role_id": r.role_id, "description": r.description} for r in state.project.roles],
                "role_groups": {
                    k: {"description": g.description, "roles": g.roles}
                    for k, g in state.project.role_groups.items()
                },
            },
            "dispatch_policy": state.policy.model_dump(),
        },
        previous_violation=previous_violation,
    )


def _build_context_pack_for_role(
    state: TaskState, subtask_id: str, role_id: str
) -> ContextPack:
    # 找当前 subtask
    assert state.dispatch_plan is not None
    subtask = next(st for st in state.dispatch_plan.business_breakdown if st.subtask_id == subtask_id)
    business_goal = subtask.description
    # related_artifacts: 该 subtask 之前所有 role 的 current artifact
    related: list[Artifact] = []
    for s in sorted(subtask.role_sequence, key=lambda x: x.step):
        if s.role_id == role_id:
            break
        a = get_current_artifact(state.task.task_id, subtask_id, s.role_id)
        if a is not None:
            related.append(a)
    # 上次自己的 artifact(如果 attempt > 1,看 reviewer 之前的 review)
    self_prev = get_current_artifact(state.task.task_id, subtask_id, role_id)
    if self_prev is not None:
        related.append(self_prev)
    # signals 给当前 role 的(从 pending_concerns 筛)
    prior = [s for s in state.pending_concerns if s.target == role_id]
    return ContextPack(
        task_context={
            "title": state.task.title,
            "owner_request": state.task.owner_request,
            "success_criteria": state.task.success_criteria,
            "constraints": state.task.constraints,
        },
        business_goal=business_goal,
        success_criteria=subtask.success_criteria,
        related_artifacts=related,
        role_specific_data={
            "subtask_id": subtask_id,
            "task_type": subtask.task_type,
        },
    ), prior  # type: ignore[return-value]


def _ctx_for_role(state: TaskState, subtask_id: str, role_id: str):
    ctx, prior_signals = _build_context_pack_for_role(state, subtask_id, role_id)
    return ctx, prior_signals


def _escalate(state: TaskState, reason: str, detail: str = "") -> None:
    state.escalation_reason = reason
    state.escalation_detail = detail
    write_event(
        state.task.task_id,
        "ESCALATED",
        actor="orchestrator",
        payload={"reason": reason, "detail": detail},
    )
    _change_status(state, "ESCALATED_TO_OWNER")


def _pm_planning(state: TaskState) -> bool:
    """PM_PLANNING 阶段。返回 True 表示成功进入 DISPATCH,False 表示 escalate。"""
    _change_status(state, "PM_PLANNING")

    orchestrator_role_id = state.project.orchestrator_role_id()
    role_config = state.project.get_role(orchestrator_role_id)
    if role_config is None:
        _escalate(
            state,
            "config_error",
            f"orchestrator role {orchestrator_role_id} 未在 project.roles 找到",
        )
        return False

    previous_violation: dict | None = None
    max_retry = state.policy.retry_limits.pm_validator_retry_max

    while True:
        runner = make_runner(role_config, attempt=state.pm_retry_count + 1)
        write_event(
            state.task.task_id,
            "ROLE_INVOKED",
            actor=orchestrator_role_id,
            payload={"phase": "PM_PLANNING", "attempt": state.pm_retry_count + 1},
        )
        try:
            ctx = _build_context_pack_for_pm(state, previous_violation)
            inp = RoleInvocationInput(
                task_id=state.task.task_id,
                role_id=orchestrator_role_id,
                context_pack=ctx,
            )
            output = runner.execute(inp, max_retries=1)  # role 内部小重试 1 次
        except RoleExecutionError as e:
            _escalate(state, "pm_runner_failed", f"{e.kind}: {e.detail}")
            return False

        # 写 PM artifact + 累计 cost
        write_artifact(output.artifact)
        add_cost(state, output.cost_used.usd)
        write_event(
            state.task.task_id,
            "ROLE_RETURNED",
            actor=orchestrator_role_id,
            payload={
                "verdict": output.verdict,
                "artifact_id": output.artifact.artifact_id,
                "cost_usd": output.cost_used.usd,
            },
        )
        write_event(
            state.task.task_id,
            "BUDGET_CONSUMED",
            actor="orchestrator",
            payload={"used": output.cost_used.usd, "total": state.cost_used_usd},
        )

        # 处理 PM 发出的 signals
        sig_action = process_signals(state, output.signals_to_other_roles, orchestrator_role_id)
        if sig_action.escalate_now:
            _escalate(state, "pm_signal_escalate", sig_action.escalate_reason)
            return False

        # 校验 PM 输出
        result = validate_dispatch_plan(
            output.artifact.content,
            task=state.task,
            project=state.project,
            policy=state.policy,
        )

        if result.action == "PASS":
            assert result.normalized_plan is not None
            state.dispatch_plan = result.normalized_plan
            # 把 PM 的 verdict 也标 (mark completed,虽然 PM 不属于 subtask)
            return True

        if result.action == "FATAL":
            write_event(
                state.task.task_id,
                "PLAN_VALIDATION_FATAL",
                actor="orchestrator",
                payload={
                    "violation_type": result.violation_type,
                    "detail": result.violation_detail,
                },
            )
            _escalate(
                state,
                f"plan_validation_fatal_{result.violation_type}",
                result.violation_detail,
            )
            return False

        # RETRY_PM
        write_event(
            state.task.task_id,
            "PLAN_RETRY_REQUESTED",
            actor="orchestrator",
            payload={
                "violation_type": result.violation_type,
                "detail": result.violation_detail,
                "attempt": state.pm_retry_count + 1,
            },
        )
        state.pm_retry_count += 1
        if state.pm_retry_count > max_retry:
            _escalate(
                state,
                "pm_retry_exhausted",
                f"PM validator 已 retry {max_retry} 次,仍然失败:{result.violation_detail}",
            )
            return False
        previous_violation = {
            "violation_type": result.violation_type,
            "detail": result.violation_detail,
            "expected_action": result.expected_action,
        }


def _dispatch_loop(state: TaskState) -> None:
    """DISPATCH 循环。直到任务完成或 escalate。"""
    _change_status(state, "DISPATCH")

    max_attempt = state.policy.retry_limits.role_attempt_max

    while True:
        # 预算 / 信号兜底
        if is_over_budget(state):
            _escalate(state, "BUDGET_EXCEEDED", f"已花费 ${state.cost_used_usd:.4f} >= 预算 ${state.budget_usd:.2f}")
            return

        nxt = find_next_ready_role(state)
        if nxt is None:
            _change_status(state, "DONE")
            return

        subtask_id, role_id = nxt
        attempt = state.get_attempt(subtask_id, role_id)
        if attempt > max_attempt:
            write_event(
                state.task.task_id,
                "ATTEMPT_LIMIT_REACHED",
                actor="orchestrator",
                payload={
                    "subtask_id": subtask_id,
                    "role_id": role_id,
                    "attempt": attempt,
                    "max": max_attempt,
                },
            )
            _escalate(
                state,
                "attempt_limit_reached",
                f"subtask {subtask_id} role {role_id} 已尝试 {attempt - 1} 次,超过上限 {max_attempt}",
            )
            return

        write_event(
            state.task.task_id,
            "DISPATCH_DECISION",
            actor="orchestrator",
            payload={"next_role": role_id, "subtask_id": subtask_id, "attempt": attempt},
        )
        _change_status(state, "ROLE_EXECUTING")

        role_config = state.project.get_role(role_id)
        if role_config is None:
            _escalate(state, "config_error", f"role {role_id} 在 project.yaml 不存在(validator 应该已拦截?)")
            return

        # 跑 role
        runner = make_runner(
            role_config,
            attempt=attempt,
            mock_behavior=state.task.mock_behavior,
        )
        write_event(
            state.task.task_id,
            "ROLE_INVOKED",
            actor=role_id,
            payload={"subtask_id": subtask_id, "attempt": attempt},
        )
        try:
            ctx, prior_signals = _ctx_for_role(state, subtask_id, role_id)
            inp = RoleInvocationInput(
                task_id=state.task.task_id,
                subtask_id=subtask_id,
                role_id=role_id,
                context_pack=ctx,
                prior_role_signals=prior_signals,
            )
            output = runner.execute(inp, max_retries=1)
        except RoleExecutionError as e:
            _escalate(state, f"role_runner_failed_{role_id}", f"{e.kind}: {e.detail}")
            return

        # 写 artifact(并 mark 老的 superseded_by)
        if attempt > 1:
            old = get_current_artifact(state.task.task_id, subtask_id, role_id)
            if old is not None and old.artifact_id != output.artifact.artifact_id:
                mark_superseded(state.task.task_id, old.artifact_id, output.artifact.artifact_id)
        write_artifact(output.artifact)
        add_cost(state, output.cost_used.usd)
        write_event(
            state.task.task_id,
            "ROLE_RETURNED",
            actor=role_id,
            payload={
                "subtask_id": subtask_id,
                "verdict": output.verdict,
                "artifact_id": output.artifact.artifact_id,
                "attempt": attempt,
                "cost_usd": output.cost_used.usd,
            },
        )
        write_event(
            state.task.task_id,
            "BUDGET_CONSUMED",
            actor="orchestrator",
            payload={"used": output.cost_used.usd, "total": state.cost_used_usd},
        )

        # 记 completed_roles
        state.mark_role_completed(
            CompletedRole(
                subtask_id=subtask_id,
                role_id=role_id,
                attempt=attempt,
                verdict=output.verdict,
                artifact_id=output.artifact.artifact_id,
            )
        )

        # 处理 signals
        sig_action = process_signals(state, output.signals_to_other_roles, role_id)
        if sig_action.escalate_now:
            _escalate(state, "signal_escalate", sig_action.escalate_reason)
            return

        # verdict 路由
        if output.verdict == "success":
            _change_status(state, "DISPATCH")
            continue
        if output.verdict == "escalate":
            _escalate(
                state,
                f"role_escalate_{role_id}",
                f"role {role_id} 主动 escalate(attempt={attempt})",
            )
            return
        if output.verdict == "needs_changes":
            # 找上游
            upstream = find_upstream_role(state, subtask_id, role_id)
            if upstream is None:
                _escalate(
                    state,
                    "needs_changes_no_upstream",
                    f"subtask {subtask_id} role {role_id} 说 needs_changes,但它是第一个角色(无上游)",
                )
                return
            # 把上游的 completed 标记 "needs replay" — 实现:从 completed_roles 移除
            state.completed_roles = [
                c
                for c in state.completed_roles
                if not (c.subtask_id == subtask_id and c.role_id == upstream)
            ]
            # 注意:attempt_counts 不重置,这样下次 attempt 接着 +1
            _change_status(state, "DISPATCH")
            continue


def run_task(state: TaskState) -> TaskState:
    """主入口。跑完整状态机直到 terminal state。"""
    write_event(
        state.task.task_id,
        "TASK_CREATED",
        actor="owner",
        payload={"title": state.task.title, "project_id": state.task.project_id},
    )

    # CREATED → PM_PLANNING
    if not _pm_planning(state):
        return state

    # DISPATCH 循环
    _dispatch_loop(state)

    # terminal event
    if state.status == "DONE":
        write_event(
            state.task.task_id,
            "TASK_COMPLETED",
            actor="orchestrator",
            payload={"total_cost_usd": state.cost_used_usd},
        )
    else:
        write_event(
            state.task.task_id,
            "TASK_FAILED",
            actor="orchestrator",
            payload={
                "status": state.status,
                "reason": state.escalation_reason,
                "total_cost_usd": state.cost_used_usd,
            },
        )

    return state
