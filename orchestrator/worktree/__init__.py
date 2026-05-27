"""Git worktree 管理(Phase 2+)。

宪法第 1 条:任务间并行,worktree 物理隔离。

public API:
    create_worktree(task_id, project) -> Path
    cleanup_worktree(task_id, project)
    worktree_path(task_id, project) -> Path
    git_diff(worktree_path) -> str
    list_changed_files(worktree_path) -> list[str]
    ensure_main_repo(project) -> Path
"""

from orchestrator.worktree._internal.manager import (
    WorktreeError,
    cleanup_worktree,
    create_worktree,
    ensure_main_repo,
    git_diff,
    list_changed_files,
    worktree_path,
)

__all__ = [
    "WorktreeError",
    "create_worktree",
    "cleanup_worktree",
    "ensure_main_repo",
    "git_diff",
    "list_changed_files",
    "worktree_path",
]
