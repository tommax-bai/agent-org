"""跨模块共享的数据类型(Pydantic models)。

这里的类型是"系统词汇表"在代码层的体现(对应 schemas/vocabulary.md)。
所有跨模块传递的数据用这些类型。
不放业务逻辑,只是数据结构 + Pydantic 校验。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# =====================================================================
# 任务相关
# =====================================================================


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

    # 0B 阶段可选:控制 mock 角色行为(只 dev 用,不进 schema)
    mock_behavior: dict[str, Any] = Field(default_factory=dict, exclude=True)


# =====================================================================
# Project / Role / DispatchPolicy
# =====================================================================


class RoleConfig(BaseModel):
    """project.yaml 里 roles[] 的一项 + role.yaml 内容合并。"""

    role_id: str
    description: str = ""
    is_orchestrator: bool = False
    artifact_type: str = "analysis"
    model_policy: dict[str, Any] = Field(default_factory=dict)
    capabilities: list[str] = Field(default_factory=list)
    inputs: dict[str, Any] = Field(default_factory=dict)
    outputs: dict[str, Any] = Field(default_factory=dict)
    safety: dict[str, Any] = Field(default_factory=dict)
    budget: dict[str, Any] = Field(default_factory=dict)
    system_prompt: str = ""


class RoleGroup(BaseModel):
    description: str = ""
    roles: list[str]


class ProjectConfig(BaseModel):
    project_id: str
    name: str
    repo_url: str = ""
    main_branch: str = "main"
    local_main_path: str = ""
    worktree_root: str = ""
    commands: dict[str, str] = Field(default_factory=dict)
    roles: list[RoleConfig] = Field(default_factory=list)
    role_groups: dict[str, RoleGroup] = Field(default_factory=dict)
    protected_paths: dict[str, list[str]] = Field(default_factory=dict)

    def get_role(self, role_id: str) -> RoleConfig | None:
        for r in self.roles:
            if r.role_id == role_id:
                return r
        return None

    def orchestrator_role_id(self) -> str:
        """返回标 is_orchestrator: true 的角色 id。

        如果不止一个或一个都没有,raise ValueError(framework 唯一硬约束)。
        """
        orchestrators = [r.role_id for r in self.roles if r.is_orchestrator]
        if len(orchestrators) != 1:
            raise ValueError(
                f"project.yaml 必须恰好一个 role 标 is_orchestrator: true,"
                f"实际找到 {len(orchestrators)} 个:{orchestrators}"
            )
        return orchestrators[0]


class MandatoryRoleRule(BaseModel):
    id: str
    if_any: dict[str, list[str]] = Field(default_factory=dict)
    require_roles: list[str]
    require_approval_gate: bool = False


class PMDeviationPolicy(BaseModel):
    can_add_roles: bool = True
    can_remove_template_roles: bool = True
    cannot_remove_mandatory_roles: bool = True
    removing_template_role_requires_signal: bool = True
    adding_non_template_role_requires_dispatch_note: bool = True


class RetryLimits(BaseModel):
    pm_validator_retry_max: int = Field(default=1, ge=0, le=3)
    role_attempt_max: int = Field(default=2, ge=1, le=5)


class DispatchPolicy(BaseModel):
    mandatory_role_rules: list[MandatoryRoleRule] = Field(default_factory=list)
    pm_deviation_policy: PMDeviationPolicy = Field(default_factory=PMDeviationPolicy)
    exceptions: list[dict[str, Any]] = Field(default_factory=list)
    retry_limits: RetryLimits = Field(default_factory=RetryLimits)


# =====================================================================
# v2.4:role_sequence 替代 required_roles
# =====================================================================


class RoleStep(BaseModel):
    """role_sequence 的一项。顺序由 step 字段决定,list 位置无语义。"""

    step: int = Field(ge=1, description="从 1 起连续递增,validator 强制")
    role_id: str


class Subtask(BaseModel):
    """PM 业务拆解的一项。"""

    subtask_id: str
    description: str
    task_type: str
    success_criteria: list[str] = Field(default_factory=list)
    role_sequence: list[RoleStep] = Field(min_length=1)
    dependencies: list[str] = Field(default_factory=list)


class RoleDispatchNote(BaseModel):
    subtask_id: str
    deviation_type: Literal["add_role", "remove_role", "template_default"]
    role_id: str
    reason: str
    policy_rule_id: str = ""


class DispatchPlan(BaseModel):
    """PM 输出的 dispatch_plan(对应 schemas/pm_dispatch_plan.schema.json)。"""

    parsed_intent: str
    assumptions: list[dict[str, Any]] = Field(default_factory=list)
    complexity: dict[str, Any] = Field(default_factory=dict)
    business_breakdown: list[Subtask] = Field(min_length=1)
    role_dispatch_notes: list[RoleDispatchNote] = Field(default_factory=list)
    confidence: float = Field(ge=0, le=1)


# =====================================================================
# Artifact(v2.4 加 attempt + superseded_by)
# =====================================================================


class Artifact(BaseModel):
    """role_invocation_output.artifact。

    content 是 dict,不在这一层校验内容结构——
    校验在 roles 模块出口做(对应 schemas/artifact_content/<type>.schema.json)。
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    artifact_id: str
    type: str
    content: dict[str, Any]
    attempt: int = Field(default=1, ge=1)
    superseded_by: str | None = None
    # 关联到具体 task/subtask/role(artifact store 索引用)
    task_id: str
    subtask_id: str | None = None
    role_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =====================================================================
