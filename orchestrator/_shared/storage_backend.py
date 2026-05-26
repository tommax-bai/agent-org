"""存储后端配置(通过环境变量切换 file / postgres)。

读取顺序:
  1. .env 文件(项目根目录,通过 python-dotenv 加载)
  2. 进程环境变量(优先级最高)

STORAGE_BACKEND=file       → 0B 行为:写 runs/<task_id>/events.jsonl + artifacts/*.json
STORAGE_BACKEND=postgres   → 0C 行为:写 Postgres task_events / artifacts 表
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Literal

# 静默加载 .env(如果有 python-dotenv)
def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv

        # 找 agent-org 根目录的 .env
        cwd = Path.cwd()
        for d in [cwd, *cwd.parents]:
            envf = d / ".env"
            if envf.exists():
                load_dotenv(envf)
                return
    except ImportError:
        pass


_load_dotenv()


StorageBackend = Literal["file", "postgres"]


def storage_backend() -> StorageBackend:
    val = os.environ.get("STORAGE_BACKEND", "file").lower()
    if val not in ("file", "postgres"):
        raise ValueError(f"STORAGE_BACKEND 必须是 file / postgres,got {val!r}")
    return val  # type: ignore[return-value]


def database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("STORAGE_BACKEND=postgres 需要环境变量 DATABASE_URL")
    return url
