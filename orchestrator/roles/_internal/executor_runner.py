"""Developer 类角色的 executor:LLM 输出 file_edits → Python 写盘 → git diff 拿真实 diff。

Phase 2 替代 Phase 1 的 proposed_changes 模式:
- Phase 1 痛点:LLM 输出长 diff 文本塞进 JSON,parse 失败率高
- Phase 2 方案:LLM 只输出 file_edits(每个文件完整内容或简单操作),Python 写盘后用 git diff 拿真实 diff

file_edits 格式(LLM 输出):
    [
        {"path": "src/x.go", "operation": "create",  "content": "<file content>"},
        {"path": "src/y.go", "operation": "modify",  "content": "<full new content>"},
        {"path": "src/z.go", "operation": "delete"},
    ]

Python 处理流程:
1. 校验每个 path 不命中 protected_paths hard_block(违反就 raise → role retry)
2. APPROVAL / WARN 级别记录到 result(汇给 Owner)
3. 在 worktree 内写盘(create / overwrite / unlink)
4. git diff HEAD 拿真实 diff
5. artifact.content augment:加 changed_files + git_diff + protected_warnings
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from orchestrator._shared import CostUsed, RoleConfig, RoleInvocationInput
from orchestrator.llm import call_llm
from orchestrator.roles._internal.protocol import RoleExecutionError, RoleRunner
from orchestrator.worktree import (
    PathProtection,
    ProtectedPathError,
    assert_writable,
    git_diff,
    list_changed_files,
    run_commands,
)


class FileExecutorRunner(RoleRunner):
    """Developer / 任何写文件类角色用。

    LLM 输出含 artifact.content.file_edits;execute 后系统 augment 真实 diff。
    """

    def __init__(
        self,
        role_config: RoleConfig,
        attempt: int = 1,
        worktree: Path | None = None,
        protected_paths: dict[str, list[str]] | None = None,
        ci_commands: dict[str, str] | None = None,
    ) -> None:
        super().__init__(role_config=role_config, attempt=attempt)
        if worktree is None:
            raise ValueError("FileExecutorRunner 需要 worktree 路径(Phase 2 任务必须有 worktree)")
        self.worktree = worktree
        self.protected_paths = protected_paths or {}
        self.ci_commands = ci_commands or {}

    def _invoke(self, system_prompt: str, user_message: str) -> tuple[str, CostUsed]:
        """先调 LLM 拿 file_edits,然后 caller 在 _build_output 里执行写盘。"""
        model = self.role_config.model_policy.get("preferred", "qwen-plus")
        max_tokens = int(self.role_config.budget.get("max_tokens", 16000))
        resp = call_llm(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            max_tokens=max_tokens,
        )
        cost = CostUsed(
            llm_tokens=resp.input_tokens + resp.output_tokens,
            duration_ms=resp.duration_ms,
            usd=resp.usd,
        )
        return resp.text, cost

    def _build_user_message(self, inp: RoleInvocationInput) -> str:
        """加入 worktree 提示。"""
        base = super()._build_user_message(inp)
        # 列出 worktree 当前文件清单,LLM 知道改什么
        try:
            files = sorted(
                str(p.relative_to(self.worktree))
                for p in self.worktree.rglob("*")
                if p.is_file() and ".git" not in p.parts
            )[:50]
        except Exception:
            files = []
        worktree_hint = (
            f"\n\n# Worktree 信息(你的代码生效环境)\n\n"
            f"工作目录:{self.worktree}\n\n"
            f"当前文件清单(部分):\n"
            + "\n".join(f"- {f}" for f in files)
            + "\n\n"
            "# 输出格式(重要,跟 Phase 1 不同)\n\n"
            "你的 artifact.content 必须含 `file_edits` 字段,**不再用** `proposed_changes`。\n"
            "格式:\n"
            "```json\n"
            "{\n"
            '  "summary": "做了什么(一两句话)",\n'
            '  "file_edits": [\n'
            '    {"path": "src/x.go", "operation": "create", "content": "<完整文件内容>"},\n'
            '    {"path": "src/y.go", "operation": "modify", "content": "<完整新内容,不是 diff>"},\n'
            '    {"path": "src/z.go", "operation": "delete"}\n'
            "  ],\n"
            '  "risks": ["可能的风险"],\n'
            '  "followups": []\n'
            "}\n"
            "```\n"
            "**critical**: `content` 字段是文件**完整新内容**(不是 diff,不是 patch)。\n"
            "系统会用你给的内容**整文件覆盖写盘**,然后用 git diff 自动生成真实 diff。\n"
            "你不需要也不应该输出 diff 文本——Phase 1 那样会让 JSON 崩。"
        )
        return base + worktree_hint

    def _validate_output(self, parsed: dict[str, Any]) -> None:
        """先做顶层 + artifact 类型校验。然后 file_edits 业务校验。"""
        super()._validate_output(parsed)
        artifact = parsed.get("artifact", {})
        content = artifact.get("content", {})
        edits = content.get("file_edits")
        if edits is None:
            # Phase 2 必须用 file_edits,proposed_changes 是 Phase 1 遗留
            raise RoleExecutionError(
                "missing_file_edits",
                "Phase 2 要求 artifact.content 含 file_edits 字段(不要用 proposed_changes)。"
                "格式:[{path, operation: create|modify|delete, content?}]",
            )
        if not isinstance(edits, list):
            raise RoleExecutionError("bad_file_edits", "file_edits 必须是 list")
        for i, e in enumerate(edits):
            if not isinstance(e, dict):
                raise RoleExecutionError("bad_file_edits", f"file_edits[{i}] 不是 dict")
            if "path" not in e or "operation" not in e:
                raise RoleExecutionError(
                    "bad_file_edits",
                    f"file_edits[{i}] 缺 path 或 operation",
                )
            if e["operation"] not in ("create", "modify", "delete"):
                raise RoleExecutionError(
                    "bad_file_edits",
                    f"file_edits[{i}] operation={e['operation']!r},必须 create/modify/delete",
                )
            if e["operation"] != "delete" and "content" not in e:
                raise RoleExecutionError(
                    "bad_file_edits",
                    f"file_edits[{i}] (create/modify) 必须有 content 字段(完整文件内容)",
                )

    def _build_output(self, inp, parsed, cost):
        """覆盖父类:执行 file_edits + augment artifact.content。"""
        artifact_data = parsed["artifact"]
        content = artifact_data.get("content", {})
        edits = content.get("file_edits", [])

        # 1. protected_paths 检查(hard_block 直接 raise → role retry)
        warnings: list[dict[str, str]] = []
        approval_paths: list[str] = []
        for e in edits:
            try:
                result = assert_writable(e["path"], self.protected_paths)
            except ProtectedPathError as ex:
                raise RoleExecutionError(
                    "protected_path",
                    f"file_edits 含 hard_block 路径 {ex.path!r}(命中 {ex.pattern!r}),拒绝执行。"
                    f"换个路径或者从 file_edits 里删掉这条",
                ) from ex
            if result.level == PathProtection.APPROVAL:
                approval_paths.append(e["path"])
                warnings.append({
                    "path": e["path"],
                    "level": "approval_required",
                    "pattern": result.matched_pattern or "",
                })
            elif result.level == PathProtection.WARN:
                warnings.append({
                    "path": e["path"],
                    "level": "warn_only",
                    "pattern": result.matched_pattern or "",
                })

        # 2. 写盘
        for e in edits:
            target = self.worktree / e["path"]
            op = e["operation"]
            if op == "delete":
                if target.exists():
                    target.unlink()
            else:  # create / modify
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text(e["content"], encoding="utf-8")

        # 3. 跑 git diff + list_changed_files 拿真实数据
        diff_text = git_diff(self.worktree)
        actual_changed = list_changed_files(self.worktree)

        # 4. Phase 2.4:跑 CI 命令(test / lint / build),输出进 artifact
        ci_output = None
        if self.ci_commands:
            ci_result = run_commands(self.worktree, self.ci_commands)
            ci_output = ci_result.to_dict()

        # 5. augment artifact.content
        content["changed_files"] = actual_changed
        content["git_diff"] = diff_text
        content["protected_warnings"] = warnings
        content["approval_required_paths"] = approval_paths
        if ci_output is not None:
            content["ci_output"] = ci_output
        # file_edits 本身可以删了(diff 已经 captured),让 content 短一点
        # 但保留 file_edits 方便 debug
        artifact_data["content"] = content

        # 调父类 _build_output 完成剩下的 wrap
        from orchestrator._shared import Artifact, Signal
        from orchestrator.artifact import make_artifact_id
        from datetime import datetime

        artifact = Artifact(
            artifact_id=make_artifact_id(),
            type=artifact_data["type"],
            content=content,
            attempt=self.attempt,
            task_id=inp.task_id,
            subtask_id=inp.subtask_id,
            role_id=inp.role_id,
            created_at=datetime.utcnow(),
        )
        signals_raw = parsed.get("signals_to_other_roles", []) or []
        try:
            signals = [Signal(**s) for s in signals_raw]
        except Exception as e:
            raise RoleExecutionError(
                "signal_schema",
                f"signals_to_other_roles 字段格式错: {e}",
            ) from e

        from orchestrator._shared import RoleInvocationOutput

        return RoleInvocationOutput(
            role_id=inp.role_id,
            task_id=inp.task_id,
            subtask_id=inp.subtask_id,
            verdict=parsed["verdict"],
            artifact=artifact,
            signals_to_other_roles=signals,
            cost_used=cost,
        )

    def _validate_output_schema_for_artifact(self, parsed):
        """skip 父类的 artifact_content schema 校验——因为 LLM 给的 content 不完整
        (system augment 后才完整),提前校验会失败。"""
        pass
