"""LLM 抽象层:包装 Anthropic SDK。

Phase 0B 只做最小集:
- 调用 + 重试(最多 2 次,指数退避)
- 简单 cost 估算(基于 token 数 + 模型定价)
- 返回 raw text(让 caller 自己解析 YAML / JSON)

Phase 0C+ 在这里加 Langfuse instrumentation。
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass
from typing import Any

# 模型定价(USD per 1M tokens,2026 年中估值)
# 注:走 Zenmux 等代理实际费用以代理商账单为准,这里只用于 budget 预估
PRICING = {
    "claude-sonnet-4-5": {"input": 3.0, "output": 15.0},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0},
    "claude-opus-4-7": {"input": 15.0, "output": 75.0},
    "claude-haiku-4-5-20251001": {"input": 0.8, "output": 4.0},
    # fallback
    "default": {"input": 3.0, "output": 15.0},
}


@dataclass
class LLMResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    usd: float


def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = PRICING.get(model, PRICING["default"])
    return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]


from orchestrator.llm._internal.langfuse_trace import trace_llm_call


@trace_llm_call
def call_claude(
    system_prompt: str,
    user_message: str,
    model: str = "claude-sonnet-4-5",
    max_tokens: int = 16000,   # Round 6 实测:长 diff 输出会被 4000 截断 → JSON parse 失败
    max_retries: int = 2,
) -> LLMResponse:
    """同步调用 Claude API,失败重试最多 max_retries 次,指数退避。"""
    try:
        from anthropic import Anthropic
    except ImportError as e:
        raise RuntimeError(
            "anthropic SDK 未安装。运行:uv pip install anthropic 或 .venv/bin/pip install anthropic"
        ) from e

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("缺少环境变量 ANTHROPIC_API_KEY")

    # 支持自定义 base_url(走 Zenmux / 其他 Anthropic 兼容代理)
    base_url = os.environ.get("ANTHROPIC_BASE_URL")
    client_kwargs: dict[str, Any] = {"api_key": api_key}
    if base_url:
        client_kwargs["base_url"] = base_url
    client = Anthropic(**client_kwargs)
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        start = time.time()
        try:
            response = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_message}],
            )
            duration_ms = int((time.time() - start) * 1000)

            # 提取文本
            text_blocks = [
                b.text  # type: ignore[union-attr]
                for b in response.content
                if getattr(b, "type", None) == "text"
            ]
            text = "\n".join(text_blocks)

            usage = response.usage
            return LLMResponse(
                text=text,
                model=model,
                input_tokens=usage.input_tokens,
                output_tokens=usage.output_tokens,
                duration_ms=duration_ms,
                usd=estimate_cost(model, usage.input_tokens, usage.output_tokens),
            )
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                sleep_s = 2**attempt
                time.sleep(sleep_s)
                continue
            raise

    # 不该到这
    raise RuntimeError("call_claude unreachable") from last_err
