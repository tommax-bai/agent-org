# Autonomous Multi-Agent 研发系统 — 完整文档集索引

> 当前版本:**v2.4**(Phase 0A 开工前的设计收紧)
>
> 最后更新:2026-05-26
>
> 14 次修订(12 次 Owner+Claude + 2 次 codex review)累积下来的完整设计文档集。

---

## 🎯 快速开始

如果你是 Owner 本人,只想知道**现在该做什么**:

```
1. 读 INDEX.md(这份)— 5 分钟,知道有哪些文档、用途是什么
2. 读 key-design-summary.md(1500 字速览)— 5 分钟,建立全局认知
3. 读主文档 v2.4 头部 + 12 条宪法 — 15 分钟,核心精神
4. 开工 Phase 0A — 看 Spec 文档 Part A
```

如果你是第三方 reviewer:

```
1. 读 codex-review-brief.md — 知道 review 任务范围
2. 按 brief 第 2.1 节推荐顺序读文档
```

---

## 📂 文档分类

### A. 核心设计三件套(必读 — 任何时候)

```
📘 autonomous-agent-system-design.md   v2.4   主设计文档(长期总纲)
📕 phase-0-1-execution-spec.md         v2.4   开工施工图(Phase 0A/0B/0C/1)
📗 design-history.md                   v2.4   修订历史档案(14 次修订)
```

#### 📘 主设计文档(v2.4)

**用途**:长期参考 / 架构总纲 / "为什么这么设计"

**结构**:
- Part I:项目定位
- Part II:8 个能力域(A 任务理解 / B 角色管理 / C 流程编排 / D 角色调用 / E 长期记忆 / F 质量与仲裁 / G 成本配额 / H 数据沉淀)
- **Part III:12 条系统宪法**(核心)
- Part IV:工具栈与架构选型(含 v2.3 新增"模块边界保护"小节)
- Part V:V1 分阶段实施路线(Phase 0A → 0B → 0C → 1 → 2 → 3 → 4A → 4B → 5)
- Part V.5:State/Event/Artifact/Memory 分层
- Part VI:记忆机制实现层
- Part VII:V1 完成后的演进路径
- Part VIII:Owner 工作量与系统边界

#### 📕 开工施工图(v2.4)

**用途**:Phase 0A/0B/0C/1 具体怎么做

**结构**:
- Part A:Phase 0A — 文件骨架(2-3 天)
- Part B:Phase 0B — 最小 runtime(2-3 天)
- Part C:Phase 0C — 基础设施替换(2-3 天)
- Part D:Phase 1 — 单任务 LLM 闭环(1 周)
- Part E:跨阶段约定
- Part F:FAQ
- Part G:开工 checklist

#### 📗 修订历史档案(v2.4)

**用途**:决策追溯 / "为什么不做 X"清单 / 元层教训

**结构**:
- Part I:修订快速概览(13 次修订表)
- Part II:压力测试方法论(4+1 问 / 业界标配陷阱 / 混合方案陷阱 / 列工具菜单陷阱 / 流量小≠系统小)
- Part III:详细修订日志(v1.0 → v2.3 每次的起因、修订、原因)
- Part IV:**被否决的设计清单**(查 "为什么不做 X" 用这里)

---

### B. 部署运维文档(Phase 0C 前看)

```
📋 deployment-decision.md              v1.1   部署架构决策
📋 dependencies.md                     v1.0   工具栈版本约束
📋 coding-subagent-prompt.md           v0.2   开发期 Claude subagent prompt
📋 ops-subagent-prompt.md              v0.2   运维期 Claude subagent prompt
```

#### 📋 deployment-decision.md (v1.1)

**用途**:V1 部署架构决策(阿里云 + bandwagon 代理)

**关键内容**:
- 部署方案对比表(本地/NAS/VPS/阿里云/k8s)
- 本项目实际方案(阿里云国内 + bandwagon 代理)
- 各 Phase 部署演进
- 数据备份策略
- **运维方式 — Claude subagent 分工**
- 决策记录
- 开工前 checklist

