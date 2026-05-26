"""dispatch_plan validator(v2.4:只 RETRY_PM / FATAL,不 autofix)。

宪法第 12 条 v2.4:validator 不替 LLM 补漏。
- LLM 可能改对的错误 → RETRY_PM(missing/removed mandatory role / role_id 拼错 /
  task_type 不存在 / role_sequence 格式错)
- 只有 Owner 能改的错误 → FATAL escalate(引用不存在的 role_id / 依赖成环 / dispatch_policy 配错)

retry 上限通过 dispatch_policy.retry_limits.pm_validator_retry_max 配置(默认 1)。
"""

from __future__ import annotations

import re
from typing import Any

import yaml

from orchestrator._shared import (
    DispatchPlan,
    DispatchPolicy,
    ProjectConfig,
    RoleStep,
    Subtask,
    Task,
    ValidationResult,
)


def _levenshtein(a: str, b: str) -> int:
    """计算 Levenshtein 距离(短字符串够用,不引入依赖)。"""
    if a == b:
        return 0
    if len(a) < len(b):
        return _levenshtein(b, a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, start=1):
            curr[j] = min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + (0 if ca == cb else 1))
        prev = curr
    return prev[-1]


def _is_typo(unknown: str, known: list[str]) -> str | None:
    for k in known:
        if _levenshtein(unknown, k) <= 2:
            return k
    return None


def _has_cycle(plan: DispatchPlan) -> bool:
    """子任务依赖是否有环。"""
    deps = {st.subtask_id: list(st.dependencies) for st in plan.business_breakdown}
    visiting: set[str] = set()
    visited: set[str] = set()

    def dfs(node: str) -> bool:
        if node in visiting:
            return True
        if node in visited:
            return False
        visiting.add(node)
        for nb in deps.get(node, []):
            if dfs(nb):
                return True
        visiting.remove(node)
        visited.add(node)
        return False

    return any(dfs(n) for n in deps)


def _check_mandatory_rules(
    task: Task, plan: DispatchPlan, policy: DispatchPolicy
) -> ValidationResult | None:
    """检查 mandatory_role_rules。

    返回 None 表示通过;返回 ValidationResult 表示有问题。
    v2.4:有问题一律 RETRY_PM(不补漏),只有 retry 后仍失败才 FATAL。
    """
    task_text = (task.title + " " + task.owner_request).lower()

    for rule in policy.mandatory_role_rules:
        # 检查是否触发
        triggered = False
        keywords = [k.lower() for k in rule.if_any.get("task_contains", [])]
        if any(kw in task_text for kw in keywords):
            triggered = True
        # paths_match 在 Phase 2+ 才有意义(那时有 worktree)
        # Phase 0B 简化:不检查 paths_match
        if not triggered:
            continue

        # 例外清单
        for ex in policy.exceptions:
            if ex.get("rule_id") == rule.id:
                skip_kws = [
                    k.lower() for k in ex.get("skip_if_any", {}).get("task_contains", [])
                ]
                if any(kw in task_text for kw in skip_kws):
                    triggered = False
                    break
        if not triggered:
            continue

        # 检查每个子任务是否含 required_roles
        for st in plan.business_breakdown:
            present_roles = {s.role_id for s in st.role_sequence}
            missing = [r for r in rule.require_roles if r not in present_roles]
            if missing:
                return ValidationResult(
                    action="RETRY_PM",
                    violation_type="missing_mandatory_role",
                    violation_detail=(
                        f"subtask {st.subtask_id} 触发了 mandatory rule {rule.id!r}"
                        f"(关键词命中),必须含角色 {rule.require_roles},"
                        f"但实际缺少:{missing}"
                    ),
                    expected_action=(
                        f"在 subtask {st.subtask_id} 的 role_sequence 里加入 {missing},"
                        f"并在 role_dispatch_notes 说明 policy_rule_id={rule.id}"
                    ),
                )
    return None


