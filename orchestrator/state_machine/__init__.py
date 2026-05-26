"""状态机模块:CREATED / PM_PLANNING / DISPATCH / ROLE_EXECUTING / DONE / ESCALATED_TO_OWNER。

通过 STATE_MACHINE 环境变量切换:
- self_written(默认,0B 自写)
- langgraph(0C PoC)

public API 保持不变(run_task)。
"""

from __future__ import annotations

import os

from orchestrator._shared import TaskState


def run_task(state: TaskState) -> TaskState:
    """跑完整状态机直到 terminal state。"""
    engine = os.environ.get("STATE_MACHINE", "self_written").lower()
    if engine == "langgraph":
        from orchestrator.state_machine._internal.langgraph_graph import (
            run_task_langgraph,
        )

        return run_task_langgraph(state)
    from orchestrator.state_machine._internal.graph import run_task as run_self_written

    return run_self_written(state)


__all__ = ["run_task"]
