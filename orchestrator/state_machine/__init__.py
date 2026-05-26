"""状态机模块:CREATED / PM_PLANNING / DISPATCH / ROLE_EXECUTING / DONE / ESCALATED_TO_OWNER。

Phase 0B 自写;Phase 0C PoC 通过后接 LangGraph。public API 保持不变。
"""

from orchestrator.state_machine._internal.graph import run_task

__all__ = ["run_task"]
