# V1 依赖清单

> **文档定位**:V1 工具栈 + 版本约束 + 各工具关键验证点
>
> **不是**:完整 API 文档(直接查官方)
>
> **真相源**:pyproject.toml + uv.lock(代码层面),本文档是设计层
>
> **配套文档**:autonomous-agent-system-design.md v2.2 Part IV

---

## 核心工具栈

### 编排层

| 工具 | 版本约束 | 用途 | 必须验证 |
|---|---|---|---|
| **Python** | 3.11+ | 主语言 | - |
| **LangGraph** | 最新稳定版 | 状态机骨架 | Part IV.5 PoC 验证清单(条件边、checkpoint、subgraph) |
| **Pydantic** | 2.x | schema 校验 | role_invocation_protocol 校验通过 |
| **uv** 或 **poetry** | 最新 | 包管理 | lock 文件能复现环境 |

### LLM 调用层

| 工具 | 版本约束 | 用途 | 必须验证 |
|---|---|---|---|
| **anthropic** (SDK) | 最新 | Claude API 调用 | tool use / structured output / 失败重试 |
| **Claude Agent SDK** | 最新 | Phase 2+ 执行器 | 走 Agent SDK credit,不走订阅 |
| **Claude Code CLI** | 最新 | Phase 2+ Developer 执行 | 跑在 worktree 内、能限制 working_dir |

### 数据层

| 工具 | 版本约束 | 用途 | 必须验证 |
|---|---|---|---|
| **PostgreSQL** | 14+ | task state + events + memory | LangGraph checkpointer 兼容 |
| **psycopg** | 3.x | Postgres driver | async 模式工作 |
| **SQLAlchemy** | 2.x | ORM(可选) | 跟 Alembic migration 兼容 |
| **Alembic** | 最新 | schema migration | 多个 phase 增量 migration |

### 观测层

| 工具 | 版本约束 | 用途 | 必须验证 |
|---|---|---|---|
| **Langfuse** (self-hosted) | 最新 | LLM trace + cost | docker-compose 起得来、Anthropic 调用能 trace |
| **structlog** | 最新 | 结构化日志 | JSON 输出,Phase 0B 用 |

### Git 层

| 工具 | 版本约束 | 用途 | 必须验证 |
|---|---|---|---|
| **Git** | 2.30+ (worktree 完整支持) | 任务隔离 | worktree create/remove 工作 |
| **GitPython** | 最新 | Git Python 封装(可选) | 不强依赖,可以直接调 git CLI |
| **GitHub CLI** (gh) | 最新 | PR 自动化 | gh pr create 可用 |
| **gitleaks** | 最新 | secret 扫描 | 能检测 .env 类敏感文件 |

### 项目工具(per-project,不强制)

| 工具 | 用途 |
|---|---|
| Node.js / pnpm / yarn | JS 项目 |
| Go | Go 项目 |
| pytest | Python 项目测试 |
| (项目自身的 CI 工具) | test / lint / build |

---

## 部署层

| 工具 | 用途 | 必须验证 |
|---|---|---|
| **Docker** + **docker-compose** | Phase 0C+ 起 Postgres + Langfuse | 单机能跑 |

---

## V1 不引入的工具(防 scope creep)

| 不引入的 | 理由 | 谁可能想加 → 不要加 |
|---|---|---|
| **LangChain** | 用 LangGraph 直接,不需要 LangChain 抽象层 | "标配" → 不需要 |
| **CrewAI / AutoGen** | 跟 v2.0 范式冲突(它们是固定角色) | "multi-agent 框架" → 不要 |
| **Vector DB** (Pinecone / Weaviate / Qdrant) | V1 memory 用 Postgres + SQL FTS,V2 才考虑 pgvector | "RAG 标配" → V1 不要 |
| **Kubernetes** | 单人项目过度工程 | "生产标准" → 不要 |
| **Inngest / Temporal** | LangGraph 已经是 workflow engine | "任务队列" → 已有 |
| **mem0 / Letta** | V1 自建简单 memory schema 够用 | "memory framework" → V1 不要 |
| **Hermes** | Hermes 是单 agent 框架,不是 multi-agent | "自演化" → 不引入 |
| **MLflow / Weights & Biases** | 我们用 Langfuse,不需要再加 | "experiment tracking" → 重复 |
| **Sentry / Datadog** | 单人项目过度,Langfuse + 飞书够了 | "error tracking" → 不要 |
| **Redis** | Postgres 已够 V1 用 | "缓存" → V1 不要,V2 评估 |

