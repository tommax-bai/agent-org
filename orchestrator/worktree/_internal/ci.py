"""CI 命令执行(Phase 2.4)。

在 worktree 内跑 project.yaml.commands(test / lint / build),
捕获 stdout/stderr/exit_code,放进 Developer artifact 给 Reviewer 看。

Phase 1 痛点:Reviewer 只看文本猜代码行不行 → 过严
Phase 2:Reviewer 看 CI pass/fail → 客观判断
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class CommandResult:
    name: str                 # 命令的 key,如 "test" / "lint"
    command: str              # 实际命令字符串
    exit_code: int
    stdout: str
    stderr: str
    duration_ms: int
    timed_out: bool = False

    @property
    def passed(self) -> bool:
        return self.exit_code == 0 and not self.timed_out

    def to_dict(self) -> dict:
        # stdout/stderr 截断,防止 artifact JSON 过大
        max_chars = 4000
        return {
            "name": self.name,
            "command": self.command,
            "exit_code": self.exit_code,
            "passed": self.passed,
            "duration_ms": self.duration_ms,
            "timed_out": self.timed_out,
            "stdout_tail": self.stdout[-max_chars:] if self.stdout else "",
            "stderr_tail": self.stderr[-max_chars:] if self.stderr else "",
        }


@dataclass
class CIResult:
    results: list[CommandResult] = field(default_factory=list)

    @property
    def all_passed(self) -> bool:
        return all(r.passed for r in self.results)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    def to_dict(self) -> dict:
        return {
            "all_passed": self.all_passed,
            "failed_count": self.failed_count,
            "total": len(self.results),
            "results": [r.to_dict() for r in self.results],
        }


def run_commands(
    worktree: Path,
    commands: dict[str, str],
    timeout_per_cmd: int = 120,
    skip_keys: tuple[str, ...] = ("install",),
) -> CIResult:
    """在 worktree 跑 project.yaml.commands 里的每个命令。

    Args:
        worktree: git worktree 绝对路径
        commands: {"test": "go test ./...", "lint": "go vet ./...", ...}
        timeout_per_cmd: 每个命令超时(秒)
        skip_keys: 默认跳过 install(Phase 2 不预装依赖,假设环境就绪)

    Returns:
        CIResult,Reviewer 拿这个判断
    """
    out = CIResult()
    for name, cmd_str in commands.items():
        if name in skip_keys:
            continue
        import time as _time

        start = _time.time()
        timed_out = False
        try:
            proc = subprocess.run(
                cmd_str,
                shell=True,
                cwd=worktree,
                capture_output=True,
                text=True,
                timeout=timeout_per_cmd,
            )
            stdout, stderr, rc = proc.stdout, proc.stderr, proc.returncode
        except subprocess.TimeoutExpired as e:
            stdout = e.stdout.decode() if isinstance(e.stdout, bytes) else (e.stdout or "")
            stderr = e.stderr.decode() if isinstance(e.stderr, bytes) else (e.stderr or "")
            rc = -1
            timed_out = True

        out.results.append(
            CommandResult(
                name=name,
                command=cmd_str,
                exit_code=rc,
                stdout=stdout,
                stderr=stderr,
                duration_ms=int((_time.time() - start) * 1000),
                timed_out=timed_out,
            )
        )
    return out
