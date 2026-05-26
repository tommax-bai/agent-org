"""跨模块共享的数据类型(Pydantic models)。

Phase 0A 只放最基础的类型占位,Phase 0B 写 runtime 时再充实字段。

设计原则:
- 这里的类型是"系统词汇表"在代码层的体现(对应 schemas/vocabulary.md)
- 所有跨模块传递的数据用这些类型
- 不放任何业务逻辑,只是数据结构 + Pydantic 校验
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


# ---------- role_sequence(v2.4 替代 required_roles) ----------


class RoleStep(BaseModel):
    """role_sequence 的一项。顺序由 step 字段决定,list 位置无语义。"""

    step: int = Field(ge=1, description="从 1 起连续递增,validator 强制")
    role_id: str = Field(description="必须存在于 project.yaml roles")


# ---------- 业务拆解 ----------


class Subtask(BaseModel):
    """PM 业务拆解的一项。"""

    subtask_id: str
    description: str
    task_type: str = Field(description="必须存在于 role_groups")
    success_criteria: list[str] = Field(default_factory=list)
    role_sequence: list[RoleStep] = Field(min_length=1, description="按 step 排序执行")
    dependencies: list[str] = Field(default_factory=list, description="subtask_id 列表,不能成环")


# ---------- 任务 ----------


class Task(BaseModel):
    """tasks/inbox/<task>.yaml 的内存表示。"""

    task_id: str
    title: str
    project_id: str
    owner_request: str
    priority: Literal["low", "normal", "high", "urgent"] = "normal"
    constraints: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)
    budget_usd: float = Field(default=20.0, ge=0)


# ---------- task state(checkpoint/恢复用) ----------


class TaskState(BaseModel):
    """运行时任务状态。LangGraph checkpoint 序列化 / 反序列化的对象。

    Phase 0B 字段会大幅扩展,这里只放最关键的占位。
    """

    task_id: str
    status: Literal[
        "CREATED",
        "PM_PLANNING",
        "DISPATCH",
        "ROLE_EXECUTING",
        "DONE",
        "ESCALATED_TO_OWNER",
        "BUDGET_EXCEEDED",
    ] = "CREATED"
    business_breakdown: list[Subtask] = Field(default_factory=list)
    pm_retry_count: int = Field(default=0, description="dispatch_plan validator retry 计数(上限 1)")
    cost_used_usd: float = 0.0
    budget_usd: float = 20.0
    extra: dict[str, Any] = Field(default_factory=dict, description="Phase 0B 扩展用")
