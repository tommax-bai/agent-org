"""artifact Postgres backend(0C+)。"""

from __future__ import annotations

from datetime import datetime
from typing import Any

import psycopg
from psycopg.types.json import Jsonb

from orchestrator._shared import Artifact, database_url


def _conn() -> psycopg.Connection[Any]:
    return psycopg.connect(database_url(), autocommit=True)


def write_artifact(artifact: Artifact) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO artifacts
              (artifact_id, task_id, subtask_id, role_id, attempt, type,
               content, superseded_by, created_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (artifact_id) DO UPDATE SET
              content = EXCLUDED.content,
              superseded_by = EXCLUDED.superseded_by
            """,
            (
                artifact.artifact_id,
                artifact.task_id,
                artifact.subtask_id,
                artifact.role_id,
                artifact.attempt,
                artifact.type,
                Jsonb(artifact.content),
                artifact.superseded_by,
                artifact.created_at,
            ),
        )


def _row_to_artifact(row: tuple) -> Artifact:
    return Artifact(
        artifact_id=row[0],
        task_id=row[1],
        subtask_id=row[2],
        role_id=row[3],
        attempt=row[4],
        type=row[5],
        content=row[6] or {},
        superseded_by=row[7],
        created_at=row[8],
    )


_SELECT_COLS = (
    "artifact_id, task_id, subtask_id, role_id, attempt, type, "
    "content, superseded_by, created_at"
)


def get_artifact(task_id: str, artifact_id: str) -> Artifact:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT {_SELECT_COLS} FROM artifacts WHERE task_id=%s AND artifact_id=%s",
            (task_id, artifact_id),
        )
        row = cur.fetchone()
    if row is None:
        raise KeyError(f"artifact {artifact_id} not found for task {task_id}")
    return _row_to_artifact(row)


def list_artifacts(task_id: str) -> list[Artifact]:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            f"SELECT {_SELECT_COLS} FROM artifacts WHERE task_id=%s ORDER BY created_at",
            (task_id,),
        )
        rows = cur.fetchall()
    return [_row_to_artifact(r) for r in rows]


def get_current_artifact(
    task_id: str,
    subtask_id: str | None,
    role_id: str,
) -> Artifact | None:
    with _conn() as conn, conn.cursor() as cur:
        if subtask_id is None:
            cur.execute(
                f"""
                SELECT {_SELECT_COLS} FROM artifacts
                WHERE task_id=%s AND subtask_id IS NULL AND role_id=%s
                ORDER BY attempt DESC LIMIT 1
                """,
                (task_id, role_id),
            )
        else:
            cur.execute(
                f"""
                SELECT {_SELECT_COLS} FROM artifacts
                WHERE task_id=%s AND subtask_id=%s AND role_id=%s
                ORDER BY attempt DESC LIMIT 1
                """,
                (task_id, subtask_id, role_id),
            )
        row = cur.fetchone()
    return _row_to_artifact(row) if row else None


def mark_superseded(task_id: str, old_artifact_id: str, new_artifact_id: str) -> None:
    with _conn() as conn, conn.cursor() as cur:
        cur.execute(
            """
            UPDATE artifacts SET superseded_by=%s
            WHERE task_id=%s AND artifact_id=%s
            """,
            (new_artifact_id, task_id, old_artifact_id),
        )
