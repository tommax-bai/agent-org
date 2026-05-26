"""产物存储。

后端通过 STORAGE_BACKEND 切换:
- file        : runs/<task_id>/artifacts/*.json(0B 默认)
- postgres    : Postgres artifacts 表(0C+)

artifact 不可变,attempt 排序找当前(v2.4)。
"""

from __future__ import annotations

from pathlib import Path

from orchestrator._shared import Artifact, storage_backend
from orchestrator.artifact._internal.file_store import make_artifact_id


def write_artifact(artifact: Artifact, base: Path | None = None) -> None:
    if storage_backend() == "postgres":
        from orchestrator.artifact._internal.postgres_store import (
            write_artifact as pg_write,
        )

        pg_write(artifact)
        return
    from orchestrator.artifact._internal.file_store import write_artifact as file_write

    file_write(artifact, base)


def get_artifact(task_id: str, artifact_id: str, base: Path | None = None) -> Artifact:
    if storage_backend() == "postgres":
        from orchestrator.artifact._internal.postgres_store import (
            get_artifact as pg_get,
        )

        return pg_get(task_id, artifact_id)
    from orchestrator.artifact._internal.file_store import get_artifact as file_get

    return file_get(task_id, artifact_id, base)


def list_artifacts(task_id: str, base: Path | None = None) -> list[Artifact]:
    if storage_backend() == "postgres":
        from orchestrator.artifact._internal.postgres_store import (
            list_artifacts as pg_list,
        )

        return pg_list(task_id)
    from orchestrator.artifact._internal.file_store import list_artifacts as file_list

    return file_list(task_id, base)


def get_current_artifact(
    task_id: str,
    subtask_id: str | None,
    role_id: str,
    base: Path | None = None,
) -> Artifact | None:
    if storage_backend() == "postgres":
        from orchestrator.artifact._internal.postgres_store import (
            get_current_artifact as pg_cur,
        )

        return pg_cur(task_id, subtask_id, role_id)
    from orchestrator.artifact._internal.file_store import (
        get_current_artifact as file_cur,
    )

    return file_cur(task_id, subtask_id, role_id, base)


def mark_superseded(
    task_id: str, old_artifact_id: str, new_artifact_id: str, base: Path | None = None
) -> None:
    if storage_backend() == "postgres":
        from orchestrator.artifact._internal.postgres_store import (
            mark_superseded as pg_mark,
        )

        pg_mark(task_id, old_artifact_id, new_artifact_id)
        return
    from orchestrator.artifact._internal.file_store import (
        mark_superseded as file_mark,
    )

    file_mark(task_id, old_artifact_id, new_artifact_id, base)


__all__ = [
    "write_artifact",
    "get_artifact",
    "list_artifacts",
    "get_current_artifact",
    "make_artifact_id",
    "mark_superseded",
]
