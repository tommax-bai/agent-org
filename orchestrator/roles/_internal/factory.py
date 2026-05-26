"""根据 role 配置选 runner(0B:PM 真 LLM,其他 mock)。"""

from __future__ import annotations

from typing import Any

from orchestrator._shared import RoleConfig
from orchestrator.roles._internal.mock_runners import MockRunner
from orchestrator.roles._internal.pm_runner import PMRunner
from orchestrator.roles._internal.protocol import RoleRunner


def make_runner(
    role_config: RoleConfig,
    attempt: int = 1,
    mock_behavior: dict[str, Any] | None = None,
    force_real_llm: bool = False,
) -> RoleRunner:
    """0B 默认:is_orchestrator 用真 LLM,其他用 mock。

    Phase 1 起把 force_real_llm 改成默认 True,所有角色调真实 LLM。
    """
    if role_config.is_orchestrator or force_real_llm:
        return PMRunner(role_config=role_config, attempt=attempt)
    return MockRunner(role_config=role_config, attempt=attempt, mock_behavior=mock_behavior)
