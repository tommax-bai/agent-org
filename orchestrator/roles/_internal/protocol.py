"""RoleRunner 抽象 + 通用执行流程。

execute() 是入口,内部调:
  1. build_user_message  - 把 context_pack 转成 prompt
  2. _invoke              - 子类实现(真 LLM 或 mock)
  3. parse_output         - 解析 LLM 返回的 YAML
  4. validate_output      - 校验 artifact.content 符合 schema(每种 artifact_type 一个 schema)
  5. consistency_check    - v2.4 一致性校验(如 Reviewer must_escalate_to_owner ↔ verdict)

failed -> retry 1 次,再失败 → ESCALATE(宪法第 12 条)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator

from orchestrator._shared import (
    Artifact,
    CostUsed,
    RoleConfig,
    RoleInvocationInput,
    RoleInvocationOutput,
)
from orchestrator.artifact import make_artifact_id


SCHEMAS_DIR = Path(__file__).resolve().parents[3] / "schemas"


class RoleExecutionError(Exception):
    """role 执行失败(retry 后仍不通过 / 一致性校验失败)。"""

    def __init__(self, kind: str, detail: str, retryable: bool = True) -> None:
        super().__init__(f"[{kind}] {detail}")
        self.kind = kind
        self.detail = detail
        self.retryable = retryable


def _load_artifact_content_schema(artifact_type: str) -> dict[str, Any] | None:
    """按 type 加载 artifact_content schema。找不到返回 None(analysis 兜底等)。

    特殊映射:dispatch_plan 直接用 schemas/pm_dispatch_plan.schema.json
    (artifact_content/dispatch_plan.schema.json 是 $ref 转发,jsonschema 不
    解析相对路径,这里直接绕过)。
    """
    if artifact_type == "dispatch_plan":
        p = SCHEMAS_DIR / "pm_dispatch_plan.schema.json"
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        return None
    p = SCHEMAS_DIR / "artifact_content" / f"{artifact_type}.schema.json"
    if p.exists():
        return json.loads(p.read_text(encoding="utf-8"))
    return None


class RoleRunner(ABC):
    """所有角色 runner 的基类。"""

    def __init__(self, role_config: RoleConfig, attempt: int = 1) -> None:
        self.role_config = role_config
        self.attempt = attempt

    # ---- 子类必须实现的钩子 ----

    @abstractmethod
    def _invoke(self, system_prompt: str, user_message: str) -> tuple[str, CostUsed]:
        """实际跑 role(真 LLM 或 mock)。返回 raw text + cost。"""
        ...

    # ---- 通用流程 ----

    def execute(self, inp: RoleInvocationInput, max_retries: int = 1) -> RoleInvocationOutput:
        """完整流程:build prompt → invoke → parse → schema 校验 → 一致性校验。

        v2.4:任何步骤失败 → retry 最多 max_retries 次,再失败 → raise(由 caller escalate)。
        """
        system_prompt = self.role_config.system_prompt
        user_message = self._build_user_message(inp)

        last_err: RoleExecutionError | None = None
        for attempt in range(max_retries + 1):
            try:
                raw_text, cost = self._invoke(system_prompt, user_message)
                parsed = self._parse_output(raw_text)
                self._validate_output(parsed)
                self._consistency_check(parsed)
                return self._build_output(inp, parsed, cost)
            except RoleExecutionError as e:
                last_err = e
                if not e.retryable or attempt >= max_retries:
                    raise
                # retry 时把错误信息注入 user_message
                user_message = self._append_retry_context(user_message, e)
                continue

        assert last_err is not None
        raise last_err

    # ---- 默认实现,子类可 override ----

    def _build_user_message(self, inp: RoleInvocationInput) -> str:
        """把 context_pack 序列化成 LLM 输入。"""
        ctx = inp.context_pack.model_dump(exclude_none=True)
        # 把 related_artifacts 简化(只显示 type + content,不展开元数据)
        if ctx.get("related_artifacts"):
            ctx["related_artifacts"] = [
                {"type": a["type"], "content": a["content"]}
                for a in ctx["related_artifacts"]
            ]
        # signals
        signals_yaml = ""
        if inp.prior_role_signals:
            signals_yaml = "\n\nprior_role_signals:\n" + yaml.safe_dump(
                [s.model_dump() for s in inp.prior_role_signals], allow_unicode=True
            )
        return (
            f"以下是 role_invocation_input:\n\n```yaml\n"
            + yaml.safe_dump(ctx, allow_unicode=True, sort_keys=False)
            + "```"
            + signals_yaml
            + "\n\n请按 system prompt 第 3 节的 output schema,输出完整的 YAML(不要 wrap 在 code fence 里)。"
        )

    def _parse_output(self, raw: str) -> dict[str, Any]:
        """解析 LLM 输出为 dict。容错处理 code fence wrap。"""
        text = raw.strip()
        if text.startswith("```"):
            # 去掉 code fence
            lines = text.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines)
        try:
            parsed = yaml.safe_load(text)
        except yaml.YAMLError as e:
            raise RoleExecutionError("yaml_parse", f"LLM 输出不是合法 YAML: {e}") from e
        if not isinstance(parsed, dict):
            raise RoleExecutionError(
                "yaml_parse", f"LLM 输出不是 dict,got {type(parsed).__name__}"
            )
        return parsed

    def _validate_output(self, parsed: dict[str, Any]) -> None:
        """校验顶层 protocol 字段 + artifact.content schema。"""
        # 顶层必须字段
        for f in ("verdict", "artifact"):
            if f not in parsed:
                raise RoleExecutionError("missing_field", f"输出缺少顶层字段 {f}")
        if parsed["verdict"] not in ("success", "needs_changes", "escalate"):
            raise RoleExecutionError(
                "bad_verdict",
                f"verdict={parsed['verdict']!r},必须是 success / needs_changes / escalate",
            )
        artifact = parsed["artifact"]
        if not isinstance(artifact, dict):
            raise RoleExecutionError("bad_artifact", "artifact 不是 dict")
        for f in ("type", "content"):
            if f not in artifact:
                raise RoleExecutionError("missing_field", f"artifact 缺少 {f}")

        # artifact.content schema 校验
        schema = _load_artifact_content_schema(artifact["type"])
        if schema is None:
            # 没有对应 schema,跳过(analysis 自由格式等)
            return
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(artifact["content"]))
        if errors:
            err_msgs = "\n".join(f"  - {e.json_path}: {e.message}" for e in errors[:5])
            raise RoleExecutionError(
                "schema_violation",
                f"artifact.content 不符合 {artifact['type']}.schema:\n{err_msgs}",
            )

    def _consistency_check(self, parsed: dict[str, Any]) -> None:
        """v2.4 一致性校验。Reviewer 类角色:must_escalate=true → verdict=escalate + 顶层 verdict=escalate。

        子类可 override 加更多角色规则。
        """
        artifact = parsed.get("artifact", {})
        if artifact.get("type") == "review":
            content = artifact.get("content", {})
            if content.get("must_escalate_to_owner"):
                if not content.get("escalation_reason"):
                    raise RoleExecutionError(
                        "consistency",
                        "must_escalate_to_owner=true 但 escalation_reason 为空",
                    )
                if content.get("verdict") != "reject":
                    raise RoleExecutionError(
                        "consistency",
                        f"must_escalate_to_owner=true 但 review.verdict={content.get('verdict')},应为 reject",
                    )
                if parsed.get("verdict") != "escalate":
                    raise RoleExecutionError(
                        "consistency",
                        f"must_escalate_to_owner=true 但顶层 verdict={parsed.get('verdict')},应为 escalate",
                    )

    def _build_output(
        self,
        inp: RoleInvocationInput,
        parsed: dict[str, Any],
        cost: CostUsed,
    ) -> RoleInvocationOutput:
        artifact_data = parsed["artifact"]
        artifact = Artifact(
            artifact_id=make_artifact_id(),
            type=artifact_data["type"],
            content=artifact_data["content"],
            attempt=self.attempt,
            task_id=inp.task_id,
            subtask_id=inp.subtask_id,
            role_id=inp.role_id,
            created_at=datetime.utcnow(),
        )
        signals_raw = parsed.get("signals_to_other_roles", []) or []
        from orchestrator._shared import Signal

        signals = [Signal(**s) for s in signals_raw]
        return RoleInvocationOutput(
            role_id=inp.role_id,
            task_id=inp.task_id,
            subtask_id=inp.subtask_id,
            verdict=parsed["verdict"],
            artifact=artifact,
            signals_to_other_roles=signals,
            cost_used=cost,
        )

    def _append_retry_context(self, msg: str, err: RoleExecutionError) -> str:
        return (
            msg
            + "\n\n"
            + "上一次输出有问题,请修正后重新输出完整 YAML:\n"
            + f"- 错误类型:{err.kind}\n"
            + f"- 详细:{err.detail}\n"
        )