# Signals
# =====================================================================


class Signal(BaseModel):
    target: str
    type: Literal["question", "concern", "suggestion", "collaboration_request"]
    severity: Literal["low", "medium", "high"] = "medium"
    content: str
    immediate_escalate_required: bool = False
    immediate_escalate_reason: str = ""


# =====================================================================
# Role invocation protocol
# =====================================================================


class ContextPack(BaseModel):
    task_context: dict[str, Any] = Field(default_factory=dict)
    business_goal: str = ""
    success_criteria: list[str] = Field(default_factory=list)
    related_artifacts: list[Artifact] = Field(default_factory=list)
    project_memory: dict[str, Any] = Field(default_factory=dict)
    role_specific_data: dict[str, Any] = Field(default_factory=dict)
    previous_violation: dict[str, Any] | None = None


class RoleInvocationInput(BaseModel):
    task_id: str
    subtask_id: str | None = None
    role_id: str
    context_pack: ContextPack
    prior_role_signals: list[Signal] = Field(default_factory=list)


class CostUsed(BaseModel):
    llm_tokens: int = 0
    duration_ms: int = 0
    usd: float = 0.0


class RoleInvocationOutput(BaseModel):
    role_id: str
    task_id: str
    subtask_id: str | None = None
    verdict: Literal["success", "needs_changes", "escalate"]
    artifact: Artifact
    signals_to_other_roles: list[Signal] = Field(default_factory=list)
    cost_used: CostUsed = Field(default_factory=CostUsed)


# =====================================================================
# Validator 结果(v2.4:两级)
# =====================================================================


class ValidationResult(BaseModel):
    action: Literal["PASS", "RETRY_PM", "FATAL"]
    normalized_plan: DispatchPlan | None = None
    violation_type: str = ""
    violation_detail: str = ""
    expected_action: str = ""


# =====================================================================
# Event(events.jsonl 一条)
# =====================================================================


EventType = Literal[
    "TASK_CREATED",
    "STATE_CHANGED",
    "DISPATCH_DECISION",
    "ROLE_INVOKED",
    "ROLE_RETURNED",
    "SIGNAL_RECEIVED",
    "BUDGET_CONSUMED",
    "ESCALATED",
    "TASK_COMPLETED",
    "TASK_FAILED",
    "PLAN_RETRY_REQUESTED",
    "PLAN_VALIDATION_FATAL",
    "ATTEMPT_LIMIT_REACHED",
    "IMMEDIATE_ESCALATE_TRIGGERED",
    "IMMEDIATE_ESCALATE_REJECTED",
    "ARTIFACT_VALIDATION_FAILED",
]


class Event(BaseModel):
    time: datetime = Field(default_factory=datetime.utcnow)
    task_id: str
    type: EventType
    actor: str
    payload: dict[str, Any] = Field(default_factory=dict)


# =====================================================================
# Task state(运行时,checkpoint/恢复用)
# =====================================================================


TaskStatus = Literal[
    "CREATED",
    "PM_PLANNING",
    "DISPATCH",
    "ROLE_EXECUTING",
    "DONE",
    "ESCALATED_TO_OWNER",
    "BUDGET_EXCEEDED",
]


class CompletedRole(BaseModel):
    """记录 (subtask, role) 已完成的 attempt 信息。"""

    subtask_id: str
    role_id: str
    attempt: int
    verdict: str
    artifact_id: str


class TaskState(BaseModel):
    task: Task
    project: ProjectConfig
    policy: DispatchPolicy

    status: TaskStatus = "CREATED"
    dispatch_plan: DispatchPlan | None = None

    # validator
    pm_retry_count: int = 0

    # 已完成的角色调用(按 (subtask, role) 索引最新 attempt)
    completed_roles: list[CompletedRole] = Field(default_factory=list)
    # (subtask, role) → 已尝试 attempt 数(用来判断 attempt 上限)
    attempt_counts: dict[str, int] = Field(default_factory=dict)

    # signals
    pending_concerns: list[Signal] = Field(default_factory=list)
    high_signal_count: int = 0

    # budget
    cost_used_usd: float = 0.0
    budget_usd: float = 20.0

    # escalation
    escalation_reason: str = ""
    escalation_detail: str = ""

    extra: dict[str, Any] = Field(default_factory=dict)

    @staticmethod
    def attempt_key(subtask_id: str, role_id: str) -> str:
        return f"{subtask_id}::{role_id}"

    def get_attempt(self, subtask_id: str, role_id: str) -> int:
        """这是该 (subtask, role) 即将要跑的第几次 attempt(从 1 起)。"""
        return self.attempt_counts.get(self.attempt_key(subtask_id, role_id), 0) + 1

    def mark_role_completed(self, completed: CompletedRole) -> None:
        # 替换或追加(取最新 attempt 作为 current)
        self.completed_roles = [
            c
            for c in self.completed_roles
            if not (c.subtask_id == completed.subtask_id and c.role_id == completed.role_id)
        ]
        self.completed_roles.append(completed)
        self.attempt_counts[self.attempt_key(completed.subtask_id, completed.role_id)] = (
            completed.attempt
        )

    def role_current_attempt_done(self, subtask_id: str, role_id: str) -> CompletedRole | None:
        for c in self.completed_roles:
            if c.subtask_id == subtask_id and c.role_id == role_id:
                return c
        return None
