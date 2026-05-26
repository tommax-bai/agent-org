"""升级通知:生成 escalation.md / final_report.md。Phase 4+ 加飞书 webhook。"""

from orchestrator.escalation._internal.reports import write_escalation, write_final_report

__all__ = ["write_escalation", "write_final_report"]
