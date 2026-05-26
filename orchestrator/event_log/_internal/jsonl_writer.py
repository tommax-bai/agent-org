"""事件日志的 jsonl 文件实现(Phase 0B)。

每次 append 后 flush + fsync,崩溃最多丢最后一行。
Phase 0C 接 Postgres task_events 表,本模块的 public API 保持不变。
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any

from orchestrator._shared import Event, EventType


def runs_dir(task_id: str, base: Path | None = None) -> Path:
    base = base or Path.cwd() / "runs"
    p = base / task_id
    p.mkdir(parents=True, exist_ok=True)
    return p


def events_file(task_id: str, base: Path | None = None) -> Path:
    return runs_dir(task_id, base) / "events.jsonl"


def write_event(
    task_id: str,
    event_type: EventType,
    actor: str,
    payload: dict[str, Any] | None = None,
    base: Path | None = None,
) -> Event:
    ev = Event(
        time=datetime.utcnow(),
        task_id=task_id,
        type=event_type,
        actor=actor,
        payload=payload or {},
    )
    path = events_file(task_id, base)
    line = json.dumps(
        {
            "time": ev.time.isoformat() + "Z",
            "task_id": ev.task_id,
            "type": ev.type,
            "actor": ev.actor,
            "payload": ev.payload,
        },
        ensure_ascii=False,
    )
    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()
        os.fsync(f.fileno())
    return ev


def read_events(task_id: str, base: Path | None = None) -> list[Event]:
    path = events_file(task_id, base)
    if not path.exists():
        return []
    out: list[Event] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        raw = json.loads(line)
        # 解析回 datetime
        if isinstance(raw.get("time"), str):
            raw["time"] = datetime.fromisoformat(raw["time"].rstrip("Z"))
        out.append(Event(**raw))
    return out
