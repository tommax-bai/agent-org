"""artifact 文件版存储(Phase 0B)。

artifact 不可变,attempt N+1 是新 artifact_id(v2.4)。
本模块对 artifact.content 类型无知,只存 dict。
content schema 校验在 roles 模块出口做。

布局:
    runs/<task_id>/artifacts/<artifact_id>.json
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime
from pathlib import Path

from orchestrator._shared import Artifact
from orchestrator.event_log import runs_dir


def _artifacts_dir(task_id: str, base: Path | None = None) -> Path:
    d = runs_dir(task_id, base) / "artifacts"
    d.mkdir(parents=True, exist_ok=True)
    return d


def make_artifact_id() -> str:
    today = datetime.utcnow().strftime("%Y-%m-%d")
    return f"artifact-{today}-{uuid.uuid4().hex[:8]}"


def write_artifact(artifact: Artifact, base: Path | None = None) -> Path:
    path = _artifacts_dir(artifact.task_id, base) / f"{artifact.artifact_id}.json"
    payload = artifact.model_dump(mode="json")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def get_artifact(task_id: str, artifact_id: str, base: Path | None = None) -> Artifact:
    path = _artifacts_dir(task_id, base) / f"{artifact_id}.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    return Artifact(**raw)


def list_artifacts(task_id: str, base: Path | None = None) -> list[Artifact]:
    d = _artifacts_dir(task_id, base)
    out: list[Artifact] = []
    for p in sorted(d.glob("artifact-*.json")):
        raw = json.loads(p.read_text(encoding="utf-8"))
        out.append(Artifact(**raw))
    return out


def get_current_artifact(
    task_id: str,
    subtask_id: str | None,
    role_id: str,
    base: Path | None = None,
) -> Artifact | None:
    """取 (task, subtask, role) 下 attempt 最大的 artifact。"""
    candidates = [
        a
        for a in list_artifacts(task_id, base)
        if a.subtask_id == subtask_id and a.role_id == role_id
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda a: a.attempt)


def mark_superseded(
    task_id: str, old_artifact_id: str, new_artifact_id: str, base: Path | None = None
) -> None:
    """老 artifact 标 superseded_by(追溯链)。"""
    old = get_artifact(task_id, old_artifact_id, base)
    old.superseded_by = new_artifact_id
    write_artifact(old, base)
