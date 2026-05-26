"""事件日志(append-only)。0B 写 jsonl 文件,0C+ 写 Postgres task_events 表。

事件类型枚举见 schemas/event.schema.json。

public API(Phase 0B 待填):
    write_event(task_id, event_type, actor, payload) -> None
    read_events(task_id) -> list[Event]
"""
