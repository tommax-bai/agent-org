"""事件日志(append-only)。

后端通过 STORAGE_BACKEND 环境变量切换:
- file       :runs/<task_id>/events.jsonl(0B,默认)
- postgres   :Postgres task_events 表(0C+)

public API 保持不变。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator._shared import Event, EventType, storage_backend
from orchestrator.event_log._internal.jsonl_writer import (
    events_file,
    runs_dir,
)


def write_event(
    task_id: str,
    event_type: EventType,
    actor: str,
    payload: dict[str, Any] | None = None,
    base: Path | None = None,
) -> Event:
    if storage_backend() == "postgres":
        from orchestrator.event_log._internal.postgres_writer import (
            write_event as pg_write,
        )

        return pg_write(task_id, event_type, actor, payload)
    from orchestrator.event_log._internal.jsonl_writer import write_event as file_write

    return file_write(task_id, event_type, actor, payload, base)


def read_events(task_id: str, base: Path | None = None) -> list[Event]:
    if storage_backend() == "postgres":
        from orchestrator.event_log._internal.postgres_writer import (
            read_events as pg_read,
        )

        return pg_read(task_id)
    from orchestrator.event_log._internal.jsonl_writer import read_events as file_read

    return file_read(task_id, base)


__all__ = ["write_event", "read_events", "events_file", "runs_dir"]
