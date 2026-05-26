# Phase 0C PoC 验证结果

> Spec C.2 要求三个 PoC 各 1 天硬时间盒。失败立即走 fallback,**架构不变**。
>
> 最后更新:2026-05-26

---

## PoC #1: LangGraph 作为状态机

### 验证清单(Spec C.2.1)

| 项 | 状态 | 备注 |
|---|---|---|
| checkpoint 在 long-running 任务可靠 | ✅ 通过 | MemorySaver 验证完整 flow,task 跑完前后 state 一致 |
| 中途 kill orchestrator 后从 checkpoint 恢复 | ⏳ 待验证 | 需 SqliteSaver / PostgresSaver(docker 起来后跑) |
| 节点 timeout 可靠 | ⏳ 待验证 | LangGraph 1.x 节点天然支持 timeout,真跑长任务再测 |
| budget exceeded 硬中断 | ✅ 通过 | 走 conditional_edges 路由到 END,跟自写版等价 |
| event 可以回放 | ✅ 通过 | events.jsonl + Postgres task_events 都是 append-only,LangGraph stream replay 也支持 |

### 结论

**LangGraph PoC 基本通过**,可作为 self_written 的替代实现。

工程实现:
- `orchestrator/state_machine/_internal/langgraph_graph.py` 用 LangGraph 1.2 StateGraph
- 跟自写版共享底层逻辑(`_pm_planning` / `_dispatch_loop`),仅状态机骨架不同
- 通过 `STATE_MACHINE=langgraph` 环境变量切换,默认 `self_written`(0B 行为)

设计选择:**不把 DISPATCH 拆成多个 LangGraph 节点**(role_executing 等),
DISPATCH 整个循环当一个节点。Trade-off:checkpoint 颗粒度变粗(只在
PM_PLANNING / DISPATCH 边界 checkpoint,不能恢复到某个 role 调用之后)。
**Phase 1+ 真有需求**(比如长任务跑一半挂了想精确恢复)再拆细。

### 不通过的话怎么办

保留 `self_written` 自写状态机(0B 已经验证完整)。架构不变,只是不用 LangGraph。
切回:`unset STATE_MACHINE` 或 `STATE_MACHINE=self_written`。

---

## PoC #2: Langfuse(self-hosted)

### 验证清单(Spec C.2.2)

| 项 | 状态 | 备注 |
|---|---|---|
| 自部署 Langfuse 能正确接收 trace | ⏳ 待验证 | docker compose up 后跑实际任务验证 |
| cost 计算准确(对比 anthropic/dashscope 账单) | ⏳ 待验证 | 跑 10+ 任务后对比 |
| 高频写入稳定(连续 10 任务) | ⏳ 待验证 | 跑 PoC stress test |

### 工程实现

- `orchestrator/llm/_internal/langfuse_trace.py` `@trace_llm_call` 装饰器
- 所有 `call_claude` / `call_qwen` 自动上报
- LANGFUSE_PUBLIC_KEY 未配时**静默跳过**(0B 行为不变,本地开发友好)

### 不通过的话怎么办

保留 structlog + Postgres task_events,自己写最简 dashboard(SQL 查询)。
代价:看 trace 不如 Langfuse UI 直观,但**功能 100% 等价**。

---

## PoC #3: Anthropic SDK / Qwen DashScope

### 验证清单

| 项 | 状态 | 备注 |
|---|---|---|
| 真实 LLM 调用稳定 | ✅ 通过 | Qwen plus 跑 task-2026-05-26-001 → DONE,4 个 subtask 拆解合理 |
| error 重试逻辑健康 | ✅ 通过 | 2 次重试 + 指数退避,代码层验证 |
| tool use 稳定 | N/A | V1 不用 tool use(Phase 2+ Claude Code CLI 才用) |
| streaming | N/A | V1 同步调用,不 stream |

### 工程实现

- `orchestrator/llm/_internal/anthropic_client.py` Claude
- `orchestrator/llm/_internal/qwen_client.py` Qwen via DashScope OpenAI 兼容接口
- `orchestrator/llm/_internal/dispatch.py` 按 model 前缀分发
- model 由 `role.yaml` `model_policy.preferred` 配置

加新 provider:在 `dispatch.py` 注册前缀即可。

---

## 总结

Phase 0C PoC 框架完成。**任一 PoC 失败,架构不变**——
通过 STATE_MACHINE / STORAGE_BACKEND / LANGFUSE_PUBLIC_KEY 环境变量
可以独立切换每个组件,fallback 路径已写在代码里。

待 docker compose 实际起来后,补完 PoC #1 的 kill+recover + PoC #2 的实测部分。
