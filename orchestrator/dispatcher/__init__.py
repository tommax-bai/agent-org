"""DISPATCH 节点:按 role_sequence.step 排序找下一个 ready 角色。

public API(待填):
    find_next_ready_role(task_state) -> tuple[subtask_id, role_id] | None
    validate_dispatch_plan(raw_plan, project, policy) -> ValidationResult
"""
