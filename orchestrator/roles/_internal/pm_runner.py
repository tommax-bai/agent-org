"""PM 真 LLM runner(v2.4:Phase 0B 唯一真 LLM 的角色)。

模型从 role.yaml 的 model_policy.preferred 读,通过 orchestrator.llm.call_llm
按前缀分发到 Anthropic / Qwen。
"""

from __future__ import annotations

from orchestrator._shared import CostUsed
from orchestrator.llm import call_llm
from orchestrator.roles._internal.protocol import RoleRunner


class PMRunner(RoleRunner):
    """调真实 LLM(Claude / Qwen / ...)。"""

    def _invoke(self, system_prompt: str, user_message: str) -> tuple[str, CostUsed]:
        model = self.role_config.model_policy.get("preferred", "qwen-plus")
        max_tokens = int(self.role_config.budget.get("max_tokens", 4000))
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
