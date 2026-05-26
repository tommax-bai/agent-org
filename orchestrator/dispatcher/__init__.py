"""DISPATCH 节点。

public API:
    validate_dispatch_plan(raw_plan_dict, task, project, policy) -> ValidationResult
    find_next_ready_role(state) -> (subtask_id, role_id) | None
    find_upstream_role(state, subtask_id, role_id) -> role_id | None
    process_signals(state, signals, actor) -> SignalAction
"""

from orchestrator.dispatcher._internal.router import find_next_ready_role, find_upstream_role
from orchestrator.dispatcher._internal.signal_handler import SignalAction, process_signals
from orchestrator.dispatcher._internal.validator import validate_dispatch_plan

__all__ = [
    "validate_dispatch_plan",
    "find_next_ready_role",
    "find_upstream_role",
    "process_signals",
    "SignalAction",
]