#### 📋 dependencies.md (v1.0)

**用途**:工具栈版本约束 + PoC 验证点 + V1 不引入的工具

**关键内容**:
- 5 大工具栈分组(编排/LLM/数据/观测/Git)
- V1 不引入的工具清单(防 scope creep)
- pyproject.toml 是真相源,本文档是设计层

#### 📋 coding-subagent-prompt.md (v0.2)

**用途**:开发期 Claude.ai Project 的 system prompt

**关键内容**:
- 5 大严格遵守的原则(含 **v2.3 模块边界纪律**)
- agent-org 系统背景
- 13 个"业界标配陷阱"清单
- 阶段性指南(Phase 0A-5)
- Context Files 上传清单

**Phase 0A 开工就可以用**。

#### 📋 ops-subagent-prompt.md (v0.2)

**用途**:运维期 Claude.ai Project 的 system prompt

**关键内容**:
- 5 大职责(故障诊断/报告/配置建议/升级/应急)
- agent-org 故障模式表
- 输出风格规范([只读]/[可逆]/[危险] 标记)
- 绝不做的事
- 演化路径(V1 → V2)

**Phase 0C 部署后才开始用**。

---

### C. Codex Review 材料(可选 — 给 reviewer 用)

```
📄 codex-review-brief.md               review 任务说明书
📄 key-design-summary.md               1500 字速览
📄 codex-review-submission-guide.md    给 Owner 看的操作说明
```

**用途**:让 codex / 别的 AI / 别的人 review v2.3 设计

**使用方式**:见 codex-review-submission-guide.md

> 注:这些材料是 v2.1 版本时准备的,但思路和结构对 v2.3 仍然适用。如果做新一轮 review,需要更新 brief 里的版本引用。

---

### D. 历史快照(可忽略)

```
📜 agent-system-design-what.md         早期版本快照
📜 memory-system-implementation.md     早期版本快照
```

**用途**:历史考古,不主动看。

如果某天想知道"早期是怎么想 memory 设计的",可以翻 `memory-system-implementation.md`。

---

## 📊 14 次修订全景

```
v1.0   初稿                              整合多份资料
v1.1   codex review #1(外部)            工具假设、Phase 拆分、PoC 验证门
v1.2   宪法第 2 条                       signals 机制
v1.4   H/B5/F1 + 重叠消除                子能力 38→32
v1.5   通信原则表述                      代码约定 vs 权限系统
v1.6   并发模型粒度                      任务级而非项目级
v1.7   severity 判定                     可执行的判定标准
v2.0   范式升级(架构级重构)             Orchestrator-Worker
v2.1   角色创建工程实践                  meta_prompts 启动门槛工具
v2.2   一致性压平 + codex review #2       12 条宪法 + dispatch_policy + validator
v2.3   模块边界保护                      modular monolith + _internal/ + import-linter
v2.4   Phase 0A 开工前设计收紧            删 autofix / role_sequence / 角色配置方案 Y / artifact attempt
```

---

## 🗂️ 文档关系图

