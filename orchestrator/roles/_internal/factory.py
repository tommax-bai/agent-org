"""根据 role 配置选 runner(Phase 1:默认全真 LLM,可降级 mock)。

环境变量:
    ROLE_RUNNER_MODE=real (默认,Phase 1+)  - 所有角色调真实 LLM
    ROLE_RUNNER_MODE=pm_only_real (0B 模式)  - 只 is_orchestrator 真 LLM,其他 mock
    ROLE_RUNNER_MODE=all_mock                - 全 mock(测状态机用)
"""

from __future__ import annotations

import os
from typing import Any

from orchestrator._shared import RoleConfig
from orchestrator.roles._internal.mock_runners import MockRunner
from orchestrator.roles._internal.pm_runner import PMRunner
from orchestrator.roles._internal.protocol import RoleRunner


def _mode() -> str:
    return os.environ.get("ROLE_RUNNER_MODE", "real").lower()


def make_runner(
    role_config: RoleConfig,
    attempt: int = 1,
    mock_behavior: dict[str, Any] | None = None,
    force_real_llm: bool = False,
) -> RoleRunner:
    """Phase 1 默认:所有角色调真实 LLM。

    通过 ROLE_RUNNER_MODE 环境变量降级到 0B 模式(只 PM 真)或 all_mock(测试用)。
    force_real_llm 参数保留向后兼容(优先级最高,override env)。
    """
    if force_real_llm:
        return PMRunner(role_config=role_config, attempt=attempt)

    mode = _mode()
    if mode == "all_mock":
        return MockRunner(role_config=role_config, attempt=attempt, mock_behavior=mock_behavior)
    if mode == "pm_only_real":
        if role_config.is_orchestrator:
            return PMRunner(role_config=role_config, attempt=attempt)
        return MockRunner(role_config=role_config, attempt=attempt, mock_behavior=mock_behavior)
    # default: real
    return PMRunner(role_config=role_config, attempt=attempt)
