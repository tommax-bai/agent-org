"""入口层:命令行 + 主循环。

public API:
    run_task_from_file(task_yaml_path, projects_root) -> TaskState
"""

from orchestrator._runtime.loader import build_task_state, load_task

__all__ = ["build_task_state", "load_task"]
