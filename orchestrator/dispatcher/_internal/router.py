"""找下一个 ready 角色(按 role_sequence.step 排序,看 dependencies)。"""

from __future__ import annotations

from orchestrator._shared import RoleStep, Subtask, TaskState


def _dependencies_met(state: TaskState, subtask: Subtask) -> bool:
    done_subtask_ids = {
        c.subtask_id
        for c in state.completed_roles
        # 该 subtask 的所有 role_sequence 都跑过且最新 attempt 是 success
    }
    # 严格判断:每个 dep 必须所有 role 都 success
    for dep_id in subtask.dependencies:
        if dep_id not in {st.subtask_id for st in (state.dispatch_plan.business_breakdown if state.dispatch_plan else [])}:
            return False
        if not _subtask_done(state, dep_id):
            return False
    return True


def _subtask_done(state: TaskState, subtask_id: str) -> bool:
    if not state.dispatch_plan:
        return False
    for st in state.dispatch_plan.business_breakdown:
        if st.subtask_id == subtask_id:
            for s in st.role_sequence:
                done = state.role_current_attempt_done(subtask_id, s.role_id)
                if done is None or done.verdict != "success":
                    return False
            return True
    return False


def find_next_ready_role(state: TaskState) -> tuple[str, str] | None:
    """返回 (subtask_id, role_id) 或 None(全部完成 / 没有 ready 的)。

    规则:
    1. 按 business_breakdown 顺序遍历 subtask
    2. 跳过已 done 的 subtask
    3. 跳过依赖未满足的 subtask
    4. 在 ready subtask 内,按 role_sequence.step 升序找下一个未跑 success 的 role
    """
    if not state.dispatch_plan:
        return None
    for st in state.dispatch_plan.business_breakdown:
        if _subtask_done(state, st.subtask_id):
            continue
        if not _dependencies_met(state, st):
            continue
        # 按 step 排序
        ordered = sorted(st.role_sequence, key=lambda x: x.step)
        for s in ordered:
            done = state.role_current_attempt_done(st.subtask_id, s.role_id)
            if done is None or done.verdict != "success":
                return (st.subtask_id, s.role_id)
    return None


def find_upstream_role(state: TaskState, subtask_id: str, role_id: str) -> str | None:
    """needs_changes 路径用:找当前 role 的上一个 step 的 role_id。

    没有上游(自己是 step=1)返回 None。
    """
    if not state.dispatch_plan:
        return None
    for st in state.dispatch_plan.business_breakdown:
        if st.subtask_id != subtask_id:
            continue
        ordered = sorted(st.role_sequence, key=lambda x: x.step)
        for i, s in enumerate(ordered):
            if s.role_id == role_id:
                if i == 0:
                    return None
                return ordered[i - 1].role_id
    return None
