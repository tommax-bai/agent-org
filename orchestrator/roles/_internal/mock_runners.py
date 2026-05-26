"""Mock runner(0B 阶段除 PM 外其他角色全用 mock,v2.4 边界)。

Mock 行为:
- 默认返 verdict=success + 合理 artifact.content
- 通过 task.mock_behavior 可以 override 特定角色的行为(测 needs_changes / escalate / signal)

mock_behavior 格式(task.yaml 可选字段,只 0B 用):
    mock_behavior:
      developer:                    # 按 role_id key
        default:
          verdict: success
        attempt_2:                  # 第 2 次 attempt 时
          verdict: success
      reviewer:
        default:
          verdict: needs_changes    # 第一次让 developer 重做
        attempt_2:
          verdict: success
"""

from __future__ import annotations

from typing import Any

import yaml

from orchestrator._shared import CostUsed, RoleConfig, RoleInvocationInput
from orchestrator.roles._internal.protocol import RoleRunner


# 各 artifact_type 的默认 mock content(符合 schema)
DEFAULT_MOCK_CONTENT: dict[str, dict[str, Any]] = {
    "code": {
        "summary": "[MOCK] 完成了 subtask 的代码改动",
        "proposed_changes": [
            {
                "file": "src/example.go",
                "operation": "modify",
                "description": "mock change",
            }
        ],
        "risks": [],
        "followups": [],
    },
    "review": {
        "verdict": "approve",
        "must_escalate_to_owner": False,
        "escalation_reason": "",
        "correctness_score": 8,
        "design_quality_score": 8,
        "test_coverage": "adequate",
        "blocking_issues": [],
        "non_blocking_issues": [],
        "confidence": 0.85,
    },
    "design": {
        "decision_summary": "[MOCK] 推荐方案 A",
        "proposed_design": {
            "components": [{"name": "MockComponent", "responsibility": "占位"}],
            "data_flow": "input → process → output",
            "key_decisions": [],
        },
        "affected_modules": ["mock"],
        "technical_choices": [],
        "suggested_implementation_steps": ["step 1", "step 2"],
        "risks": [],
        "confidence": 0.8,
    },
    "analysis": {"content_text": "[MOCK] 通用 analysis 占位", "confidence": 0.7},
}


class MockRunner(RoleRunner):
    """除 PM 外角色的 mock 实现。

    返回符合 schema 的固定数据。可以通过 RoleInvocationInput 上的 mock_behavior
    覆盖默认行为(0B 阶段 testing用)。
    """

    def __init__(
        self,
        role_config: RoleConfig,
        attempt: int = 1,
        mock_behavior: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(role_config=role_config, attempt=attempt)
        self.mock_behavior = mock_behavior or {}

    def _invoke(self, system_prompt: str, user_message: str) -> tuple[str, CostUsed]:
        # 1. 决定 verdict / signals(看 mock_behavior)
        role_id = self.role_config.role_id
        cfg = self.mock_behavior.get(role_id, {})
        attempt_key = f"attempt_{self.attempt}"
        applied = {**cfg.get("default", {}), **cfg.get(attempt_key, {})}
        verdict = applied.get("verdict", "success")
        signals = applied.get("signals", [])

        # 2. 决定 content
        artifact_type = self.role_config.artifact_type
        content = applied.get("content")
        if content is None:
            # 用 default,如果是 review 类且 verdict=escalate,自动联动 must_escalate
            content = dict(DEFAULT_MOCK_CONTENT.get(artifact_type, {}))
            if artifact_type == "review":
                if verdict == "needs_changes":
                    content["verdict"] = "request_changes"
                    content["correctness_score"] = 6
                elif verdict == "escalate":
                    content["verdict"] = "reject"
                    content["must_escalate_to_owner"] = True
                    content["escalation_reason"] = applied.get(
                        "escalation_reason", "[MOCK] 模拟触发 escalate"
                    )

        # 3. 拼 YAML
        output = {
            "verdict": verdict,
            "artifact": {"type": artifact_type, "content": content},
            "signals_to_other_roles": signals,
        }
        text = yaml.safe_dump(output, allow_unicode=True, sort_keys=False)

        # mock 没有真实 cost
        return text, CostUsed(llm_tokens=0, duration_ms=10, usd=0.0)
