"""统一 LLM 调用入口,按 model 前缀分发到 Anthropic / Qwen。

支持:
    claude-*        → orchestrator.llm._internal.anthropic_client.call_claude
    qwen-* / qwen3-* → orchestrator.llm._internal.qwen_client.call_qwen

加新 provider:在 PROVIDER_MAP 注册前缀即可。
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class LLMCallResult:
    """统一返回类型(屏蔽 Anthropic / Qwen 差异)。"""

    text: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    usd: float


def call_llm(
    system_prompt: str,
    user_message: str,
    model: str,
    max_tokens: int = 4000,
    max_retries: int = 2,
) -> LLMCallResult:
    if model.startswith("claude-"):
        from orchestrator.llm._internal.anthropic_client import call_claude

        r = call_claude(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )
        return LLMCallResult(
            text=r.text,
            model=r.model,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            duration_ms=r.duration_ms,
            usd=r.usd,
        )

    if model.startswith("qwen") or model.startswith("qwen3"):
        from orchestrator.llm._internal.qwen_client import call_qwen

        r = call_qwen(
            system_prompt=system_prompt,
            user_message=user_message,
            model=model,
            max_tokens=max_tokens,
            max_retries=max_retries,
        )
        return LLMCallResult(
            text=r.text,
            model=r.model,
            input_tokens=r.input_tokens,
            output_tokens=r.output_tokens,
            duration_ms=r.duration_ms,
            usd=r.usd,
        )

    raise ValueError(
        f"不支持的模型 {model!r}。已注册前缀:claude-*, qwen-*, qwen3-*。"
        f"加新 provider 在 orchestrator/llm/_internal/dispatch.py 注册。"
    )