```
                ┌──────────────────────────────────────┐
                │  主设计文档 (autonomous-agent-...)    │
                │  v2.3 长期总纲                        │
                │                                       │
                │  - 12 条宪法                          │
                │  - 8 能力域                           │
                │  - 5 phase 路线                       │
                │  - 模块边界保护(v2.3)                │
                └────────────┬─────────────────────────┘
                             │ 派生
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
   │ Phase 0-1 Spec   │ │ design-history│ │ key-design-    │
   │ v2.3             │ │ v2.3          │ │ summary       │
   │                  │ │               │ │ (1500 字)      │
   │ 开工施工图        │ │ 修订历史 +    │ │                │
   │                  │ │ 已否决清单    │ │                │
   └──────────────────┘ └──────────────┘ └────────────────┘
                             ▲
                             │ 引用
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
   ┌──────────────────┐ ┌──────────────┐ ┌────────────────┐
   │ deployment-      │ │ dependencies  │ │ codex-review-  │
   │ decision v1.1    │ │ v1.0          │ │ brief          │
   │                  │ │               │ │                │
   │ 阿里云方案 +     │ │ 工具栈约束    │ │ review 任务说明 │
   │ subagent 分工    │ │               │ │                │
   └────────┬─────────┘ └──────────────┘ └────────────────┘
            │
            │ 落地为
            ▼
   ┌──────────────────────────────────────┐
   │ 两个 Claude subagent prompt           │
   │                                       │
   │ - coding-subagent-prompt v0.2         │
   │   (开发期,Phase 0A 用)                │
   │                                       │
   │ - ops-subagent-prompt v0.2            │
   │   (运维期,Phase 0C 后用)              │
   └──────────────────────────────────────┘
```

---

## 🎯 Phase 0A 完整启动 checklist

按这个顺序做事:

### Day 1:基础设施 + 配置

```
[ ] 创建 agent-org 私有 Git 仓库
[ ] 写 .gitignore(.env / runs/ / tasks/active|done|failed/ 等)
[ ] 写 pyproject.toml(声明 Python 3.11+ / langgraph / pydantic / import-linter 等)
[ ] 写 README.md(简单)
[ ] 拷贝 12 条宪法到 constitution.md(从主文档 Part III,v2.4 第 12 条删 autofix)
[ ] 整理 vocabulary.md(从主文档 D 域,含 v2.4 role_sequence / must_escalate_to_owner / attempt)
[ ] 写 docs/role_prompt_structure.md(说明 6 段标准结构)
[ ] 写 docs/golden_dataset_format.md(说明 case 格式)
[ ] 写 docs/module_boundaries.md(v2.3 新增 - 说明 _internal/ 约定)
[ ] 写 importlinter.cfg(v2.3 新增 - 从 Spec A.2.5 抄)
[ ] 写 docs/decisions/2026-05-26-no-autofix-in-validators.md(v2.4 ADR Q1)
[ ] 写 docs/decisions/2026-05-26-all-roles-owner-configured.md(v2.4 ADR 方案 Y)
[ ] 写 docs/decisions/2026-05-26-artifact-attempt-versioning.md(v2.4 ADR Q4)
```

### Day 2:目录骨架 + meta_prompts

```
[ ] 建 orchestrator/ 子模块骨架(每个模块 __init__.py + _internal/)
    orchestrator/
      _runtime/__init__.py
      state_machine/{__init__.py, _internal/__init__.py}
      dispatcher/{__init__.py, _internal/__init__.py}
      roles/{__init__.py, _internal/__init__.py}
      llm/{__init__.py, _internal/__init__.py}
      memory/{__init__.py, _internal/__init__.py}
      event_log/{__init__.py, _internal/__init__.py}
      artifact/{__init__.py, _internal/__init__.py}
      budget/{__init__.py, _internal/__init__.py}
      escalation/{__init__.py, _internal/__init__.py}
      _shared/__init__.py

[ ] 建 examples/role_templates/_template/ 通用模板(v2.4 方案 Y)
[ ] 建 examples/role_templates/{pm,developer,reviewer,architect}/ 参考实现
[ ] (不再创建 Claude.ai Project — v2.4 决定先不建 subagent,Phase 1 后期再评估)
[ ] 写 meta_prompts/generate_role_prompt.md
[ ] 写 meta_prompts/generate_golden_dataset.md
[ ] 写 scripts/generate_role_prompt.py
[ ] 用 meta_prompts 生成 examples/role_templates/pm/ 的 system_prompt.md 第一版
    (含 role_sequence 结构说明 + v2.4 5 类 must_escalate 触发条件)
[ ] 写 PM 的 5 个 golden_dataset case
```

