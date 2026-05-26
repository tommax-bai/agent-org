"""调度者处理 signals 的规则(主文档 D 域 + Spec B.8)。

主要逻辑:
- low: 记 event,不影响流程
- medium: 记 event,加入 pending_concerns(下次相关 role 拿到 context)
- high: 累计计数,3 次后强制 escalate
- immediate_escalate_required=true(必须有 reason): 立即 escalate
- immediate_escalate_required=true 但无 reason: 降级为 high 处理 + 记拒绝事件
"""

from __future__ import annotations

from dataclasses import dataclass

from orchestrator._shared import Signal, TaskState
from orchestrator.event_log import write_event


@dataclass
class SignalAction:
    """处理 signal 后,告诉 caller 是否需要立即 escalate。"""

    escalate_now: bool = False
    escalate_reason: str = ""


def process_signal(state: TaskState, signal: Signal, actor: str) -> SignalAction:
    task_id = state.task.task_id
    payload = signal.model_dump()

    # immediate_escalate 优先级最高
    if signal.immediate_escalate_required:
        if not signal.immediate_escalate_reason.strip():
            write_event(
                task_id, "IMMEDIATE_ESCALATE_REJECTED", actor, {"reason": "missing_reason", **payload}
            )
            # 降级为 high 处理(继续走下面 severity 逻辑)
            signal = signal.model_copy(update={"immediate_escalate_required": False, "severity": "high"})
        else:
            write_event(task_id, "IMMEDIATE_ESCALATE_TRIGGERED", actor, payload)
            return SignalAction(
                escalate_now=True,
                escalate_reason=f"immediate_escalate from {actor}: {signal.immediate_escalate_reason}",
            )

    # 按 severity 处理
    write_event(task_id, "SIGNAL_RECEIVED", actor, payload)
    if signal.severity == "low":
        return SignalAction()
    if signal.severity == "medium":
        state.pending_concerns.append(signal)
        return SignalAction()
    # high
    state.high_signal_count += 1
    state.pending_concerns.append(signal)
    if state.high_signal_count >= 3:
        return SignalAction(
            escalate_now=True,
            escalate_reason=f"high_signals_overflow: 累计 {state.high_signal_count} 个 high severity signal",
        )
    return SignalAction()


def process_signals(state: TaskState, signals: list[Signal], actor: str) -> SignalAction:
    """处理一批 signal。任一触发 escalate 立即返回。"""
    for s in signals:
        action = process_signal(state, s, actor)
        if action.escalate_now:
            return action
    return SignalAction()
