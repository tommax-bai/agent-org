"""事件日志的 Postgres 实现(0C+)。

跟 jsonl_writer 的 public API 等价(write_event / read_events),通过
storage_backend() 选哪个。
"""

from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from orchestrator._shared import Event, EventType, database_url


def _conn() -> psycopg.Connection[Any]:
    # autocommit 简化(write_event 不在事务里)
    return psycopg.connect(database_url(), autocommit=True)


def write_event(
    task_id: str,
    event_type: EventType,
    actor: str,
    payload: dict[str, Any] | None = None,
) -> Event:
    ev = Event(
        time=datetime.utcnow(),
        task_id=task_id,
        type=event_type,
        actor=actor,
        payload=payload or {},
    )
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO task_events (task_id, event_type, actor, payload, occurred_at)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (ev.task_id, ev.type, ev.actor, Jsonb(ev.payload), ev.time),
        )
    return ev


def read_events(task_id: str) -> list[Event]:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            SELECT occurred_at, task_id, event_type, actor, payload
            FROM task_events
            WHERE task_id = %s
            ORDER BY occurred_at, id
            """,
            (task_id,),
        )
        rows = cur.fetchall()
    return [
        Event(time=r[0], task_id=r[1], type=r[2], actor=r[3], payload=r[4] or {})
        for r in rows
    ]
