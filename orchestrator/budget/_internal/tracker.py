"""预算追踪(Phase 0B 简化版)。

任务级硬上限,超过强制 ESCALATED_TO_OWNER。
不做项目级 / 月度级预算(那是 Phase 4+)。
"""

from __future__ import annotations

from orchestrator._shared import TaskState


def add_cost(state: TaskState, usd: float) -> float:
    state.cost_used_usd += max(0.0, usd)
    return state.cost_used_usd


def is_over_budget(state: TaskState) -> bool:
    return state.cost_used_usd >= state.budget_usd


def remaining_budget(state: TaskState) -> float:
    return max(0.0, state.budget_usd - state.cost_used_usd)
