# agent-org

Autonomous Multi-Agent 研发系统(V1 设计 v2.4)。

Owner 派任务后,系统自主调度多个 LLM 角色(PM 编排 → Architect/Developer/Reviewer 等执行)完成任务,Owner 不在 review loop 里(但持续改进系统)。

**不是** SaaS 产品,不是团队工具。**纯 Owner 个人杠杆放大工具**。

---

## 快速开始

读 `docs/INDEX.md`(5 分钟知道有哪些文档),然后:

- 想知道是什么 / 为什么 → `docs/key-design-summary.md`(1500 字速览)
- 想知道开工怎么做 → `docs/phase-0-1-execution-spec.md`
- 想知道某个设计的理由 → `docs/design-history.md`
- 想知道协作纪律 → `CLAUDE.md`

---

## 核心数字

| | |
|---|---|
| Owner | 1 人 |
| 每天任务密度 | 3 个 |
| V1 周期 | 6-8 周 |
| 单任务预算硬上限 | $20 |

## 工具栈

```
Python 3.11+      uv 包管理
LangGraph         状态机骨架(0C+)
Anthropic SDK     Claude API
Postgres 14+      state + memory + events(0C+)
Langfuse          observability(0C+)
Git worktree      任务物理隔离(Phase 2+)
Pydantic          schema 校验
structlog         日志
import-linter     模块边界强制
```

## 当前阶段

Phase 0A:文件骨架(2-3 天)。

完整路线:0A → 0B(jsonl runtime)→ 0C(接 Postgres + Langfuse)→ 1(单任务真 LLM 闭环)→ 2(worktree)→ 3(质量门)→ 4(项目记忆)→ 5(多任务并行)。

---

## 文档结构

```
agent-org/
├── README.md                    本文件
├── CLAUDE.md                    协作纪律(给 AI 看)
├── constitution.md              12 条宪法(从主文档抽)
├── pyproject.toml
├── importlinter.cfg             模块边界规则
├── docs/                        设计文档(真相源)
│   ├── INDEX.md
│   ├── autonomous-agent-system-design.md
│   ├── phase-0-1-execution-spec.md
│   ├── design-history.md
│   ├── key-design-summary.md
│   ├── deployment-decision.md
│   ├── dependencies.md
│   ├── role_prompt_structure.md
│   ├── golden_dataset_format.md
│   ├── module_boundaries.md
│   ├── decisions/               ADR(每次重要决策)
│   └── operations/              运维 / 开发期 AI 助手 prompt
├── orchestrator/                Python 主进程(0B 开始填)
├── examples/role_templates/     角色参考模板(Owner 拷贝起步)
├── projects/                    用户项目实例(每个项目有自己的 roles/)
├── tasks/                       任务文件(inbox / active / done / failed)
├── runs/                        运行时输出(不进 git)
├── schemas/                     JSON Schema(任务 / 角色 / 产物 / 事件)
├── meta_prompts/                LLM 辅助生成 prompt 的工具
└── scripts/                     一次性脚本
```
