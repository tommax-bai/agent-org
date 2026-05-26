"""预算追踪。任务级硬上限,超过强制 ESCALATED_TO_OWNER。

public API(Phase 0B 待填):
    track_cost(task_id, usd) -> RunningTotal
    check_budget(task_id) -> bool  # False 表示超限
"""
