"""生成 escalation.md(失败时)和 final_report.md(成功时)。

Phase 4+ 加飞书 webhook 推送。
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from orchestrator._shared import TaskState
from orchestrator.artifact import list_artifacts
from orchestrator.event_log import read_events, runs_dir


def _summarize_events(task_id: str, base: Path | None = None) -> str:
    events = read_events(task_id, base)
    if not events:
        return "(无事件)"
    lines = []
    for e in events:
        t = e.time.isoformat() + "Z" if isinstance(e.time, datetime) else str(e.time)
        payload_brief = ""
        if e.payload:
            keys = list(e.payload.keys())[:3]
            payload_brief = " " + ", ".join(f"{k}={e.payload[k]}" for k in keys)
        lines.append(f"- {t} `{e.type}` actor={e.actor}{payload_brief}")
    return "\n".join(lines)


def write_escalation(state: TaskState, base: Path | None = None) -> Path:
    """任务失败 / escalate 时生成 escalation.md。"""
    path = runs_dir(state.task.task_id, base) / "escalation.md"
    artifacts = list_artifacts(state.task.task_id, base)

    md = [
        f"# Escalation: {state.task.task_id}",
        "",
        f"**任务标题**:{state.task.title}",
        f"**项目**:{state.task.project_id}",
        f"**失败状态**:{state.status}",
        f"**升级原因**:{state.escalation_reason}",
        "",
    ]
    if state.escalation_detail:
        md += ["## 详细说明", "", state.escalation_detail, ""]

    md += [
        "## 成本",
        "",
        f"- 已花费:${state.cost_used_usd:.4f} / ${state.budget_usd:.2f}",
        f"- 剩余预算:${max(0, state.budget_usd - state.cost_used_usd):.4f}",
        "",
    ]

    if state.dispatch_plan:
        md += [
            "## PM 输出(dispatch_plan)",
            "",
            f"- parsed_intent: {state.dispatch_plan.parsed_intent}",
            f"- confidence: {state.dispatch_plan.confidence:.2f}",
            f"- subtasks: {len(state.dispatch_plan.business_breakdown)}",
            "",
        ]

    if artifacts:
        md += ["## Artifacts(全部 attempt)", ""]
        for a in artifacts:
            md.append(
                f"- `{a.artifact_id}` "
                f"subtask={a.subtask_id} role={a.role_id} attempt={a.attempt} type={a.type}"
                + (f"  superseded_by={a.superseded_by}" if a.superseded_by else "")
            )
        md.append("")

    md += [
        "## 事件流",
        "",
        _summarize_events(state.task.task_id, base),
        "",
        "## 建议 Owner 操作",
        "",
        "1. 看 `runs/<task_id>/events.jsonl` 完整事件",
        "2. 看 `runs/<task_id>/artifacts/` 每个 role 的产出",
        "3. 根据升级原因决定:改 prompt / 改 dispatch_policy / 重新提交任务",
    ]

    path.write_text("\n".join(md), encoding="utf-8")
    return path


def write_final_report(state: TaskState, base: Path | None = None) -> Path:
    """任务成功时生成 final_report.md。"""
    path = runs_dir(state.task.task_id, base) / "final_report.md"
    artifacts = list_artifacts(state.task.task_id, base)

    md = [
        f"# Final Report: {state.task.task_id}",
        "",
        f"**任务标题**:{state.task.title}",
        f"**项目**:{state.task.project_id}",
        f"**完成状态**:{state.status} ✅",
        "",
        "## 成本",
        "",
        f"- 总花费:${state.cost_used_usd:.4f} / ${state.budget_usd:.2f}",
        "",
    ]

    if state.dispatch_plan:
        md += [
            "## 业务拆解",
            "",
            f"- parsed_intent: {state.dispatch_plan.parsed_intent}",
            f"- subtasks: {len(state.dispatch_plan.business_breakdown)}",
            "",
        ]
        for st in state.dispatch_plan.business_breakdown:
            seq = " → ".join(s.role_id for s in sorted(st.role_sequence, key=lambda x: x.step))
            md += [f"  - **{st.subtask_id}** ({st.task_type}): {st.description}"]
            md += [f"    role_sequence: {seq}"]

    md += ["", "## 各角色产出"]
    for a in artifacts:
        if a.superseded_by:
            continue  # 只显示 current attempt
        md += [
            "",
            f"### {a.role_id} (subtask={a.subtask_id}, attempt={a.attempt})",
            "",
            f"- artifact_id: `{a.artifact_id}`",
            f"- type: `{a.type}`",
            "- content(摘要):",
        ]
        # 简单序列化前几个字段
        content_keys = list(a.content.keys())[:5]
        for k in content_keys:
            v = a.content[k]
            v_str = str(v)
            if len(v_str) > 120:
                v_str = v_str[:117] + "..."
            md.append(f"    - {k}: {v_str}")

    md += ["", "## 事件流", "", _summarize_events(state.task.task_id, base)]
    path.write_text("\n".join(md), encoding="utf-8")
    return path
