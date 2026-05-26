"""跨模块共享类型 / 基础设施。最底层,所有模块都能 import。"""

from orchestrator._shared.types import (
    # tasks / project
    Task,
    ProjectConfig,
    RoleConfig,
    RoleGroup,
    DispatchPolicy,
    MandatoryRoleRule,
    PMDeviationPolicy,
    RetryLimits,
    # dispatch plan (v2.4 role_sequence)
    RoleStep,
    Subtask,
    RoleDispatchNote,
    DispatchPlan,
    # artifacts / signals
    Artifact,
    Signal,
    # role invocation
    ContextPack,
    RoleInvocationInput,
    RoleInvocationOutput,
    CostUsed,
    # validator
    ValidationResult,
    # events
    Event,
    EventType,
    # task state
    TaskState,
    TaskStatus,
    CompletedRole,
)

__all__ = [
    "Task",
    "ProjectConfig",
    "RoleConfig",
    "RoleGroup",
    "DispatchPolicy",
    "MandatoryRoleRule",
    "PMDeviationPolicy",
    "RetryLimits",
    "RoleStep",
    "Subtask",
    "RoleDispatchNote",
    "DispatchPlan",
    "Artifact",
    "Signal",
    "ContextPack",
    "RoleInvocationInput",
    "RoleInvocationOutput",
    "CostUsed",
    "ValidationResult",
    "Event",
    "EventType",
    "TaskState",
    "TaskStatus",
    "CompletedRole",
]
