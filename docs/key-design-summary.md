# Autonomous Multi-Agent 研发系统 - 关键设计速览

> 这是一份**1500 字以内**的速览,让 reviewer 不用读完全部 5000+ 行就能建立基本认知。
>
> 配套完整文档:
> - autonomous-agent-system-design.md (主文档 v2.4)
> - phase-0-1-execution-spec.md (Spec v2.4)
> - design-history.md (历史 v2.4)

---

## 是什么

一个**单人开发者**用的 Autonomous Multi-Agent 研发系统。Owner 派任务后,系统自主调度多个 LLM 角色完成任务,Owner 不在 review loop 里(但持续改进系统)。

不是 SaaS 产品,不是团队工具。**纯 Owner 个人杠杆放大工具**。

## 核心数字

- Owner:1 人
- 每天任务密度:3 个
- V1 周期:6-8 周
- 单任务预算硬上限:$20

## 核心架构(v2.0+:动态角色 / Orchestrator-Worker)

```
Owner 派任务
   ↓
PM (任务编排者)
   - 业务拆解(任务 → 业务子目标)
   - 决定每个子目标调用哪些角色
   - 不做技术决策、不写代码、不审查
   ↓
调度者(纯确定性代码,LangGraph 状态机)
   - PM_PLANNING + DISPATCH 循环
   - 按 PM 决定派活给角色
   ↓
角色们(Owner 配置,任意数量)
   - Architect: 系统设计(可选)
   - Developer: 代码实现
   - Reviewer: 产物审查
   - 也可以加 Security_Reviewer / Tester / DBA 等
   ↓
回到 DISPATCH(角色返回后,看下一个该调谁)
   ↓
DONE 或 ESCALATED_TO_OWNER
```

## 12 条宪法(精简版 v2.4)

```
1.  任务间并行(worktree 物理隔离),任务内串行(角色顺序)
2.  角色不直接调用,但可在输出里发 signals,调度者读 signals 决定
3.  项目之间完全隔离
4.  PM 是编排者,调度者是执行者(Orchestrator-Worker)
5.  角色由 Owner 配置,不固定数量(v2.4 落实:framework 不预设,is_orchestrator 唯一硬约束)
6.  质量来自结构化评估 + 硬护栏(不是冗余对抗)
7.  硬护栏在基础设施层强制,不靠 LLM 判断
8.  "更新 agent" 完全是 Owner 决定
9.  所有决策可解释、可追溯
10. 失败和介入沉淀为数据,辅助 Owner 改进(不自动改自己)
11. Owner 不在 loop 里 review,但始终在 loop 里改进系统
12. LLM 输出 + 确定性兜底:兜底只 retry 或 escalate,不替 LLM 补漏(v2.4 修订:删 autofix)
```

## 8 个能力域(32 个子能力)

| 域 | 名称 | 关键 |
|---|---|---|
| A | 任务理解 + 业务拆解 + 角色调度 | PM 输出 business_breakdown + role_sequence(step+role_id,v2.4) |
| B | 角色管理 | Owner 配置,role_groups 模板,B5 质量门 |
| C | 流程编排(动态调度) | PM_PLANNING + DISPATCH 循环 |
| D | 角色调用协议 + 信息流 | role_invocation_protocol,signals |
| E | 长期记忆 | 仅 1 个核心子能力(E3 项目级记忆) |
| F | 质量与仲裁 | 单 LLM Reviewer + 结构化 rubric + 硬护栏 |
| G | 成本与配额 | 任务级预算硬上限 |
| H | 数据沉淀与 Owner 改进辅助 | 3 个子能力,纯数据收集 |

## 工具栈

```
LangGraph         (状态机骨架 + checkpoint,需 PoC 验证)
Claude Agent SDK  (角色 LLM 调用)
Claude Code CLI   (Phase 2+ 才用,Developer 真改代码)
Postgres          (state + memory + queue)
Langfuse          (自托管 observability)
Git worktree      (任务物理隔离)
Pydantic          (schema 校验)
structlog         (日志)
gitleaks          (secret 扫描)
GitHub CLI        (PR 自动化)
```

## V1 路线

| Phase | 时长 | 目标 | 关键约束 |
|---|---|---|---|
| 0A | 2-3 天 | 文件骨架(无任何 runtime) | 纯目录 + yaml + schema |
| 0B | 2-3 天 | 最小 runtime(jsonl 文件) | 不接 Postgres |
| 0C | 2-3 天 | 基础设施替换(Postgres + Langfuse) | 前提:PoC 验证门通过 |
| 1 | 1 周 | 单任务 LLM 闭环 | DISPATCH 循环跑通 |
| 2 | 1-2 周 | Git worktree | 真改代码 |
| 3 | 1-2 周 | 质量门 + PR_READY | 不 auto-merge |
| 4 | 1 周 | 项目记忆(DB→MD 单向) | 不做双向 |
| 5 | 1 周 | 多任务并行 | worktree 隔离 |

## 11 次修订的核心叙事

**前 7 次都在精简**:删虚高功能(Hermes 全栈引入、H 域 self-evolution、B5 灰度 A/B、F1 跨模型 panel、6 层防死循环)+ 表述精准化(控制权 / 并发粒度 / severity 判定)+ 重叠消除(子能力 38→32)。

**第 8-11 次是架构演化**:
- v1.6: 并发模型从项目级改任务级
- v1.7: severity 模糊副词改可执行规则
- v2.0: **范式升级**——固定角色 → 动态角色(Orchestrator-Worker)
- v2.1: 角色创建工程实践(meta_prompts 启动门槛工具)
- v2.2: 一致性压平 + dispatch_policy + 12 条宪法
- v2.3: 模块边界保护(modular monolith)
- v2.4: Phase 0A 开工前设计收紧(删 autofix / role_sequence / 角色配置方案 Y / artifact attempt)

## 已经被否决的设计(详见 design-history.md Part IV)

```
❌ Hermes 全栈引入
❌ 角色严格中转通信(改为 signals)
❌ H 域 self-evolution
❌ B5 灰度 A/B 测试
❌ F1 跨模型 3-reviewer panel
❌ Tier 1/2/3 分级自治
❌ 6 层防死循环护栏
❌ 固定 4 角色范式(v2.0 改)
❌ 固定状态机流程(v2.0 改)
❌ A3 强制 Architect 复核(v2.0 改)
❌ 项目级 advisory lock(v1.6 改)
```

## 反复出现的设计偏差(给 reviewer)

Claude(写主文档的 AI)被 Owner 反复抓到的模式:

> 倾向于用"业界标准 / 生产标配 / 研究表明"这类术语**包装未经验证的设计选择**。

7 次被 Owner 反问后修正。**reviewer 看到任何"业界标配"的措辞,请保持警惕**。

## 关键先决条件(不要质疑)

- 不引入 Hermes / CrewAI / AutoGen 等框架
- 用 LangGraph + Postgres
- Git worktree 物理隔离
- V1 不 auto-merge(Owner 手动 merge)
- 不做 self-evolution / A/B / 跨模型 panel(详细原因见 history.md)

---

> 速览结束。如需深入,请按 codex-review-brief.md 第 2.1 节推荐顺序读完整文档。