def validate_dispatch_plan(
    raw_plan_dict: dict[str, Any],
    task: Task,
    project: ProjectConfig,
    policy: DispatchPolicy,
) -> ValidationResult:
    """主入口。raw_plan_dict 是 PM 输出的 artifact.content(已经过 schema 校验)。

    返回:
        PASS  + normalized_plan(可进 DISPATCH)
        RETRY_PM + violation_detail(让 PM 重做,上限 1 次)
        FATAL + violation_detail(escalate)
    """
    # 1. 结构层(pydantic 解析失败 = fatal,因为格式错到 PM 大概率不能修)
    try:
        plan = DispatchPlan(**raw_plan_dict)
    except Exception as e:
        return ValidationResult(
            action="RETRY_PM",
            violation_type="schema_violation",
            violation_detail=f"PM 输出不能解析为 DispatchPlan: {e}",
            expected_action="重新输出符合 pm_dispatch_plan schema 的 YAML",
        )

    # 2. subtask_id 重复
    ids = [st.subtask_id for st in plan.business_breakdown]
    if len(ids) != len(set(ids)):
        return ValidationResult(
            action="RETRY_PM",
            violation_type="duplicate_subtask_id",
            violation_detail=f"subtask_id 重复:{ids}",
            expected_action="每个 subtask_id 必须唯一",
        )

    known_roles = [r.role_id for r in project.roles]
    known_task_types = list(project.role_groups.keys())

    # 3. 每个子任务的 role_sequence + dependencies
    for st in plan.business_breakdown:
        # task_type
        if st.task_type not in known_task_types:
            typo = _is_typo(st.task_type, known_task_types)
            if typo:
                return ValidationResult(
                    action="RETRY_PM",
                    violation_type="task_type_typo",
                    violation_detail=f"subtask {st.subtask_id}: task_type={st.task_type!r} 不在 role_groups 里,你是不是想说 {typo!r}?",
                    expected_action=f"task_type 必须从 {known_task_types} 里选",
                )
            return ValidationResult(
                action="RETRY_PM",
                violation_type="task_type_unknown",
                violation_detail=f"subtask {st.subtask_id}: task_type={st.task_type!r} 不在 role_groups 里",
                expected_action=f"task_type 必须从 {known_task_types} 里选",
            )

        # role_sequence step 连续递增
        steps = sorted(s.step for s in st.role_sequence)
        if steps != list(range(1, len(steps) + 1)):
            return ValidationResult(
                action="RETRY_PM",
                violation_type="role_sequence_step_malformed",
                violation_detail=f"subtask {st.subtask_id}: step 必须从 1 起连续递增,实际 {steps}",
                expected_action="把 step 改成 1, 2, 3...",
            )

        # role_sequence 内 role_id 不重复
        role_ids_in_seq = [s.role_id for s in st.role_sequence]
        if len(role_ids_in_seq) != len(set(role_ids_in_seq)):
            return ValidationResult(
                action="RETRY_PM",
                violation_type="role_sequence_duplicate_role",
                violation_detail=f"subtask {st.subtask_id}: role_sequence 含重复 role_id {role_ids_in_seq}",
                expected_action="同一 subtask 内每个 role_id 只能出现一次。重试逻辑走 needs_changes / attempt 字段,不要在 role_sequence 里重复",
            )

        # role_id 必须存在
        for s in st.role_sequence:
            if s.role_id not in known_roles:
                typo = _is_typo(s.role_id, known_roles)
                if typo:
                    return ValidationResult(
                        action="RETRY_PM",
                        violation_type="role_id_typo",
                        violation_detail=(
                            f"subtask {st.subtask_id} role={s.role_id!r} 不在 project.yaml,"
                            f"你是不是想说 {typo!r}?"
                        ),
                        expected_action=f"role_id 必须从 {known_roles} 里选",
                    )
                return ValidationResult(
                    action="FATAL",
                    violation_type="unknown_role_id",
                    violation_detail=(
                        f"subtask {st.subtask_id} role={s.role_id!r} 不在 project.yaml roles 里。"
                        f"这是配置问题,Owner 需要加这个角色到 project.yaml 或修改任务描述。"
                    ),
                    expected_action=f"加 {s.role_id} 到 project.yaml,或让 PM 不要用这个角色",
                )

        # dependencies 引用必须存在
        for dep in st.dependencies:
            if dep not in ids:
                return ValidationResult(
                    action="RETRY_PM",
                    violation_type="dependency_not_found",
                    violation_detail=f"subtask {st.subtask_id} 依赖 {dep!r},但找不到这个 subtask",
                    expected_action=f"dependencies 必须引用 business_breakdown 里存在的 subtask_id",
                )

    # 4. 环检测
    if _has_cycle(plan):
        return ValidationResult(
            action="FATAL",
            violation_type="dependency_cycle",
            violation_detail="business_breakdown 的 dependencies 含环",
            expected_action="Owner 需要看 PM 的拆解,改任务描述或人工拆解",
        )

    # 5. mandatory rules
    res = _check_mandatory_rules(task, plan, policy)
    if res is not None:
        return res

    # 通过
    return ValidationResult(action="PASS", normalized_plan=plan)