### Day 3:其他角色 + 配置 + 校验

```
[ ] 同样流程生成 examples/role_templates/{developer,reviewer}/ 的 system_prompt + golden_dataset
[ ] (可选)生成 examples/role_templates/architect/ 的 system_prompt
[ ] 写 schemas/ 各 schema 文件(v2.4)
    - task.schema.json
    - role.schema.json (含 is_orchestrator: boolean)
    - project.schema.json (含约束:恰好一个 is_orchestrator: true)
    - dispatch_policy.schema.json
    - role_invocation.schema.json (artifact 加 attempt 字段)
    - pm_dispatch_plan.schema.json (用 role_sequence 结构)
    - artifact_content/code.schema.json
    - artifact_content/design.schema.json
    - artifact_content/review.schema.json (含 must_escalate_to_owner + escalation_reason)
    - artifact_content/dispatch_plan.schema.json
    - artifact_content/analysis.schema.json
    - event.schema.json (加 PLAN_RETRY_REQUESTED / ATTEMPT_LIMIT_REACHED;删 PLAN_AUTOFIXED)
[ ] 写 projects/example-api/project.yaml(含 roles 列表 + 恰好一个 is_orchestrator: true)
[ ] 写 projects/example-api/dispatch_policy.yaml(含 mandatory_role_rules / pm_deviation_policy)
[ ] 从 examples/role_templates/ 拷贝 pm/developer/reviewer 到 projects/example-api/roles/
[ ] 写 tasks/inbox/task-2026-05-XX-001.yaml(示例任务)
[ ] 跑 jsonschema 校验所有 yaml
[ ] 跑 lint-imports(空规则应该过)
[ ] CI 跑通(GitHub Actions 简单 workflow)
[ ] git commit + push
[ ] ✅ Phase 0A 完成
```

---

## 📌 关键决策快速查

| 决策 | 结论 | 版本 |
|---|---|---|
| 范式 | Orchestrator-Worker(动态角色) | v2.0 |
| 状态机 | PM_PLANNING + DISPATCH 循环 | v2.2 |
| 调度 | PM raw plan → validator → normalized plan | v2.2 |
| 角色配置 | Owner 配,不固定数量;framework 唯一约束 is_orchestrator: true | v2.0 / v2.4 |
| 规则强制 | dispatch_policy.yaml mandatory_role_rules | v2.2 |
| Signal 紧急升级 | immediate_escalate_required boolean | v2.2 |
| 架构形态 | modular monolith | v2.3 |
| 模块边界保护 | _internal/ + __init__.py + import-linter | v2.3 |
| **Validator 失败处理** | **只 retry 或 escalate,不 autofix(宪法第 12 条 v2.4 修订)** | v2.4 |
| **PM 角色顺序** | **role_sequence(step + role_id 结构),单一事实源** | v2.4 |
| **Reviewer 一票否决字段** | **must_escalate_to_owner + escalation_reason** | v2.4 |
| **重试产物处理** | **追加 attempt,不覆盖;同 (subtask, role) 上限 2 次** | v2.4 |
| **Phase 0B mock 边界** | **只 PM 真 LLM,其他角色 mock** | v2.4 |
| 部署目标 | 阿里云国内 ECS + bandwagon 代理 | v1.1 deploy |
| 运维方式 | Claude subagent 分工(coding + ops) | v1.1 deploy |
| Git 仓库 | 单仓 monorepo,内部严格模块化 | v2.3 |
| V1 不做 | self-evolution / A/B 灰度 / 跨模型 panel / k8s | 见 history Part IV |

---

## ⚙️ 元数据

- 索引版本:v1.1(同步主文档 v2.4)
- 创建:2026-05-25
- 维护:每次主文档大版本修订后,更新版本表 + 关键决策表
- 阅读策略:**保留这份在仓库根目录,任何时候迷路就回来看**