> **判断原则**:如果一个工具的角色已经被现有工具覆盖,**不加**。引入新工具的代价(学习 + 集成 + 维护)远高于"它能再优化 10%"的价值。

---

## V2 可能评估的(不在 V1 范围)

| 工具 | 用途 | V2 评估时间 |
|---|---|---|
| pgvector | 记忆向量检索 | 记忆条目 ≥ 几千时 |
| Docker / microVM sandbox | executor 安全隔离 | 任务接触敏感数据时 |
| Redis | 任务队列缓存 | V1 LangGraph queue 跑不动时 |
| 跨模型 LLM (GPT / Gemini) | reviewer panel | V1 单 LLM reviewer 跑稳后 |

---

## 工具文档查阅原则

```text
不在本文档列文档地址。理由:
  - URL 容易失效,3 个月后链接死了
  - 维护索引成本高于直接 google
  - 官方文档总在更新,索引会过时

需要查文档时:
  google "<tool> <topic>" 或者直接去官方文档站
  
官方文档主入口(记不住时):
  - LangGraph: langchain-ai.github.io/langgraph
  - Anthropic SDK: docs.anthropic.com
  - Langfuse: langfuse.com/docs
  - 其他工具:都是 <tool-name>.com/docs 或 GitHub README
```

---

## 版本锁定策略

```text
V1 阶段:
  - pyproject.toml 写主版本约束(如 langgraph >= 0.2)
  - uv.lock / poetry.lock 锁具体版本
  - 不主动升级(除非有安全 patch 或必需功能)
  
V1 升级时机:
  - 当前版本有 bug 阻塞工作
  - 新版本有明确需要的功能
  - 半年没升级,做一次例行升级
  
V1 不做:
  ❌ dependabot 自动 PR
  ❌ 每周升级
  ❌ pre-release / beta 版本
```

---

## PoC 验证清单(主文档 Part IV.5 已有)

每个工具的"必须验证"项汇总在主文档 Part IV.5,Phase 0C 启动前**必须全部跑通**,结论写到 `docs/poc-results.md`。

关键验证:

```text
1. LangGraph:
   - conditional_edges 能实现 DISPATCH 循环
   - Postgres checkpointer 能持久化 + 恢复
   - Subgraph 支持(子任务并行,V1.5+)
   - 整体 LLM 调用走 Anthropic SDK 没问题

2. Postgres + Langfuse:
   - docker-compose 起来不冲突
   - Langfuse 能 trace Anthropic 调用
   - Postgres 性能足够(每天 3 任务下基本没问题)

3. Claude Code CLI:
   - 跑在 Git worktree 内
   - 能限制 working_dir
   - 输出能解析(stdout / artifact)
   - 走 Agent SDK credit(不消耗订阅)

4. gitleaks:
   - .env 类文件能检测
   - 项目主流语言(Python/Go/JS)的 secret pattern 都识别
```

如果 PoC 失败,fallback 见主文档 Part IV.5(自写状态机替代 LangGraph 等)。

---

## 元数据

- 版本:v1.0
- 创建:2026-05-25
- 配套主文档:autonomous-agent-system-design.md v2.2 Part IV
- 维护:工具版本约束变化时,pyproject.toml 是真相源,本文档只在重大变化(加/删工具)时更新
