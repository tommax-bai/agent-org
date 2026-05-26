"""agent-org 主进程包。

modular monolith 架构。模块间只通过 top-level namespace 通信:
    from orchestrator.event_log import write_event   # 允许
    from orchestrator.event_log._internal.X import Y # 禁止(import-linter 拦截)

模块清单见 docs/module_boundaries.md。
"""
