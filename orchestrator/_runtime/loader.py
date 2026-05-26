"""加载 task.yaml / project.yaml / dispatch_policy.yaml / role.yaml + system_prompt.md。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from orchestrator._shared import (
    DispatchPolicy,
    ProjectConfig,
    RoleConfig,
    Task,
    TaskState,
)


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def load_task(task_yaml_path: Path) -> Task:
    raw = _load_yaml(task_yaml_path)
    return Task(**raw)


def load_project(project_dir: Path) -> ProjectConfig:
    proj_path = project_dir / "project.yaml"
    raw = _load_yaml(proj_path)
    project = ProjectConfig(**raw)

    # 用 projects/<project>/roles/ 里的 system_prompt.md 填充 role
    for role in project.roles:
        role_dir = project_dir / "roles" / role.role_id
        if not role_dir.exists():
            continue
        # role.yaml 内的字段补到 role(覆盖 project.yaml 的轻量配置)
        role_yaml = role_dir / "role.yaml"
        if role_yaml.exists():
            extra = _load_yaml(role_yaml)
            # 注意:project.yaml 的 is_orchestrator 优先级高于 role.yaml
            for k, v in extra.items():
                if k == "is_orchestrator":
                    continue  # project.yaml 是真相源
                if k in RoleConfig.model_fields:
                    setattr(role, k, v)
        prompt_path = role_dir / "system_prompt.md"
        if prompt_path.exists():
            role.system_prompt = prompt_path.read_text(encoding="utf-8")
    return project


def load_dispatch_policy(project_dir: Path) -> DispatchPolicy:
    path = project_dir / "dispatch_policy.yaml"
    if not path.exists():
        return DispatchPolicy()
    raw = _load_yaml(path)
    return DispatchPolicy(**raw)


def build_task_state(
    task_yaml_path: Path,
    projects_root: Path,
) -> TaskState:
    """加载所有 yaml 拼成 TaskState。"""
    task = load_task(task_yaml_path)
    project_dir = projects_root / task.project_id
    if not project_dir.exists():
        raise FileNotFoundError(f"project 目录不存在:{project_dir}")
    project = load_project(project_dir)
    policy = load_dispatch_policy(project_dir)

    # 校验 framework 唯一硬约束(v2.4)
    project.orchestrator_role_id()  # 抛 ValueError if not exactly one

    return TaskState(
        task=task,
        project=project,
        policy=policy,
        budget_usd=task.budget_usd,
    )
