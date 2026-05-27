"""Git worktree 管理。

每个 task 一个独立 worktree(物理隔离,避免任务间相互影响)。

布局:
    project.local_main_path/      # 主仓库(bare clone or full clone)
    project.worktree_root/
        <task_id>/                # 该 task 的 worktree

bootstrap:
    第一次跑某 project 时,如果 local_main_path 不存在 git repo,
    会从 fixtures/<project_id>/ 拷贝 + git init + 首次 commit。
    这是 dev fixture 行为;生产用户应该自己配真实 repo path。

宪法第 1 条:任务间并行 + worktree 物理隔离。
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from orchestrator._shared import ProjectConfig


class WorktreeError(RuntimeError):
    pass


def _run(cmd: list[str], cwd: Path | None = None, check: bool = True) -> str:
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=60)
    if check and result.returncode != 0:
        raise WorktreeError(
            f"command failed: {' '.join(cmd)}\nstdout: {result.stdout}\nstderr: {result.stderr}"
        )
    return result.stdout


def _is_git_repo(path: Path) -> bool:
    return (path / ".git").exists() or (path / "HEAD").exists()


def ensure_main_repo(project: ProjectConfig, repo_root: Path | None = None) -> Path:
    """确保 local_main_path 是个 git repo。不存在则从 fixtures bootstrap。

    返回主仓库 Path。
    """
    main_path = Path(project.local_main_path).expanduser()
    if _is_git_repo(main_path):
        return main_path

    # bootstrap from fixtures
    repo_root = repo_root or Path.cwd()
    fixture = repo_root / "fixtures" / project.project_id
    if not fixture.exists():
        raise WorktreeError(
            f"主仓库 {main_path} 不存在 git repo,且 fixtures/{project.project_id} 也没有。"
            f"请要么配置真实 local_main_path,要么 mkdir fixtures/{project.project_id}/ 放骨架代码"
        )

    main_path.mkdir(parents=True, exist_ok=True)
    # 拷贝 fixture 内容
    for src in fixture.rglob("*"):
        if src.is_file():
            rel = src.relative_to(fixture)
            dst = main_path / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

    # git init + 配 user(避免 commit 报错)+ 首次 commit
    _run(["git", "init", "-b", project.main_branch], cwd=main_path)
    _run(["git", "config", "user.email", "agent-org-bootstrap@local"], cwd=main_path)
    _run(["git", "config", "user.name", "agent-org-bootstrap"], cwd=main_path)
    _run(["git", "add", "."], cwd=main_path)
    _run(["git", "commit", "-m", f"chore: bootstrap {project.project_id} from fixtures"], cwd=main_path)
    return main_path


def create_worktree(
    task_id: str,
    project: ProjectConfig,
    repo_root: Path | None = None,
) -> Path:
    """为 task_id 创建 worktree。

    返回 worktree 绝对路径。worktree 在新分支 `agent-org/<task_id>` 上。
    如果已经存在(残留),先 cleanup 再新建。
    """
    main_path = ensure_main_repo(project, repo_root).resolve()
    # 必须用绝对路径,否则 git worktree add 会相对 cwd(=main_path)解释 → 递归
    worktree_root = Path(project.worktree_root).expanduser().resolve()
    worktree_root.mkdir(parents=True, exist_ok=True)
    wt = worktree_root / task_id
    branch = f"agent-org/{task_id}"

    # 残留清理 + prune 孤儿引用(防止上次崩溃留下的 worktree 引用阻塞新建)
    if wt.exists():
        cleanup_worktree(task_id, project)
    _run(["git", "worktree", "prune"], cwd=main_path, check=False)

    # -B 而不是 -b:即使同名分支存在也覆盖(残留分支不阻塞)
    _run(
        ["git", "worktree", "add", "--force", str(wt), "-B", branch, project.main_branch],
        cwd=main_path,
    )
    return wt


def cleanup_worktree(task_id: str, project: ProjectConfig) -> None:
    """删除 worktree(force,即使有未提交改动也删)。

    保留 branch(可能 Owner 想 review history)。
    """
    main_path = Path(project.local_main_path).expanduser().resolve()
    worktree_root = Path(project.worktree_root).expanduser().resolve()
    wt = worktree_root / task_id

    if not wt.exists():
        return

    if not _is_git_repo(main_path):
        # 主仓库都没了,直接 rm
        shutil.rmtree(wt, ignore_errors=True)
        return

    # git worktree remove --force
    try:
        _run(
            ["git", "worktree", "remove", str(wt), "--force"],
            cwd=main_path,
            check=False,
        )
    except WorktreeError:
        pass
    # 兜底 rm(git worktree remove 偶尔残留)
    if wt.exists():
        shutil.rmtree(wt, ignore_errors=True)


def worktree_path(task_id: str, project: ProjectConfig) -> Path:
    """取该 task 的 worktree 路径(可能不存在)。"""
    worktree_root = Path(project.worktree_root).expanduser().resolve()
    return worktree_root / task_id


def git_diff(worktree: Path) -> str:
    """跑 git diff HEAD,返回完整 diff 文本。"""
    return _run(["git", "diff", "HEAD"], cwd=worktree, check=False)


def list_changed_files(worktree: Path) -> list[str]:
    """列出 worktree 里有改动(staged + unstaged + untracked)的文件路径。"""
    out = _run(["git", "status", "--porcelain"], cwd=worktree, check=False)
    files = []
    for line in out.splitlines():
        line = line.strip()
        if not line:
            continue
        # `XY path` 格式
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            files.append(parts[1])
    return files
