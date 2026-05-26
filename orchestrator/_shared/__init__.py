"""跨模块共享类型 / 基础设施。最底层,所有模块都能 import。"""

from orchestrator._shared.types import Task, Subtask, RoleStep, TaskState

__all__ = ["Task", "Subtask", "RoleStep", "TaskState"]
