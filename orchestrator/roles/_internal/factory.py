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


def _is_executor_role(role_config: RoleConfig) -> bool:
    """Phase 2:判断是否是"改文件"类角色(developer / 类似)。

    判定:capabilities 含 modify_code / propose_code_changes,或 artifact_type=code。
    """
    caps = set(role_config.capabilities)
    if {"modify_code", "propose_code_changes", "edit_files"} & caps:
        return True
    if role_config.artifact_type == "code":
        return True
    return False


def make_runner(
    role_config: RoleConfig,
    attempt: int = 1,
    mock_behavior: dict[str, Any] | None = None,
    force_real_llm: bool = False,
    worktree=None,
    protected_paths: dict[str, list[str]] | None = None,
    ci_commands: dict[str, str] | None = None,
) -> RoleRunner:
    """Phase 2:默认所有角色调真实 LLM。Developer 类自动用 FileExecutorRunner。

    通过 ROLE_RUNNER_MODE 环境变量:
        real         (默认):全真 LLM,执行类角色用 FileExecutorRunner
        pm_only_real (0B):只 PM 真,其他 mock
        all_mock     (test):全 mock
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
    # Phase 2:执行类角色用 FileExecutorRunner(需要 worktree)
    if _is_executor_role(role_config) and worktree is not None:
        from orchestrator.roles._internal.executor_runner import FileExecutorRunner

        return FileExecutorRunner(
            role_config=role_config,
            attempt=attempt,
            worktree=worktree,
            protected_paths=protected_paths or {},
            ci_commands=ci_commands or {},
        )
    return PMRunner(role_config=role_config, attempt=attempt)
