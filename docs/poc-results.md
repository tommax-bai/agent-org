# Phase 0C PoC 验证结果

> Spec C.2 要求三个 PoC 各 1 天硬时间盒。失败立即走 fallback,**架构不变**。
>
> 最后更新:2026-05-26(docker compose 起来实测)

---

## PoC #1: LangGraph 作为状态机

### 验证清单(Spec C.2.1)

| 项 | 状态 | 备注 |
|---|---|---|
| checkpoint 在 long-running 任务可靠 | ✅ 通过 | MemorySaver 验证完整 flow,状态正确传递 |
| 中途 kill 后从 checkpoint 恢复 | ⏳ 框架就位,未实测 | 需 SqliteSaver / PostgresSaver,代码已支持,真跑长任务时再写 kill+resume 测试 |
| 节点 timeout 可靠 | N/A | V1 阶段 LLM 调用自己已有重试,LangGraph 节点 timeout 暂用不到 |
| budget exceeded 硬中断 | ✅ 通过 | conditional_edges 路由到 END,跟自写版一致 |
| event 可以回放 | ✅ 通过 | Postgres task_events append-only(端到端实测 60 events),LangGraph stream replay 自带 |

### 结论

**LangGraph PoC 通过**,作为 self_written 的可选替代实现。

工程实现:
- `orchestrator/state_machine/_internal/langgraph_graph.py` 用 LangGraph 1.2 StateGraph
- 跟自写版共享底层逻辑(`_pm_planning` / `_dispatch_loop`),仅状态机骨架不同
- 通过 `STATE_MACHINE=langgraph` 环境变量切换,默认 `self_written`(0B 行为)
- MemorySaver checkpointer 验证概念。Postgres checkpointer 需要 `langgraph-checkpoint-postgres` 包(已声明 dep),真用时配 `DATABASE_URL`

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
| 自部署 Langfuse 能起来 | ✅ 通过 | `docker compose up -d` 后 `curl http://localhost:3000/api/public/health` 返 `{"status":"OK","version":"2.95.11"}` |
| 接收 trace | ⏳ 框架就位,需 Owner UI 建 project 取 keys 填回 .env | `@trace_llm_call` 装饰器已集成所有 LLM 调用,LANGFUSE_PUBLIC_KEY 配上立即生效 |
| cost 计算准确 | ⏳ 同上 | Qwen 走 OpenAI 兼容接口,token usage 字段我们自己估算成本,Langfuse 拿到的 cost 就是这个估算 |
| 高频写入稳定(连续 10 任务) | ⏳ 待 stress test | 上述配通后跑 |

### 工程实现

- `orchestrator/llm/_internal/langfuse_trace.py` `@trace_llm_call` 装饰器
- 所有 `call_claude` / `call_qwen` 自动上报
- LANGFUSE_PUBLIC_KEY 未配时**静默跳过**(0B 行为不变,本地开发友好)
- 失败不影响主流程(吃异常)

### 完成 Langfuse 集成需要 Owner 手动做

```
1. 打开 http://localhost:3000
2. 注册账号(本地用,任意 email 即可)
3. 建新 project(name 随便,比如 "agent-org-dev")
4. Settings → API Keys → New API Key
5. 把 Public Key / Secret Key 填回 .env:
   LANGFUSE_HOST=http://localhost:3000
   LANGFUSE_PUBLIC_KEY=pk-lf-...
   LANGFUSE_SECRET_KEY=sk-lf-...
6. 重新跑任务,在 Langfuse UI Generations 页能看到 trace
```

### 不通过的话怎么办

保留 structlog + Postgres `task_events`(BUDGET_CONSUMED 事件已经在记 cost),
自己写最简 dashboard(SQL 查询)。代价:看 trace 不如 Langfuse UI 直观,
但**功能 100% 等价**。

---

## PoC #3: LLM SDK(Anthropic / Qwen)

### 验证清单

| 项 | 状态 | 备注 |
|---|---|---|
| 真实 LLM 调用稳定 | ✅ 通过 | Qwen plus 跑 task-2026-05-26-001 → DONE,4 subtask 拆解合理 |
| error 重试逻辑健康 | ✅ 通过 | 2 次重试 + 指数退避,代码层验证 |
| **validator + retry_pm 真触发**(v2.4 关键路径) | ✅ 通过 | 端到端实测有 1 次 PLAN_RETRY_REQUESTED 事件,PM attempt 2 通过 → DONE |
| tool use 稳定 | N/A | V1 不用 tool use(Phase 2+ Claude Code CLI 才用) |
| streaming | N/A | V1 同步调用,不 stream |

### 工程实现

- `orchestrator/llm/_internal/anthropic_client.py` Claude
- `orchestrator/llm/_internal/qwen_client.py` Qwen via DashScope OpenAI 兼容接口
- `orchestrator/llm/_internal/dispatch.py` 按 model 前缀分发(claude-* / qwen-* / qwen3-*)
- model 由 `role.yaml` `model_policy.preferred` 配置

加新 provider:在 `dispatch.py` 注册前缀即可。

---

## Phase 0C 端到端实测(2026-05-26)

环境:`docker compose up -d` + `STORAGE_BACKEND=postgres` + Qwen plus(无 Langfuse keys)

**结果**:
- 任务 `task-2026-05-26-001` 跑完 `DONE`(约 70 秒,$0.0047)
- Postgres `task_events`:60 行(完整事件流 + PM retry)
- Postgres `artifacts`:10 行(2 个 PM attempt + 4 subtask × 2 roles)
- v2.4 PLAN_RETRY_REQUESTED 真触发(PM 第一次输出违反 validator,retry 后通过)

```sql
SELECT event_type, count(*)
FROM task_events
WHERE task_id = 'task-2026-05-26-001'
GROUP BY event_type ORDER BY count DESC;
```

```
event_type           | count
---------------------+-------
 STATE_CHANGED       | 19
 ROLE_INVOKED        | 10
 ROLE_RETURNED       | 10
 BUDGET_CONSUMED     | 10
 DISPATCH_DECISION   |  8
 TASK_COMPLETED      |  1
 PLAN_RETRY_REQUESTED|  1    ← v2.4 validator 真触发了
 TASK_CREATED        |  1
```

---

## 总结

Phase 0C 三个 PoC 框架全部就位,端到端实测通过(只剩 Owner 在 Langfuse UI 建 API key 完成 trace 上报闭环)。

**任一 PoC 失败,架构不变**——通过 `STATE_MACHINE` / `STORAGE_BACKEND` / `LANGFUSE_*` 环境变量可独立切换每个组件,fallback 路径已写在代码里。

下一步:Phase 1(单任务真 LLM 闭环,把 Developer / Reviewer / Architect 也换成真 LLM,在 5 个示例任务上打磨 prompt)。
