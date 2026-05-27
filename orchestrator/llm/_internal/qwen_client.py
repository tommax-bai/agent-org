"""Qwen via DashScope OpenAI 兼容接口。

需要环境变量 DASHSCOPE_API_KEY。
endpoint: https://dashscope.aliyuncs.com/compatible-mode/v1

模型列表(2026 年中):
    qwen-max         最强,贵
    qwen3-max        新一代旗舰
    qwen-plus        性价比平衡(推荐默认)
    qwen-turbo       快,便宜
    qwen-flash       最便宜
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass


DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass
class QwenResponse:
    text: str
    model: str
    input_tokens: int
    output_tokens: int
    duration_ms: int
    usd: float


# Qwen 定价(USD/1M tokens,2026 年中估算,DashScope 中国区按 RMB 计费转换)
# 真实价格 Owner 在阿里云控制台查,这里用估算值
QWEN_PRICING = {
    "qwen-max": {"input": 2.8, "output": 8.4},
    "qwen3-max": {"input": 2.8, "output": 8.4},
    "qwen-plus": {"input": 0.4, "output": 1.2},
    "qwen-turbo": {"input": 0.3, "output": 0.9},
    "qwen-flash": {"input": 0.15, "output": 0.45},
    "default": {"input": 0.4, "output": 1.2},
}


def estimate_qwen_cost(model: str, input_tokens: int, output_tokens: int) -> float:
    p = QWEN_PRICING.get(model, QWEN_PRICING["default"])
    return (input_tokens / 1_000_000) * p["input"] + (output_tokens / 1_000_000) * p["output"]


from orchestrator.llm._internal.langfuse_trace import trace_llm_call


@trace_llm_call
def call_qwen(
    system_prompt: str,
    user_message: str,
    model: str = "qwen-plus",
    max_tokens: int = 16000,    # Round 6 实测:Developer 长 diff 输出会被截断
    max_retries: int = 2,
) -> QwenResponse:
    """同步调 Qwen(DashScope OpenAI 兼容接口),失败重试,指数退避。"""
    try:
        from openai import OpenAI
    except ImportError as e:
        raise RuntimeError(
            "openai SDK 未安装。运行:.venv/bin/pip install openai"
        ) from e

    api_key = os.environ.get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("缺少环境变量 DASHSCOPE_API_KEY")

    client = OpenAI(api_key=api_key, base_url=DASHSCOPE_BASE_URL)
    last_err: Exception | None = None

    for attempt in range(max_retries + 1):
        start = time.time()
        try:
            response = client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
            )
            duration_ms = int((time.time() - start) * 1000)
            text = response.choices[0].message.content or ""
            usage = response.usage
            input_tokens = usage.prompt_tokens if usage else 0
            output_tokens = usage.completion_tokens if usage else 0
            return QwenResponse(
                text=text,
                model=model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                duration_ms=duration_ms,
                usd=estimate_qwen_cost(model, input_tokens, output_tokens),
            )
        except Exception as e:
            last_err = e
            if attempt < max_retries:
                time.sleep(2**attempt)
                continue
            raise

    raise RuntimeError("call_qwen unreachable") from last_err
