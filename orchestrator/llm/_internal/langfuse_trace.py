"""Langfuse 可观测性集成。

环境变量(都为空则静默跳过,跟 0B 行为一致):
    LANGFUSE_HOST          (默认 http://localhost:3000)
    LANGFUSE_PUBLIC_KEY
    LANGFUSE_SECRET_KEY

用法:
    @trace_llm_call
    def call_qwen(...): ...

trace_llm_call 装饰器透明包装 call_*,失败时不影响主流程(吃异常)。
"""

from __future__ import annotations

import functools
import os
import time
from typing import Any, Callable, TypeVar

R = TypeVar("R")


_LANGFUSE_CLIENT: Any | None = None
_LANGFUSE_TRIED = False


def _get_langfuse() -> Any | None:
    """惰性初始化。返回 None 表示 Langfuse 未配置或加载失败。

    给 Langfuse 传一个 trust_env=False 的 httpx client,避免国内开发机的
    HTTP_PROXY / macOS 系统代理把 localhost:3000 走代理拐弯(LLM 调用走代理
    不受影响,因为 LLM 用的是另外的 httpx 实例)。
    """
    global _LANGFUSE_CLIENT, _LANGFUSE_TRIED
    if _LANGFUSE_TRIED:
        return _LANGFUSE_CLIENT
    _LANGFUSE_TRIED = True

    public_key = os.environ.get("LANGFUSE_PUBLIC_KEY")
    secret_key = os.environ.get("LANGFUSE_SECRET_KEY")
    if not public_key or not secret_key:
        return None

    try:
        import httpx
        from langfuse import Langfuse
    except ImportError:
        return None

    host = os.environ.get("LANGFUSE_HOST", "http://localhost:3000")
    try:
        # trust_env=False:完全忽略 HTTP_PROXY / HTTPS_PROXY / 系统代理
        # 因为 Langfuse 通常是 localhost(self-hosted)或者公网直连,不该走代理
        direct_client = httpx.Client(trust_env=False, timeout=20)
        _LANGFUSE_CLIENT = Langfuse(
            public_key=public_key,
            secret_key=secret_key,
            host=host,
            httpx_client=direct_client,
        )
    except Exception:
        _LANGFUSE_CLIENT = None
    return _LANGFUSE_CLIENT


def trace_llm_call(fn: Callable[..., R]) -> Callable[..., R]:
    """装饰 LLM 调用函数。上报 trace + cost + duration 到 Langfuse。

    fn 期望返回带 .text / .model / .input_tokens / .output_tokens / .usd /
    .duration_ms 属性的对象(LLMResponse / QwenResponse 都符合)。
    """

    @functools.wraps(fn)
    def wrapped(*args: Any, **kwargs: Any) -> R:
        lf = _get_langfuse()
        if lf is None:
            return fn(*args, **kwargs)

        # 提取 system_prompt / user_message / model
        system_prompt = kwargs.get("system_prompt") or (args[0] if args else "")
        user_message = kwargs.get("user_message") or (args[1] if len(args) > 1 else "")
        model = kwargs.get("model", "unknown")

        start = time.time()
        try:
            result = fn(*args, **kwargs)
        except Exception as e:
            try:
                lf.generation(
                    name="llm_call_error",
                    model=model,
                    input={"system": system_prompt[:500], "user": user_message[:2000]},
                    level="ERROR",
                    status_message=str(e)[:500],
                )
                lf.flush()
            except Exception:
                pass
            raise

        try:
            lf.generation(
                name=f"llm_call_{model}",
                model=model,
                input={"system": system_prompt[:500], "user": user_message[:2000]},
                output=getattr(result, "text", "")[:2000],
                usage={
                    "input": getattr(result, "input_tokens", 0),
                    "output": getattr(result, "output_tokens", 0),
                    "total_cost": getattr(result, "usd", 0.0),
                    "unit": "TOKENS",
                },
                metadata={
                    "duration_ms": getattr(result, "duration_ms", 0),
                    "elapsed_ms": int((time.time() - start) * 1000),
                },
            )
            lf.flush()
        except Exception:
            # 监控失败不影响主流程
            pass
        return result

    return wrapped
