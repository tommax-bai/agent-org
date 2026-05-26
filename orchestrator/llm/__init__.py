"""LLM 抽象层。按 model 前缀分发到 provider:
- claude-*        → Anthropic
- qwen-* / qwen3-* → DashScope OpenAI 兼容(Qwen)

加新 provider:在 _internal/dispatch.py 加分支。
"""

from orchestrator.llm._internal.anthropic_client import call_claude, estimate_cost
from orchestrator.llm._internal.dispatch import LLMCallResult, call_llm
from orchestrator.llm._internal.qwen_client import call_qwen

__all__ = [
    "call_llm",
    "LLMCallResult",
    # provider-specific(直接用不推荐,改用 call_llm)
    "call_claude",
    "call_qwen",
    "estimate_cost",
]
