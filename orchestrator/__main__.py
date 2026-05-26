"""python -m orchestrator run <task.yaml>

Phase 0B 命令行入口。
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from orchestrator._runtime import build_task_state
from orchestrator.escalation import write_escalation, write_final_report
from orchestrator.state_machine import run_task


def main() -> int:
    parser = argparse.ArgumentParser(description="agent-org 主进程(Phase 0B)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="跑一个 task.yaml")
    run_p.add_argument("task_yaml", type=Path)
    run_p.add_argument(
        "--projects-root",
        type=Path,
        default=Path.cwd() / "projects",
        help="projects/ 目录(默认当前目录下的 projects/)",
    )

    args = parser.parse_args()

    if args.cmd == "run":
        if not args.task_yaml.exists():
            print(f"ERROR: task.yaml 不存在: {args.task_yaml}", file=sys.stderr)
            return 2

        try:
            state = build_task_state(args.task_yaml, args.projects_root)
        except Exception as e:
            print(f"ERROR: 加载配置失败: {e}", file=sys.stderr)
            return 3

        print(f"▶  跑任务 {state.task.task_id}: {state.task.title}")
        print(f"   project={state.task.project_id}, budget=${state.task.budget_usd}")
        print()

        state = run_task(state)

        print()
        print(f"✓ 状态: {state.status}")
        print(f"  花费: ${state.cost_used_usd:.4f} / ${state.budget_usd:.2f}")
        if state.status == "DONE":
            path = write_final_report(state)
            print(f"  报告: {path}")
            return 0
        else:
            path = write_escalation(state)
            print(f"  升级原因: {state.escalation_reason}")
            print(f"  详细: {state.escalation_detail}")
            print(f"  升级文档: {path}")
            return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
