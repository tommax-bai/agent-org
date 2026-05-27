"""protected_paths 三级强制(宪法第 7 条:硬护栏在基础设施层强制)。

Owner 在 project.yaml 配 protected_paths:
    hard_block:        ← 完全禁止 LLM 改(.env / secrets / .github/workflows/deploy.yml)
    approval_required: ← 允许改,但需要 Owner 在 PR 上特殊审批(标记进 PR body)
    warn_only:         ← 允许改,只记警告事件

Phase 2 实现:
- hard_block:写文件时 raise ProtectedPathError → Developer artifact 失败
- approval_required:允许写 + 把路径记到 state.extra['approval_required_paths']
- warn_only:允许写 + 写 PROTECTED_PATH_WARNING 事件

Phase 3+ PR 生成时,approval_required_paths 列在 PR body 标红。
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from fnmatch import fnmatch
from pathlib import Path
from typing import Literal


class PathProtection(Enum):
    ALLOW = "allow"
    WARN = "warn_only"
    APPROVAL = "approval_required"
    BLOCK = "hard_block"


class ProtectedPathError(RuntimeError):
    """hard_block 路径被写时抛出。"""

    def __init__(self, path: str, pattern: str) -> None:
        super().__init__(
            f"路径 {path!r} 命中 hard_block 模式 {pattern!r},Developer 不允许改"
        )
        self.path = path
        self.pattern = pattern


@dataclass
class PathCheckResult:
    level: PathProtection
    matched_pattern: str | None = None


def check_path(
    path: str | Path,
    protected_paths: dict[str, list[str]],
) -> PathCheckResult:
    """检查 path 在 project.yaml.protected_paths 里命中哪一级。

    返回 BLOCK / APPROVAL / WARN / ALLOW。

    匹配规则:
    - 用 fnmatch(glob 风格,支持 * / ? / [...])
    - 优先级:hard_block > approval_required > warn_only > allow
    """
    rel = str(path)
    # 标准化:去掉前导 ./
    if rel.startswith("./"):
        rel = rel[2:]

    for level_name, level_enum in [
        ("hard_block", PathProtection.BLOCK),
        ("approval_required", PathProtection.APPROVAL),
        ("warn_only", PathProtection.WARN),
    ]:
        patterns = protected_paths.get(level_name, [])
        for pat in patterns:
            if _match(rel, pat):
                return PathCheckResult(level=level_enum, matched_pattern=pat)
    return PathCheckResult(level=PathProtection.ALLOW)


def _match(path: str, pattern: str) -> bool:
    """fnmatch + 路径分隔符敏感的匹配。

    支持:
        .env             → 精确匹配 .env 或 dir/.env
        .env.*           → .env.production / .env.local 等
        secrets/         → secrets/ 下任何
        secrets/**       → secrets/ 下任何(递归)
        migrations/      → migrations/ 下任何
        .github/workflows/deploy.yml → 精确
    """
    # `.env.*` 视为 glob,在路径任一段都匹配
    if "/" not in pattern:
        # 文件名模式,匹配路径中任一 segment
        segments = path.split("/")
        return any(fnmatch(seg, pattern) for seg in segments)
    # 目录前缀模式(secrets/ → secrets/anything)
    if pattern.endswith("/"):
        return path.startswith(pattern) or path == pattern.rstrip("/")
    # 完整路径 glob(支持 **)
    if "**" in pattern:
        # 转 ** 为 fnmatch 兼容:把 ** 当成 *
        pattern_compat = pattern.replace("**", "*")
        return fnmatch(path, pattern_compat)
    return fnmatch(path, pattern)


def assert_writable(
    path: str | Path,
    protected_paths: dict[str, list[str]],
) -> PathCheckResult:
    """便利方法:check + 如果 BLOCK 就抛异常。

    返回 check result(APPROVAL / WARN / ALLOW),caller 自己决定后续动作
    (比如 APPROVAL 时把路径记进 state)。
    """
    result = check_path(path, protected_paths)
    if result.level == PathProtection.BLOCK:
        raise ProtectedPathError(str(path), result.matched_pattern or "?")
    return result
