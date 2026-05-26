# Autonomous Multi-Agent 研发系统 - 完整设计文档

> **文档版本**:v2.4(Phase 0A 开工前的设计收紧)
>
> **文档定位**:**长期总纲 / Architecture Reference**
>
> 本文档回答"系统长什么样"和"为什么这么设计",**不直接作为开工清单使用**。
>
> 开工执行请参考配套的分阶段 Execution Spec(见下方索引)。

## v2.4 修订简介(2026-05-26)

Phase 0A 开工前,Owner 跟 Claude 把 Spec 没收死的 5 个开放问题敲死,并捎带把
v2.0 没改干净的"固定角色残留"也清掉。

**核心修订**:

```text
1. 宪法第 12 条:删 autofix 档,validator 只 retry 或 escalate
   - 理由:autofix 让 LLM 失败模式被掩盖,Owner 看不见 → 系统不进化
   - 兜底只 retry(LLM 可能改对)或 escalate(只有 Owner 能改)

2. dispatch_plan validator:同步删 autofix,违反类型按 RETRY_PM / FATAL 分流
   - 漏 mandatory role / 删 mandatory role / role_id 拼错 → RETRY_PM
   - 引用不存在的角色 / 依赖成环 → FATAL escalate

3. PM 输出契约:required_roles 改为 role_sequence
   - 用 [{step: N, role_id: X}, ...] 结构,list 位置无语义
   - dispatcher 按 step 排序,不读 list 位置
   - 单一事实源,LLM 不可能忽略顺序

4. Reviewer artifact:security_or_data_loss_risk 改名 must_escalate_to_owner
   - 字段名描述效果(必须 escalate),不描述类型
   - 加 escalation_reason 字段强制 Reviewer 写原因
   - schema 描述里列五类触发条件(安全/数据/合规/稳定性/不可逆架构变更)

5. artifact 版本:重试不覆盖,追加 attempt 字段
   - 同 (subtask, role) attempt 上限 2 次,第 3 次强制 escalate
   - 满足宪法第 9 条可追溯,为 Phase 4 记忆系统留数据

6. 角色配置(方案 Y):彻底落实第 5 条宪法
   - 所有角色(包括 PM)都是 Owner 配置,framework 不预设
   - 删除 required: true / false,改用 is_orchestrator(恰好一个)
   - examples/role_templates/ 提供起步模板,Owner 拷贝改
   - 同步删除 D 域"V1 内置的"措辞残留(v2.0 改干净)

7. Phase 0B mock 边界明确:只 PM 真 LLM,其他 mock
```

**新增元层教训**(进 design-history Part II):

```text
多层保护 / 防御性设计 / 冗余兜底,大概率是设计本身有问题
  - 通常根因:数据结构没拆干净 / 边界不清 / 责任分配错位
  - 修方案的方向是合并到单一事实源,不是堆更多层
  - 校验/格式合法性不算"层",那是基本卫生
```

## v2.3 修订简介(2026-05-25)

v2.2 完成"一致性压平"后,Owner 关于"工程实施"层面提出新关切:

1. **架构形态**:agent-org 该不该拆微服务?
2. **模块边界**:AI 迭代下,如何保证 modular monolith 不腐烂?

v2.3 加入"模块边界保护"小节(Part IV 末尾)。

**核心决策**:

```text
1. 架构形态:modular monolith(物理单体,逻辑严格模块化)
   - 不拆微服务(单人项目过度工程)
   - 但内部严格模块边界(对抗 AI 迭代下的耦合腐烂)

2. 模块边界保护最小集(V1):
   - _internal/ + __init__.py(显式 public API)← 基础,最重要
   - coding-subagent-prompt 加"模块边界纪律"段
   - import-linter 强制 enforcement
   
3. 不做的(V1 阶段):
   - 完整 Protocol/ABC 体系(V1.5 视情况)
   - 架构测试(linter 已覆盖)
   - pre-commit hook(CI 已覆盖)
```

详见 Part IV 末尾"模块边界保护"段。

## v2.2 修订简介(2026-05-25)

v2.1 完成后,Owner 找 codex 做了独立 review。codex 发现 v2.0 范式升级时**没改干净**——主架构是动态角色,但 V1 路线/Phase 0B/部分状态机仍残留固定角色描述。同时提出了 dispatch_plan validator、artifact 子 schema、状态分层等结构性补充。

v2.2 一次性整合 codex 8 条建议 + Claude/Owner 二次审视发现的 4 个盲区补充:

```text
P0 修订:
  1. 全文消除固定角色流程(Architect 不再出现在状态机骨架)
  2. 新增 dispatch_plan validator(确定性校验 + 三级处理 autofix/retry/fatal)
  3. 新增 dispatch_policy.yaml(mandatory_role_rules + pm_deviation_policy)
  4. signal schema 改 immediate_escalate_required(替代不可靠的 risk_class+keyword)
  5. validator 修改透明执行,记 PLAN_AUTOFIXED 事件
  6. 新增第 12 条宪法:LLM 输出 + 确定性兜底

P1 修订:
  7. 4 个核心角色 artifact 子 schema(PM / Developer / Reviewer / Architect)
  8. 新增 State/Event/Artifact/Memory 分层(Part V.5)
  9. Phase 4 拆为 4A(可用记忆)/ 4B(记忆治理)
  10. worktree 表述改为"工程隔离不是安全沙箱"+ Phase 2 加最小保护

P2 修订:
  11. 术语和版本统一
```

详细修订日志见 design-history.md v2.2。

## v2.1 增量(2026-05-24)

v2.0 完成范式升级(动态角色)后,Owner 提出**加角色的工程实践缺失**——人工写 system_prompt 和 golden dataset 门槛太高。

v2.1 在主文档 B 域加上**轻量工程实践**:

- roles/_template/ 模板目录(cp -r 起步)
- system_prompt 6 段标准结构
- golden dataset 格式约定
- meta_prompts/ LLM 辅助生成(启动门槛工具,不全自动)
- 配套 CI 模板

详细见主文档 B 域"角色创建的工程实践"段。

## v2.0 范式升级简介

v1.x 系列都是"固定角色范式"(固定 4 个角色:PM/Architect/Developer/Reviewer,固定状态机流程)。

**v2.0 升级为"动态角色范式"(Orchestrator-Worker 模式)**:

```text
PM = 任务编排者
  - 业务拆解(任务 → 业务子目标)
  - 角色调度(决定每个子任务调哪些角色)
  - 不做技术决策、不写代码、不审查

角色 = Owner 配置的能力单元
  - role.yaml + system_prompt.md
  - 任意数量(项目可有 1 个,也可有 10 个)
  - Architect / Developer / Reviewer / Security_Reviewer / Tester / DBA / ...
  - 按需配置

调度者 = 按 PM 决定派活
  - 不再写死"PM→Architect→Developer→Reviewer"流程
  - 状态机 = PM_PLANNING + DISPATCH 循环
```

**关键收益**:
- 跟现实世界一致(PM 业务,Architect 系统,各司其职)
- 跟业界 best practice 一致(Orchestrator-Worker)
- V1 架构 = 终局架构(不需要后期重写)
- 角色可扩展(加 role.yaml,不改架构)
- 任务复杂度自适应(简单任务少调几个角色)

详细修订日志见 design-history.md v1.8。

## 配套文档索引

```text
当前文档    完整设计文档 v2.4            (长期总纲,你正在读)
                ↓
开工         Phase 0-1 Execution Spec v2.4 (开工施工图,已同步)
                ↓
后续         Phase 2/3/4/5 Spec           (每个 phase 完成后归档)

附属         design-history.md            (设计修订历史档案,v2.4 已同步)
```

**协同原则**:

- 主文档定义"为什么"和"是什么"
- Execution Spec 定义"这周写哪几个文件"
- 任何 Spec 跟主文档冲突时,以最新讨论结论为准,然后更新两份文档保持一致
- 每个 phase 完成时,对应 Spec 归档,作为 V1 → V2 对照参考

## 关于设计修订历史

本文档**只展示当前的设计**,不包含修订理由、原版 vs 新版对比。

如果你想知道:

- 为什么某个设计是这样,而不是另一种?
- 为什么某个"业界标配"没在系统里?
- 某个推迟到 V2 的设计当时是怎么想的?

→ **请翻 `design-history.md`**(修订历史档案)

那份文档专门回答"为什么不是另一种设计"。它在你**做决策时**才有用,**写代码时**用不上。

---

## 目录

- [Part I:项目定位](#part-i项目定位)
- [Part II:8 个能力域(做什么)](#part-ii8-个能力域做什么)
- [Part III:12 条系统宪法](#part-iii12-条系统宪法)
- [Part IV:工具栈与架构选型](#part-iv工具栈与架构选型)
- [Part V:V1 分阶段实施路线](#part-vv1-分阶段实施路线)
- [Part VI:记忆机制实现层](#part-vi记忆机制实现层)
- [Part VII:V1 完成后的演进路径](#part-viiv1-完成后的演进路径)
- [Part VIII:Owner 工作量与系统边界](#part-viiiowner-工作量与系统边界)
- [Part IX:已知未解决问题](#part-ix已知未解决问题)
- [附录:讨论历程与关键决策点](#附录讨论历程与关键决策点)

---

# Part I:项目定位

## 一句话

**一个 autonomous multi-agent 软件开发组织**,由 Owner 定义角色、调度者协调执行、PM 担任智能顾问、各角色协作完成长期项目;Owner 不在 loop 里干活,只在系统集体搞不定时介入,介入方式是改进 agent。

## 核心画像

| 维度 | 取值 |
|---|---|
| 服务对象 | Owner 一人(内部开发团队的极小版本) |
| 部署环境 | 自有机房 / 内网 |
| 代码敏感度 | 外部公开代码 / 个人项目(低敏感) |
| 任务量 | 当前每天 3 个,目标是借此撬动产能,挑项目就能跑 |
| 自动化野心 | 越自动越好,Owner 只在 agent 集体失败时介入 |
| 错误容忍 | 可以接受 agent 犯错,但守住数据丢失 / 严重安全问题底线 |
| 维护模式 | Owner 单人 + AI 工具辅助维护 |
| 节奏 | 全套打磨,不赶时间 |

## 设计哲学

**关键认知**:这不是"AI 辅助工具",而是"自治的数字组织"。

- 工具的目标是**省人的时间**,组织的目标是**撬动人的产能**
- 工具的设计止于"用得顺手",组织的设计要支持"长期演进"
- 工具的失败是 bug,组织的失败是治理问题

整套系统是为 Owner 的"工作方式重塑"服务的:从"执行者"变成"组织造物主"。

---

# Part II:8 个能力域(做什么)

## 总览

```
A. 任务理解与拆解   ← 系统入口质量
B. 角色管理         ← 调度者的"员工花名册"
C. 流程编排(动态)   ← 系统主循环
D. 角色间通信       ← 消息高速公路
E. 长期记忆         ← 系统的"灵魂"
F. 质量与仲裁       ← 没人 review 时的质量底线
G. 成本与配额       ← 边界控制(不是省钱,是安全)
H. 自我改进         ← 系统的飞轮
```

## 域之间的依赖关系

```
              ┌──────────────────┐
              │  H (自我改进)     │ ◄── 元层,观察并改进所有
              └────────▲─────────┘
                       │ 反哺
   ┌───────────────────┼───────────────────┐
   ▼                   │                   ▼
┌──────┐    ┌─────────────────────┐    ┌──────┐
│  A   │───▶│  C (流程编排核心)    │◄───│  B   │
│拆解  │    │  调度者主循环        │    │角色  │
└──────┘    └──────┬──────────────┘    └──────┘
   │               │                       │
   │               ▼                       │
   │        ┌──────────┐                   │
   │        │   D      │                   │
   │        │ 消息中转  │                   │
   │        └──────┬───┘                   │
   │               ▼                       │
   │        ┌──────────┐                   │
   │        │   F      │                   │
   │        │ 质量仲裁  │                   │
   │        └──────────┘                   │
   ▼                                       ▼
┌─────────────────────────────────────────────┐
│  E (长期记忆 - 系统的灵魂)                    │
│  所有域的读写源                               │
└─────────────────────────────────────────────┘
       横切: G (成本) - 监控所有域的资源消耗
```

## 关键架构概念

### 调度者 vs PM(必须分清)

| 概念 | 性质 | 是否思考 | 作用 |
|---|---|---|---|
| **调度者(Orchestrator)** | 系统骨架,确定性代码 | 不思考 | 状态机、消息中转、强制隔离、失败兜底 |
| **PM 角色** | 一个 agent,LLM 驱动 | 思考 | 任务理解、拆解、智能建议 |

类比:**调度者 = Linux 内核;PM = Jira 这个应用**。两者完全不同性质,不要混淆。

调度者跑 PM,就像 Linux 跑 Jira。PM 给建议,调度者执行。PM 失败了,调度者还在;调度者挂了,PM 也跑不起来。

### 并发模型

- **任务间**:默认并行(每个 task 独立 worktree + 独立 task_id + 独立 LLM context)
- **任务内**:子任务按依赖顺序执行;每个子任务内的角色按 PM 调度顺序串行
- **唯一隔离硬约束**:同一 worktree 同时只跑一个 task(自动满足,每个 task 创独立 worktree)
- **项目边界**:每个 Git 仓库 = 一个项目(monorepo 算一个)
- **项目隔离**:不同项目的 PM 互不可见,记忆完全隔离

### 通信原则

**核心**:区分"调用"和"通信"。

- **禁止的(硬约束)**:
  - 角色在自己的 LLM 调用里直接触发另一个角色执行
  - 角色直接修改另一个角色的产出
  - 角色凭意志绕过调度者发起协作
  
- **允许的**:
  - 角色在自己的**输出**里引用其他角色的产出
  - 角色在输出里提出 signals(疑问 / 关注 / 建议 / 协作请求)
  - 调度者读 signals 后决定下一步(可能是调另一个角色,也可能是 escalate)

**底层模型**:

所有角色读写同一份 task state(LangGraph 的 graph state)。"通信"是信息在 state 里流动,不是 RPC 调用。

**调度者的"控制"是代码架构约定,不是权限系统**:

- 所有 state 修改通过 node 的 return 值,由 LangGraph reducer 合并(角色不直接 mutate state object)
- 角色看到什么 input 由调度者的 build_context_pack 决定(角色拿不到完整 state,只拿到调度者给的部分)
- 不同 task 的 state 由 task_id + LangGraph checkpoint 自动隔离

V1 阶段**不做强安全沙箱**,只做**工程隔离**(v2.2 修正表述):

底层默认假设:

- Owner 单人使用
- 代码低敏感度
- executor 可信
- 任务运行在内网机器
- 风险可接受

实际"隔离"机制:

- LLM 是无状态 API,看不到任何没传给它的数据(真隔离)
- Postgres 的 task state 只有 orchestrator 主进程能连(进程级隔离)
- Claude Code subprocess 在 worktree 里跑(**工程隔离,非安全沙箱**)
- task_id + LangGraph checkpoint 隔离不同任务的 state(逻辑隔离)

> **重要澄清(v2.2)**:Git worktree 是 **Git 工作目录隔离,不是 OS sandbox**。executor subprocess 跟 orchestrator 在同一用户权限下运行,理论上可以 cd .. 访问 worktree 外的文件。
>
> V1 接受这个风险(内部使用、低敏感度)。Phase 2+ 加最小 executor 保护(working_dir 限定、环境变量白名单、不传 orchestrator DB URL)。Docker / microVM sandbox 推迟到 V2 评估。

- 全局消息格式词汇表统一(D1)

> "为什么不严格中转?为什么不需要文件权限?worktree 是不是安全沙箱?" → 见 design-history.md

---

## 能力域 A:任务理解 + 业务拆解 + 角色调度

**目标**:接收任务 → 产出业务拆解 + 角色调度决策 + 完整上下文包

> **v2.0 重大修订**:A 域职责重新定义。PM 不再做"系统拆解",改为**业务拆解 + 角色调度**(Orchestrator-Worker 范式)。原 A3"强制 Architect 复核"被废除——Architect 不是 reviewer,是一种**Owner 可配置的角色**。

### 5 个子能力

| 能力 | 说明 |
|---|---|
| A1 任务接收与解析 | 多入口归一 + 结构化解析 + 三层假设防御(记录+暴露+学习),不主动反问 Owner |
| A2 任务复杂度评估 | 多维度复杂度画像,动态修正(角色可提议升级) |
| **A3 业务拆解 + 角色调度** | 把任务拆成业务子目标,**决定每个子目标调用哪些角色**(基于 project.yaml 的 role_groups 模板,可加减) |
| A4 任务依赖识别 | 带类型的依赖图(强 / 弱 / 信息依赖),变更影响分析 |
| A5 任务上下文构建 | 角色定向的 context pack,相关性排序,摘要 / 全文 / 节选三档 |

### 关键决策

- A 域所有 LLM 能力由 **PM 角色**承担,**PM 是任务编排者**
- **PM 不做系统设计、不写代码、不审查产物**——这些工作派给具体角色
- PM 决定每个业务子目标调用哪些角色
- 角色调度的兜底:Owner 在 project.yaml 配置 `role_groups`(任务类型 → 默认角色组),PM 用模板作为起点,可提议加减(走 signal,严重时通知 Owner)

### A3 业务拆解 + 角色调度的具体逻辑

```yaml
PM 看到任务:
  1. 业务拆解:把任务拆成 1-N 个业务子目标
     例:"加用户登录功能"
        → [邮箱登录, 第三方登录, 找回密码]
  
  2. 任务类型识别:每个子目标属于什么类型
     例:邮箱登录 → simple_feature
        第三方登录 → integration_feature
  
  3. 角色调度决策:基于 project.yaml 模板 + 任务特殊性
     例:邮箱登录 (simple_feature)
        → 默认模板:[developer, reviewer]
        → PM 判断:不需要 architect (常规 CRUD)
        → final role_sequence: [{step:1, developer}, {step:2, reviewer}]
     
     例:第三方登录 (integration_feature)
        → 默认模板:[architect, developer, reviewer]
        → PM 判断:涉及安全,加 security_reviewer
        → final role_sequence: [
            {step:1, architect},
            {step:2, developer},
            {step:3, security_reviewer},
            {step:4, reviewer}
          ]
        → 因为加了非默认角色,发 signal(severity: medium)通知 Owner
  
  4. 顺序与并行:
     - 同一子目标内的角色顺序由 role_sequence.step 决定(单一事实源)
     - 不同子目标之间能否并行(取决于依赖)
```

> **v2.4 修订**:`required_roles` 改为 `role_sequence` 结构,顺序由每个 item 的
> `step` 字段决定,list 位置无语义。理由:plain list 顺序对 LLM 是"隐式"的,
> 容易忽略;显式 step 字段让 LLM 不可能不思考顺序。dispatcher 按 step 排序读,
> 跟 list 位置无关。

### 关键产出契约

```yaml
task_understanding_output:
  task_id: ...
  pm_output:
    parsed_intent: {...}
    assumptions: [...]
    complexity_profile: {...}
    
    # v2.0 新增 / v2.4 改 role_sequence:业务拆解
    business_breakdown:
      - subtask_id: subtask-001
        description: "邮箱登录"
        task_type: simple_feature
        success_criteria: [...]
        role_sequence:
          - step: 1
            role_id: developer
          - step: 2
            role_id: reviewer
        dependencies: []
      - subtask_id: subtask-002
        description: "第三方登录"
        task_type: integration_feature
        success_criteria: [...]
        role_sequence:
          - step: 1
            role_id: architect
          - step: 2
            role_id: developer
          - step: 3
            role_id: security_reviewer
          - step: 4
            role_id: reviewer
        dependencies: [subtask-001]
    
    # v2.0 新增:角色调度的额外说明
    role_dispatch_notes:
      - subtask: subtask-002
        deviation_from_template: "加了 security_reviewer(默认模板没有)"
        reason: "OAuth 涉及第三方,需要安全审查"
    
    context_packs_per_role: {...}
    pm_confidence: 0.85
    signals_to_other_roles: [...]
  
  final_status: ready_for_execution
```

> **关键变化**:不再有 `architect_review` 字段。Architect 如果被 PM 调用,就在它的角色 turn 做系统设计,不是单独的 review 步骤。

### Dispatch Plan Validator(v2.2 新增 / v2.4 简化为两级)

**关键**:**PM 输出的 business_breakdown 不是直接执行计划**。调度者必须先经过 deterministic validator,产出 `normalized_dispatch_plan` 后才能进入 DISPATCH。

```text
PM raw plan
   ↓
validate_dispatch_plan() ← 确定性代码,不调 LLM
   ↓ PASS → normalized_dispatch_plan → DISPATCH 执行
   ↓ RETRY_PM → PM 重做(上限 1 次)
   ↓ FATAL → ESCALATED_TO_OWNER
```

**为什么需要 validator**:

PM 是 LLM,可能输出:

```text
1. 漏 mandatory role(security 任务漏 security_reviewer / 涉及代码漏 reviewer)
2. 主动删 mandatory role(违反 dispatch_policy 的 cannot_remove_mandatory_roles)
3. 引用不存在的 role_id
4. role_id 拼错(developr / reviwer)
5. 循环依赖
6. task_type 不存在于 role_groups
7. role_sequence step 不连续 / 不从 1 开始
8. role_sequence 为空 / 同 subtask 内 role_id 重复
```

validator 是**确定性代码护栏**,防止 PM 错误导致任务失败或安全风险。

**核心校验规则**:

```python
def validate_dispatch_plan(pm_plan, project_config, dispatch_policy):
    """
    Deterministic validation only.
    No LLM call.
    No autofix — validator 不替 LLM 补漏(宪法第 12 条 v2.4)。
    Returns: ValidationResult(action=PASS|RETRY_PM|FATAL, ...)
    """
    checks = [
        "all role_id must exist in project.yaml roles",
        "each subtask.role_sequence must not be empty",
        "each subtask.role_sequence step must be 1..N continuous, no duplicates",
        "same role_id must not appear twice in one subtask",
        "task_type must exist in role_groups",
        "dependencies must reference existing subtasks",
        "dependencies must be acyclic",
        "mandatory_role_rules must be satisfied (from dispatch_policy)",
        "cannot_remove_mandatory_roles must not be violated",
        "code-changing task must include developer-type role",
        "PR-producing task must include reviewer-type role",
        "estimated subtask budget must not exceed task budget",
    ]
    return validation_result
```

**Validator 失败的两级处理**(v2.4:删除原 autofix 档):

| 类别 | 触发条件 | 处理 |
|---|---|---|
| **RETRY_PM** | LLM 可能改对的错误 | 带 violation_detail 让 PM 重新生成(上限 1 次,可配置) |
| **FATAL** | 只有 Owner 能改的错误,或 retry 后仍失败 | ESCALATED_TO_OWNER |

**RETRY_PM 的具体场景**:

```yaml
retry_pm:
  - "漏 mandatory role(role_groups 模板里没有,PM 也没加)" → PM 重做,把 missing role 注入 context
  - "主动删 mandatory role(违反 dispatch_policy)" → PM 重做,告诉它这个不能删
  - "role_id 拼错(Levenshtein 距离 ≤ 2)" → PM 重做,给正确角色名清单
  - "task_type 不存在于 role_groups" → PM 重做,给可选 task_type 清单
  - "subtask description 跟 task 完全不符" → PM 重做,重新理解任务
  - "role_sequence step 不连续 / 同 role_id 重复" → PM 重做,提示格式要求
```

**FATAL 的场景**:

```yaml
fatal:
  - "引用了 project.yaml 不存在的 role_id"(角色根本没配,只有 Owner 能修)
  - "依赖图成环"(PM 业务理解有问题,retry 概率低)
  - retry_pm 后仍然失败(连续两次同类错误)
  - validator 自身遇到配置错误(dispatch_policy 矛盾 / role_groups 写错)
  → ESCALATED_TO_OWNER
```

**为什么不做 autofix**(宪法第 12 条 v2.4):

```text
autofix("validator 直接补全漏掉的角色")在 v2.2-v2.3 一度被允许,v2.4 删除。理由:
  1. 让 LLM 失败模式被掩盖,Owner 看不见漏角色的模式 → 改不动 PM prompt
  2. 模糊 Orchestrator-Worker 边界(validator 干了 PM 该干的事)
  3. autofix 凭模板/policy 补角色,这俩变更时 autofix 可能补错
代价:每任务多 ~$0.3-0.5 的 retry 成本。换长期可改进性,这笔账划算。
```

**Validator 透明度**:

每次 RETRY_PM 或 FATAL 都记到 event log(`PLAN_RETRY_REQUESTED` / `PLAN_VALIDATION_FATAL`)。Owner 通过 dashboard 看模式,决定是否改 PM prompt 或 dispatch_policy。

**Validator 的优先级**:

```text
mandatory_role_rules
  > protected_paths rule
  > role_groups template (默认起点)
  > PM discretionary changes (有限自由)
```

详细 dispatch_policy 设计见 B 域。

---

## 能力域 B:角色管理

**目标**:调度者眼里"角色"这个概念怎么存在、怎么变化、怎么被使用

> **v2.0 修订**:角色不再固定数量。Owner 可以配置任意数量的角色,只要每个角色实现统一的 role_invocation_protocol(见 D 域)。

### 5 个子能力

| 能力 | 说明 |
|---|---|
| B1 角色注册 | Git 仓库 + role.yaml + 校验 CI + 热加载 + version pinning;**任意数量,Owner 自由配置** |
| **B2 角色能力建模与表现追踪** | 声明 + 自报 + 历史表现度量 + 反哺 PM 的角色调度决策 |
| B3 角色状态跟踪 | 实例级 + 角色级状态,可观察 |
| B4 角色选择 | **PM 在业务拆解时决定调用哪些角色**(基于 project.yaml 的 role_groups 模板) |
| **B5 角色质量门** | Git PR + golden dataset 回归测试 + LLM-as-judge diff 报告 |

### 角色配置(v2.4 方案 Y:framework 不预设角色)

**关键原则**:**所有角色都是 Owner 配置,framework 不预设任何角色**(落实第 5 条宪法)。
唯一的 framework 约束是:project.yaml 里必须有恰好一个角色标 `is_orchestrator: true`
(担任 PM 职责,出 dispatch_plan,状态机入口指向它)。

```yaml
# project.yaml(Owner 自己写)
roles:
  - role_id: pm
    description: "业务拆解 + 角色调度(任务编排者)"
    is_orchestrator: true   # ← framework 唯一硬约束:恰好一个
  
  - role_id: developer
    description: "代码实现"
  
  - role_id: reviewer
    description: "产物审查 + 质量评估"
  
  - role_id: architect
    description: "系统设计 + 系统任务拆解"
  
  - role_id: security_reviewer
    description: "安全审查(OAuth、加密、密钥相关)"
  
  - role_id: tester
    description: "测试用例设计"
```

**起步路径**:framework 在 `examples/role_templates/` 提供 pm / developer /
reviewer / architect 等参考模板,Owner 启动项目时从 examples 拷贝想要的到
`projects/<project>/roles/`,改名/改 prompt 都行。完全替换/全自定义都行,
只要 project.yaml 里有 is_orchestrator: true 的那个角色实现 dispatch_plan 协议。

**校验**:`is_orchestrator: true` 的角色不止一个或一个都没有 → project.yaml
校验失败,系统拒绝启动。

> **v2.4 修订**:删除 `required: true/false` 概念(本质是 framework 半固定角色,
> 跟第 5 条"Owner 配置不固定数量"自相矛盾)。改用 `is_orchestrator` 标记唯一
> 的 framework 必需点。详见 design-history.md v2.4 修订条目。

### 任务类型 → 默认角色组(role_groups)

```yaml
# project.yaml
role_groups:
  simple_feature:
    description: "简单 CRUD、明确需求"
    roles: [developer, reviewer]
  
  complex_feature:
    description: "涉及多模块、需要系统设计"
    roles: [architect, developer, reviewer]
  
  integration_feature:
    description: "对接第三方服务"
    roles: [architect, developer, security_reviewer, reviewer]
  
  refactor:
    description: "重构、性能优化"
    roles: [architect, developer, tester, reviewer]
  
  bug_fix:
    description: "Bug 修复"
    roles: [developer, reviewer]
```

PM 根据任务类型选择模板,允许提议加减(走 signal,严重时通知 Owner)。

### Dispatch Policy(v2.2 新增 — 强制规则配置)

**关键**:role_groups 是"默认模板",dispatch_policy 是"硬规则"。PM 可以在模板上加减,但**不能违反 dispatch_policy 的 mandatory rules**。

```yaml
# projects/<project>/dispatch_policy.yaml

# 强制角色规则(validator 必须强制执行)
mandatory_role_rules:
  - id: security_sensitive_task
    if_any:
      task_contains:
        # 关键词列表大一点,宁可误报不漏报
        - OAuth
        - SSO
        - token
        - password
        - secret
        - encryption
        - auth
        - login
        - session
        - JWT
        - cookie
        - credential
      paths_match:
        - "auth/**"
        - "security/**"
    require_roles:
      - security_reviewer
  
  - id: data_loss_risk
    if_any:
      task_contains:
        - migration
        - delete data
        - drop table
        - drop column
        - schema change
        - truncate
        - wipe
      paths_match:
        - "db/migrations/**"
        - "schema/**"
    require_roles:
      - architect
      - reviewer
    require_approval_gate: true
  
  - id: protected_paths
    if_any:
      paths_match:
        - ".github/workflows/**"
        - "infra/**"
        - "Dockerfile"
        - "k8s/**"
    require_roles:
      - reviewer
    require_approval_gate: true

# PM 偏离模板的权限
pm_deviation_policy:
  can_add_roles: true
  can_remove_template_roles: true
  cannot_remove_mandatory_roles: true       # 硬规则:mandatory 不能删
  removing_template_role_requires_signal: true
  adding_non_template_role_requires_dispatch_note: true

# 例外清单(Owner 维护,处理 keyword 误报)
exceptions:
  - rule_id: security_sensitive_task
    skip_if_any:
      task_contains:
        - "update docs"
        - "rename"
        - "改文档"
        - "documentation"
    rationale: "文档类任务,即使提到 auth/OAuth 也不需要 security review"
```

**优先级**:

```text
mandatory_role_rules    (硬规则,最高)
  > protected_paths rule
  > role_groups template (默认起点)
  > PM discretionary changes (PM 自由度,最低)
```

**关于 keyword 匹配的认知**:

```text
keyword 列表故意做得大(高 recall),宁可误报不漏报:
  - 误报代价:多调一次 security_reviewer ≈ $0.5
  - 漏报代价:安全/数据丢失风险进入 PR

误报由 Owner 维护例外清单消化。
真实 keyword 漏报的情况,Owner 看 dashboard 后补关键词。
```

### PM 输出的偏离说明(role_dispatch_notes)

PM 如果偏离 role_groups 默认模板,**必须在 role_dispatch_notes 里说明**:

```yaml
role_dispatch_notes:
  - subtask_id: subtask-002
    deviation_type: add_role | remove_role
    role_id: security_reviewer
    reason: "OAuth/token handling requires security review"
    policy_rule_id: security_sensitive_task    # 关联到 mandatory rule(如果是)
```

validator 检查(v2.4:删 autofix,违反走 RETRY_PM):

- 删模板角色 → 必须发 signal(违反则 RETRY_PM)
- 加非模板角色 → 必须在 dispatch_note 写明 reason(违反则 RETRY_PM)
- 违反 mandatory rule(漏 / 删 mandatory)→ RETRY_PM,记 `PLAN_RETRY_REQUESTED` 事件

### 关键决策(v2.0 + v2.2 + v2.4)

- 角色数量 **Owner 决定**(v2.4 落实:framework 不预设任何角色,只要恰好一个 is_orchestrator: true)
- 简单任务可不调用 Architect,复杂任务可调用多个 reviewer
- PM 输出 role_sequence 里的 role_id 必须是 project.yaml 注册过的角色
- **PM 可以偏离模板,但不能违反 mandatory rules**(v2.2)
- **dispatch_policy 是 Owner 控制系统行为的核心配置文件**(v2.2)
- **validator 不替 PM 补漏**(v2.4 第 12 条宪法):违反 mandatory 走 RETRY_PM,不 autofix
- B2 历史表现可让 PM 知道某角色擅长什么任务

### 关于角色质量门(B5)

```yaml
角色质量门:
  trigger: Owner 创建 PR 改 role.yaml 或 system_prompt.md
  
  CI 流程:
    1. 拉对应角色的 golden dataset (5-30 cases)
    2. 用旧版 prompt 跑,记录基线
    3. 用新版 prompt 跑,记录新结果
    4. LLM-as-judge 对比每个 case,输出 diff 报告
    5. 报告附在 PR 上
  
  数据来源:
    - 初始:Owner 手动写 5-10 个 case(或用 meta_prompts 生成,见下)
    - 持续:每次失败任务自动进 golden dataset 候选池
    - Owner 审批进入正式 golden dataset
  
  切换:
    - Binary cutover (不灰度)
    - Version pinning (正在跑的任务用旧版完成)
```

### 角色创建的工程实践(v2.1 新增)

V2.0 范式下,加新角色是 Owner 的常规操作。这一节说明**轻量工程实践**——不做完整脚手架软件,但提供模板 + LLM 辅助生成,降低 Owner 加角色的门槛。

#### 1. roles/_template/ 模板目录

```
roles/
├── _template/                    # 模板目录(不是真实角色,Owner 不直接调用)
│   ├── role.yaml
│   ├── system_prompt.md
│   ├── golden_dataset/
│   │   └── README.md
│   └── README.md
├── pm/
├── developer/
└── reviewer/
```

Owner 加新角色起步:`cp -r roles/_template/ roles/<new_role>/` 然后改。

#### 2. system_prompt.md 6 段标准结构

所有角色的 system_prompt.md 应包含 6 个段落:

```markdown
## 1. 角色定位
（Owner 写:这个角色是干什么的,在系统里的位置）

## 2. 输入约定
（统一模板,引用 D 域 role_invocation_protocol）

## 3. 输出约定
（统一模板,引用 D 域 role_invocation_protocol + 角色 artifact.content 约定）

## 4. Signal severity 判定标准
（统一模板,引用 D 域 severity 判定规则)

## 5. 角色专属能力
（Owner 写:这个角色特有的判断、规则、约束)

## 6. 反模式
（Owner 写:这个角色绝不应该做什么,可选)
```

标准结构的目的:**降低 Owner 写 prompt 的认知负担**——只有第 1、5、6 段需要 Owner 自己想,其他都是模板。

#### 3. golden dataset 格式

```yaml
# roles/<role>/golden_dataset/case_001.yaml
case_id: case_001
description: "典型场景 - 简单 bug fix 任务"

input:
  task_id: example-task-001
  subtask_id: subtask-001
  role_id: developer
  context_pack:
    task_context: {...}
    business_goal: |
      修复 login timeout 问题
    related_artifacts: []

expected_output_traits:
  # LLM-as-judge 用这些 traits 评估输出
  - "应该 verdict=success"
  - "artifact.content.proposed_changes 至少有 1 个 file"
  - "应该提到 ctx.WithTimeout 或类似 API"
  - "不应该改 schema"
  - "应该有测试改动"
```

注意:**不是精确字符串匹配**,而是"特征描述",LLM-as-judge 用这些判断。

#### 4. meta_prompts/ 启动门槛工具(LLM 辅助生成)

人工从零写 system_prompt.md 和 golden dataset 门槛高。提供 meta_prompts/ 帮 Owner 生成"第一版":

```
agent-org/
├── meta_prompts/
│   ├── generate_role_prompt.md          # 用来生成新 role 的 system_prompt 第一版
│   ├── generate_golden_dataset.md       # 用来生成 golden case 第一版
│   └── README.md                         # 怎么用
├── scripts/
│   ├── generate_role_prompt.py           # CLI 包装(简单脚本,30-50 行)
│   └── generate_golden_case.py
```

**工作流**:

```text
Owner 想加 security_reviewer 角色:

1. 跑生成器:
   $ python scripts/generate_role_prompt.py \
       --role-id security_reviewer \
       --description "OAuth、加密、密钥审查" \
       --inherits-from reviewer        # 可选,继承某个已有角色的 prompt 风格

2. 生成器内部:
   - 读 meta_prompts/generate_role_prompt.md(meta prompt)
   - 读 docs/role_prompt_structure.md(6 段标准结构说明)
   - 读 D 域 role_invocation_protocol 文档
   - 调 Claude API
   - 输出 roles/security_reviewer/system_prompt.md 第一版

3. Owner review 生成结果:
   - 第 1、5、6 段:Owner 主要看这里(角色专属内容)
   - 第 2、3、4 段:套模板,基本不用改
   
4. git commit 这版作为 v1 基线

5. 跑 golden dataset 生成:
   $ python scripts/generate_golden_case.py \
       --role-id security_reviewer \
       --num-cases 5

6. Owner review 生成的 case,筛选/修改

7. 后续走 B5 角色质量门:
   - Owner 改 system_prompt.md → PR
   - CI 跑 vN vs vN+1 用 golden dataset
   - LLM-as-judge 输出 diff 报告
   - Owner 看报告 merge
```

**meta_prompts 的定位**:

| 是 | 不是 |
|---|---|
| 启动门槛工具(降低写第一版门槛) | 一键自动化(不能直接进 git) |
| 生成结果必须 Owner review | 全自动 dashboard |
| 写一次 meta prompt,用很多次 | 持续维护的产品功能 |
| ~50 行 Python + 2 个 meta prompt 文件 | 复杂工程 |

**为什么不做更多(不做 CLI 工具 `agent-org new-role`)**:

```text
V1 阶段角色数量预期 < 10,加角色频率不高,过度工程没必要。
等真的频繁加角色(每周 1+)再上更自动化的工具。
```

#### 5. CI 模板

```
agent-org/
├── .github/
│   └── workflows/
│       └── role_regression.yml.template   # 角色质量门 CI 模板
```

新角色创建后,copy 模板,改 role_id 即可工作。

#### 6. V1 阶段不做的事

避免一开始就过度工程:

- ❌ CLI 工具 `agent-org new-role` (V1 用 cp -r 够了)
- ❌ Role dashboard / UI
- ❌ Prompt 版本管理 GUI(用 Git)
- ❌ Golden dataset 自动收集(V1 手动审批)
- ❌ Multi-tenant role 配置

#### 7. 演化路径

```
V1:    模板 + meta_prompts + 手工生成
V1.5:  根据 V1 真实加角色频率 / 痛点,看是否需要 CLI 工具
V2:    考虑 role hub(可分享 / 复用角色配置)
V3+:   多人协作的角色管理
```

---

## 能力域 C:流程编排(动态调度)

**目标**:基于 PM 的角色调度决策,实际跑起来的工作流(无预定义路径)

> **v2.0 修订**:状态机从固定流程(PM→Architect→Developer→Reviewer)改为 **PM_PLANNING + DISPATCH 循环**。Architect 不再是必经步骤,而是 PM 可调用的一种角色。

### 5 个子能力

| 能力 | 说明 |
|---|---|
| C1 下一步决策 | 事件驱动,按 PM 的 role_sequence(step 排序)派活 |
| C2 并行决策 | **任务间并行(worktree 物理隔离),子任务间可并行(按依赖),角色顺序串行** |
| C3 重试决策 | 失败分类 + 反馈式重试 + PM 主导策略 |
| **C4 基于 signals 的流程调整** | D5 signals 在流程层的应用:按 severity 分级。判定标准见 D 域 |
| C5 中止决策 | 四级:角色 turn / 子任务 / 任务 / 项目;自动 + escalate 混合 |

### 核心循环(v2.0)

```text
while task.status != DONE:
  
  1. PM_PLANNING 阶段(任务入口,只跑一次)
     - PM 业务拆解 → business_breakdown
     - PM 决定每个子任务的 role_sequence(含 step + role_id)
     - 输出 dispatch plan
  
  2. DISPATCH 循环
     while 还有未完成的子任务:
       a. 找下一个 ready 的子任务(依赖已完成)
       b. 找该子任务下一个 ready 的角色(前置角色已完成)
       c. 调度该角色:
          - 调度者准备 context_pack
          - 调用角色 LLM(走 role_invocation_protocol)
          - 收到 role output(含 signals)
          - 调度者处理 signals(可能改变下一步)
       d. 子任务所有角色完成 → 子任务 done
       e. 回到 a
  
  3. 所有子任务 done → task done
```

### 状态机示例(LangGraph 实现)

```python
# 不是固定 PM→Architect→Developer→Reviewer
# 而是 PM_PLANNING + DISPATCH 节点 + conditional_edges

graph = StateGraph(TaskState)
graph.add_node("PM_PLANNING", run_pm_planning)
graph.add_node("DISPATCH", dispatch_next_role)
graph.add_node("ROLE_EXECUTING", run_role)
graph.add_node("DONE", finalize_task)
graph.add_node("ESCALATED", notify_owner)

graph.set_entry_point("PM_PLANNING")
graph.add_edge("PM_PLANNING", "DISPATCH")

# DISPATCH 决定下一步去哪里(动态)
graph.add_conditional_edges("DISPATCH", route_after_dispatch, {
    "execute": "ROLE_EXECUTING",
    "done": "DONE",
    "escalate": "ESCALATED"
})

# 角色执行完回到 DISPATCH 决定下一步
graph.add_edge("ROLE_EXECUTING", "DISPATCH")
```

**关键洞察**:这个状态机**不再写死流程**。`route_after_dispatch` 看 task_state.pending_roles,决定调哪个角色或者结束。

### 调度顺序的决定权

```text
PM 在 business_breakdown 输出(v2.4 role_sequence 结构):
  subtask-001:
    role_sequence:
      - step: 1
        role_id: architect
      - step: 2
        role_id: developer
      - step: 3
        role_id: reviewer
  subtask-002:
    role_sequence:
      - step: 1
        role_id: developer
      - step: 2
        role_id: reviewer
    dependencies: [subtask-001]

调度者按 step 排序派活(不看 list 位置):
  1. subtask-001 的 architect (step:1)
  2. subtask-001 的 developer (step:2)
  3. subtask-001 的 reviewer  (step:3 → subtask-001 done)
  4. subtask-002 的 developer (因为 subtask-001 已完成)
  5. subtask-002 的 reviewer  (subtask-002 done)
  
  任务 done
```

如果子任务之间无依赖,**可以并行**(但需要更复杂的 worktree 管理,V1 阶段子任务先串行)。

---

## 能力域 D:角色调用协议 + 信息流

**目标**:统一所有角色的调用方式(input/output schema),让动态角色范式可工作

> **v2.0 修订**:加上 role_invocation_protocol——所有角色(包括 is_orchestrator 的 PM)都是 Owner 配置,遵循同一套调用协议。
>
> v2.4 措辞修正:删除"V1 内置的"残留(那是 v2.0 没改干净的痕迹,跟第 5 条宪法矛盾)。

### 5 个子能力

| 能力 | 说明 |
|---|---|
| D1 消息词汇 | **全局词汇表统一**(Owner 定义角色时必须遵守),自动匹配 |
| D2 上下文裁剪 | 角色契约声明所需 + 相关性排序 + 摘要 / 全文 / 节选三档 |
| D3 产物归档 | 分类存储(代码 / 文档 / 数据) + 唯一 ID + 不可变 + 全保留 |
| D4 多角色协作 | **支持 review_panel + debate_round**,角色发 signals,调度者协调 |
| D5 反馈与 signals 传递 | 结构化反馈 / 疑问 / 协作请求 + 上下文带反馈链 + 反复识别 + 忽略机制 |

### Role Invocation Protocol(v2.0 新增)

所有角色的输入输出格式统一,这样新加角色不需要改架构:

```yaml
# 调度者调用角色的标准 input
role_invocation_input:
  task_id: ...
  subtask_id: ...           # 该角色服务的子任务
  role_id: developer        # 调谁
  
  context_pack:             # 调度者准备的 context
    task_context: {...}     # 任务背景
    business_goal: {...}    # PM 提供的业务目标
    success_criteria: [...]
    related_artifacts: [...]  # 前置角色的产物(如 architect 的设计)
    project_memory: {...}   # 相关项目记忆
    role_specific_data: {}  # 该角色特定的数据
  
  prior_role_signals: [...]  # 之前角色发给当前角色的 signals

# 角色的标准 output
role_invocation_output:
  role_id: developer
  task_id: ...
  subtask_id: ...
  
  verdict: success | needs_changes | escalate
  
  artifact:                  # 角色产生的产物
    type: code | design | review | analysis | ...
    content: {...}
    artifact_id: ...         # 不可变 ID,可被后续角色引用
    attempt: 1               # v2.4:同 (subtask, role) 第几次尝试,从 1 起,上限 2
    superseded_by: null      # v2.4:被哪个新 artifact_id 取代(可选,追溯链)
  
  # 角色对其他角色的反馈
  signals_to_other_roles:
    - target: pm | architect | developer | reviewer | ...
      type: question | concern | suggestion | collaboration_request
      content: 自然语言描述
      severity: low | medium | high  # 见下方判定标准
  
  cost_used:
    llm_tokens: ...
    duration_ms: ...
```

**核心收益**:加任何新角色,Owner 只需要写 role.yaml + system_prompt.md + 遵守这套 protocol。架构不变。

### Core Role Artifact Schemas(v2.2 新增)

`role_invocation_output.artifact.content` 在 v2.0 设计是自由格式(`{...}`)。v2.2 为核心角色定义 artifact.content 子 schema,**让产物可解析、可归档、可生成 PR body**。

**重要**:这些子 schema 只对**核心角色**强制,新加的自定义角色可以先用自由格式,稳定后再加 schema。

#### PM artifact schema(v2.4:role_sequence 结构)

```yaml
artifact:
  type: dispatch_plan
  content:
    parsed_intent: object
    assumptions:
      - id: string
        content: string
        risk: low | medium | high
    business_breakdown:
      - subtask_id: string
        description: string
        task_type: string                # 必须存在于 role_groups
        success_criteria: [string]
        role_sequence:                   # v2.4:替代 required_roles
          - step: int                    # 1..N 连续,validator 强制
            role_id: string              # 必须存在于 project.yaml roles
        dependencies: [subtask_id]
    role_dispatch_notes:
      - subtask_id: string
        deviation_type: add_role | remove_role | template_default
        role_id: string
        reason: string
        policy_rule_id: string           # 关联到 mandatory rule(如果是)
    confidence: 0.0-1.0
```

#### Developer artifact schema

```yaml
artifact:
  type: code_patch
  content:
    summary: string
    changed_files:
      - path: string
        change_type: create | modify | delete
        reason: string
    commands_run:
      - command: string
        exit_code: int
        output_summary: string
    tests_added:
      - path: string
        purpose: string
    tests_run:
      - command: string
        result: pass | fail | skipped
    risks: [string]
    followups: [string]
```

#### Reviewer artifact schema(v2.4:字段重命名 + 加 reason)

```yaml
artifact:
  type: review
  content:
    verdict: approve | request_changes | reject
    must_escalate_to_owner: true | false   # v2.4:替代 security_or_data_loss_risk
    escalation_reason: string              # v2.4:必填(当 must_escalate_to_owner=true)
    correctness_score: 0-10
    design_quality_score: 0-10
    test_coverage: adequate | inadequate | not_applicable
    blocking_issues:
      - file: string
        line: int                  # 可选
        issue: string
        required_fix: string
    non_blocking_issues:
      - issue: string
        suggestion: string
    confidence: 0.0-1.0
```

**Verdict 规则**:

```text
must_escalate_to_owner=true           → verdict=reject (一票否决)
任一 CI 硬护栏失败                      → verdict=reject
correctness_score<7 或 test_coverage=inadequate → verdict=request_changes
其他                                   → verdict=approve
```

**`must_escalate_to_owner` 必须设为 true 的情况**(写进 Reviewer system_prompt,任一条满足即可):

- 安全风险:代码可能泄露 secret / 绕过认证 / 引入注入漏洞
- 数据损失:改动可能导致不可逆数据丢失(drop / 不可逆 migration / 删备份)
- 合规风险:违反明显的法规(GDPR / 个人隐私)
- 生产稳定性:改动核心配置 / 可能引起宕机
- 不可逆的架构变更:违反当初 Architect 的核心设计约定

不确定时设为 true,让 Owner 判断。宁可误报不可漏报。

> **v2.4 重命名理由**:原名 `security_or_data_loss_risk` 描述风险**类型**,
> 但系统真正在乎的是**效果**(必须 escalate)。出现新类别(合规、稳定性等)
> 时,旧名字塞不下。改成 `must_escalate_to_owner` 直接说明效果,触发条件
> 写在 prompt 里。一致性校验:`must_escalate_to_owner=true` 时 verdict 必须
> 是 reject,不一致 → RETRY_LLM(宪法第 12 条 v2.4)。

#### Architect artifact schema

```yaml
artifact:
  type: design
  content:
    decision_summary: string
    proposed_design:
      components:
        - name: string
          responsibility: string
      data_flow: string
      key_decisions:
        - decision: string
          rationale: string
          alternatives_considered: [string]
    affected_modules: [string]
    technical_choices:
      - choice: string
        rationale: string
    suggested_implementation_steps: [string]
    risks: [string]
    confidence: 0.0-1.0
```

#### Security Reviewer artifact schema(可选,推荐)

```yaml
artifact:
  type: security_review
  content:
    verdict: approve | request_changes | reject
    security_issues:
      - severity: critical | high | medium | low
        category: auth | injection | secrets | data_loss | crypto | other
        location: string                     # file:line 或 概念位置
        description: string
        recommendation: string
    threat_model_check:
      authentication_changes_reviewed: true | false
      authorization_changes_reviewed: true | false
      data_flow_reviewed: true | false
      secrets_handling_reviewed: true | false
    confidence: 0.0-1.0
```

### 关键决策

- D1 走全局词汇表(严格一致),不靠 LLM 动态转换
- 所有角色遵循 role_invocation_protocol(v2.0)
- 核心角色 artifact.content 有强制 schema(v2.2)
- 新自定义角色 artifact.content 可以先自由格式,稳定后加 schema
- D4 当前支持 review_panel + debate_round 两种模式
- 角色之间不直接 invoke 对方,但可以在输出里发 signals 给彼此
- 调度者读 signals 决定下一步:可能是调另一角色、可能是回炉、可能是 escalate

### 关于 signals 的设计

每个角色的输出 schema 都有 `signals_to_other_roles` 字段(可选):

```yaml
signals_to_other_roles:
  - target: pm | architect | developer | reviewer | <任何 Owner 配置的角色>
    type: question | concern | suggestion | collaboration_request
    content: 自然语言描述
    severity: low | medium | high
    immediate_escalate_required: false           # v2.2 新增,默认 false
    immediate_escalate_reason: "..."             # 当 immediate_escalate_required=true 时必填
```

> **v2.2 修订**:删除原本计划的 `risk_class` 字段(关键词匹配兜底不可靠)。改用 `immediate_escalate_required` boolean——完全交给 LLM 判断,但必须写明理由(可审计)。
>
> 任务级硬护栏由 dispatch_policy 的 mandatory_role_rules 提供(任务一开始就配备专门角色),signal 只处理"任务跑到一半角色发现的紧急风险"。

### Severity 判定标准(写进各角色的 system_prompt)

**默认 medium**,然后看是否触发升级或降级。

**升级到 high(任一满足)**:

- 跟任务 success_criteria 直接冲突
- 检测到 security 或 data_loss 风险
- 跟另一个角色的产出明确矛盾
- 当前流程再继续也是白做

**降级到 low(任一满足)**:

- 只是风格 / 命名 / 注释建议
- 跟当前任务无关的长期想法
- 不影响 success_criteria 的小优化

**其他情况 → medium**

### immediate_escalate_required 判定标准(写进各角色的 system_prompt,v2.2)

**默认 false**。只在以下情况设为 true:

- **不可逆的数据丢失风险**(会删用户数据 / 不可恢复的 migration)
- **安全漏洞**(可被攻击利用、密钥泄露、权限失控)
- **死循环**(角色之间反复矛盾,继续跑也是白做)
- **超出 success_criteria 的爆炸性变化**(任务要做 A,但角色发现做 A 必须做 B/C/D)

**反模式**:

- 不要把"我有疑问"标为 immediate_escalate(用 severity=high 就够了)
- 不要把"设计选择有争议"标为 immediate_escalate(让调度者处理普通 high)
- **immediate_escalate_required=true 时必须填 immediate_escalate_reason**,否则调度者降级为 severity=high 处理

### 调度者对 signal 的处理规则(v2.2)

| Signal | 调度者行为 | Owner 体验 |
|---|---|---|
| **low** | 仅记 events.jsonl,不影响流程 | 看 dashboard 能查到,不打扰 |
| **medium** | 记 events + 写入 pending_concerns,下一个相关角色拿到 context | 看 dashboard 能查到,不主动打扰 |
| **high(普通)** | 立即改变流向,回炉相关角色;累计 ≥ 3 → ESCALATED_TO_OWNER | 单次不打扰,累计触发飞书推送 |
| **immediate_escalate_required=true** | **立即 ESCALATED_TO_OWNER**(不论 severity,不计入 3 次累计) | 立即飞书推送 |

**immediate_escalate 的处理逻辑**:

```python
def process_signal(signal, state):
    # 1. immediate_escalate 优先级最高
    if signal.immediate_escalate_required:
        if not signal.immediate_escalate_reason:
            # 没说理由 → 降级为 high 处理(防 LLM 滥用)
            log_event('IMMEDIATE_ESCALATE_REJECTED', 
                      payload={'reason': 'missing_reason'})
            signal.immediate_escalate_required = False
            signal.severity = 'high'
        else:
            log_event('IMMEDIATE_ESCALATE_TRIGGERED', payload=signal)
            return escalate_immediately()
    
    # 2. 按 severity 处理
    if signal.severity == 'low':
        log_event('SIGNAL_RECEIVED', payload=signal)
        return None
    elif signal.severity == 'medium':
        state.pending_concerns.append(signal)
        log_event('SIGNAL_RECEIVED', payload=signal)
        return None
    else:  # high
        state.high_signal_count += 1
        log_event('SIGNAL_RECEIVED', payload=signal)
        if state.high_signal_count >= 3:
            return escalate_immediately()
        else:
            return reroute_to(signal.target)
```

**滥用防御**:

- Owner 在 Langfuse dashboard 看"过去 7 天 immediate_escalate 触发 N 次,实际合理 M 次"
- 如果 N/M 比例失常,Owner 改对应角色 prompt 收紧判定
- 不在系统里做自动检测(避免过度工程)

### "通知"和"escalate"的边界

C4 子能力提到"小/中/大调整",但**没有独立的判定逻辑**。具体落地是 severity 三级:

| 概念 | 含义 | 触发条件 |
|---|---|---|
| **PM 自主** | 流程在 LangGraph 范围内自然推进 | severity=low / medium 的 signal |
| **通知 Owner** | 信息可查,Owner 主动看才能看到 | 写到 events.jsonl + Langfuse |
| **Escalate Owner** | 主动推飞书,任务停下来等决策 | severity=high 累计 ≥ 3 / 预算耗尽 / 死循环 |

"小/中/大"的判定 = severity 字段的 low / medium / high。**C4 子能力本身不需要独立的"小中大"判定逻辑**。

---

## 能力域 E:长期记忆

**目标**:跨任务的项目级知识沉淀(LLM 无状态 + 项目长期积累知识的调和)

### 1 个核心子能力

| 能力 | 说明 |
|---|---|
| **E3 项目级记忆** | 分层(事实 / 约定 / 历史 / 经验 / 偏好) + 检索 + 鲜度管理 + Curator |

> E 域曾经包含 5 个子能力,经压力测试后收缩为 1 个。具体来龙去脉见 design-history.md。
> 简单说:E1/E2 是基础设施伪装、E4 是"任务相似度自动反哺"幻想、E5 跟 B2 重叠合并了。

### 关键决策

- E3 来源:**三者都要**(手动 + 任务沉淀 + 代码扫描)
- **项目完全隔离**,不做跨项目咨询
- 记忆有人类可读形态(markdown 存 Git)+ 机器可索引形态(SQL + 可选 embedding)

E 域的详细实现在 [Part VI](#part-vi记忆机制实现层) 展开。

---

## 能力域 F:质量与仲裁

**目标**:autonomous 系统在没有人 review 的情况下的质量底线

### 5 个子能力

| 能力 | 说明 |
|---|---|
| **F1 产物评估** | 客观(CI 硬护栏) + 主观(**单 LLM Reviewer + 结构化 rubric**) |
| **F2 分歧仲裁** | 分级:PM 仲裁 → 辩论(引用 D4 debate_round)→ Arbiter(Opus,V2) → 升级 Owner |
| F3 收敛判定 | 信号驱动 + 硬指标兜底 + 质量等级声明 |
| F4 死循环检测 | 4 种模式 + 多种恢复策略 + 数据反哺 |
| F5 升级判定 | 明确触发条件 + 结构化求助 + 反哺机制 + 频率监控 |

### F1 详细设计

```yaml
F1 产物评估:
  
  客观层 (CI 硬护栏, 必过):
    - tests_pass
    - lint_pass / build_pass
    - gitleaks_pass
    - protected_paths_check (三级)
    - diff_size_limit
    任一失败 → REJECT
  
  主观层 (V1 单 LLM Reviewer):
    模型: Claude Sonnet/Opus (单一)
    
    输出结构化 rubric:
      verdict: approve | request_changes | reject
      must_escalate_to_owner: true | false   # v2.4:一票否决
      escalation_reason: string              # v2.4:must_escalate=true 时必填
      correctness: 0-10
      design_quality: 0-10
      test_coverage: adequate | inadequate
      blocking_issues: [...]
      non_blocking_issues: [...]
      signals_to_other_roles: [...]
  
  Verdict 规则:
    - must_escalate_to_owner=true → REJECT (单一硬规则)
    - 任一硬护栏失败 → REJECT
    - correctness < 7 或 test_coverage=inadequate → REQUEST_CHANGES
    - 其他 → APPROVE

V1.5 可选:self-consistency(单模型多采样,温度高)
V2 可选:高风险场景用跨模型,常规场景仍单 LLM
```

> "为什么不做 3-reviewer 跨模型 panel?" → 见 design-history.md

### F2 详细设计

```yaml
F2 分歧仲裁:
  分级处理:
    1. 角色间冲突 → PM 仲裁(常规)
    2. PM 仲裁不决 → 辩论(引用 D4 debate_round 机制实现)
    3. 辩论仍不决 → Arbiter(V2 才做,用 Opus)
    4. 多次失败 → 升级 Owner (F5)
  
  辩论机制:不在 F2 重复定义,见 D4 debate_round
```

### 关键决策

- F1:单 LLM Reviewer + 单一 must_escalate_to_owner 一票否决(v2.4 重命名)
- F2 的辩论机制由 D4 实现,F2 只定义"什么时候用"
- F5 升级请求是**结构化的**:包含分析、根因、备选方案、PM 推荐

### 两条公理

1. 质量来自**结构化评估和硬护栏**
2. 硬护栏(数据丢失 / 安全)在基础设施层强制,不靠 LLM 判断

---

## 能力域 G:成本与配额

**目标**:不是省钱,是**边界控制**(防跑飞 + 成本作为系统健康度信号)

### 4 个子能力

| 能力 | 说明 |
|---|---|
| G1 预算护栏 | 多层级硬上限 + 实时统计 + **PM 可申请重新分配,Owner 同意后释放** |
| G2 成本归因 | 多维度标签 + 任意切片 + **只实时告警**(不要定期报表) |
| G3 异常检测 | 6 种异常类型 + 分级响应 + 自动归因 |
| G4 配额管理 | 资源池定义 + 公平调度 + 跨模型冗余 |

### 预算多层结构

```
per_task_hard_stop:        $100
per_subtask_hard_stop:     $20
per_role_invocation:       $5
per_project_daily:         $1000
per_system_daily:          $3000
```

硬上限**不能被 PM 自动解锁**,只有 Owner 能解。

---

## 能力域 H:数据沉淀与 Owner 改进辅助

**目标**:为 Owner 改进系统提供数据基础。系统**不自动改自己**,所有改进决策权在 Owner。

### 3 个子能力(都是数据收集,不是改进)

| 能力 | 说明 |
|---|---|
| **H1a 失败结构化存档** | 每次失败任务存成 failure record(events + escalation + 根因 + tags) |
| **H1b 失败聚类与复发检测** | 同一类失败 N 天内出现 ≥ M 次 → 告警 Owner(V2 跟 G3 异常检测合并) |
| **H4 Owner 反馈收集** | Owner 飞书回复 / PR 拒绝原因 / 手动改动结构化存(audit log) |

> 黄金测试集(原 H5)已合并到 B5 角色质量门。

> H 域曾经包含"自我改进"相关的多个子能力(H1c / H2 / H3a / H3b)和 Tier 1/2/3 分级自治机制,**经压力测试后全部删除**。
>
> 简单说:2026 年业界数据(包括 Hermes 社区)显示 LLM self-evolution 不成熟,"unobservable learning"是单人维护的灾难。详见 design-history.md。

### 核心原则

- H 域**只沉淀数据**,不自动改系统
- "更新 agent"完全是 Owner 决定
- 系统改进的范式:Owner 看数据 → Owner 改 prompt → 走 B5 角色质量门验证
- V3+ 才重新考虑 self-evolution(等业界数据成熟)

---

# Part III:12 条系统宪法

```
1. 任务间并行,任务内串行
   - 任务间:每个 task 有独立 worktree + 独立 task_id,默认可并行
   - 任务内:子任务按依赖顺序,角色按 PM 调度顺序执行
   - 唯一硬约束:同一 worktree 同时只跑一个 task(自动满足,每个 task 一个 worktree)
   (并发模型的基础)

2. 角色不直接调用对方,但可以在输出里发 signals;所有执行调度由调度者决定
   - 允许:角色输出引用其他角色的产出、提出疑问、给出反馈、请求协作
   - 禁止:角色在自己的执行过程中直接 invoke 另一个角色或修改对方产出
   - 调度者读取 signals,根据规则决定下一步流向
   (隔离与可控的基础)

3. 项目之间完全隔离
   (简单性与安全性)

4. PM 是任务编排者,调度者是执行者
   - PM 做业务拆解 + 角色调度(决定调用哪些角色)
   - PM 不做技术决策、不写代码、不审查
   - 调度者按 PM 决定派活,纯确定性,不做语义判断
   - 各个角色(Architect、Developer、Reviewer 等)做自己专业范围的工作
   (Orchestrator-Worker 范式)

5. 角色由 Owner 配置,不固定数量
   - role.yaml + system_prompt.md 即可注册新角色
   - project.yaml 配置 role_groups 模板(任务类型 → 默认角色组)
   - 角色必须遵守 role_invocation_protocol(见 D 域)
   (角色可扩展)

6. 质量来自结构化评估 + 硬护栏
   - 单 LLM Reviewer + 结构化 rubric + 硬护栏 + golden dataset 回归
   (autonomous 质量保证)

7. 硬护栏在基础设施层强制,不靠 LLM 判断
   (安全底线)

8. "更新 agent" 完全是 Owner 决定
   系统只沉淀数据,所有改进决策权在 Owner
   (控制权归属)

9. 所有决策可解释、可追溯
   (可调试性)

10. 失败和介入沉淀为数据,辅助 Owner 改进
    系统不自动改自己,Owner 看数据改 prompt
    (可观测性)

11. Owner 不在 loop 里 review,但始终在 loop 里改进系统
    (Autonomous != 失控)

12. LLM 输出 + 确定性兜底(v2.4 修订)
    - LLM 输出 = 起点,不是终点
    - 确定性代码(validator / hard guardrails)= 兜底
    - **兜底只能 retry 或 escalate,不能替 LLM 补漏**
    - 理由:
      1. 替 LLM 补漏会让 LLM 失败模式被掩盖,Owner 看不见 → 改不动 prompt → 系统不进化(违反第 10、11 条)
      2. 模糊职责边界(validator 干了 PM 的活,违反第 4 条 Orchestrator-Worker)
      3. 兜底机制本身脆弱,policy/模板变更时可能补错(已否决清单同源问题)
    - retry 必须有硬上限(默认 1 次,可配置),超过即 escalate
    - 兜底机制本身必须可靠;不可靠的兜底(如关键词匹配 signal 内容)反而是噪声
    - 所有 LLM 输出的异常 / retry / escalation 都记到 event log
    (LLM 治理原则)
```

> 宪法 v2.4 修订:第 12 条删 autofix 档(详见 design-history v2.4)。
> 宪法 v2.2 修订:新增第 12 条"LLM 输出 + 确定性兜底"。
> v2.0 重大修订:第 4/5 条体现动态角色范式。
> 第 2/6/8/10 条都经过修订(从更激进的原版收敛到现在)。详细原因见 design-history.md。

> **宪法演化**:v1.0 10 条 → v2.0 11 条(加角色配置)→ v2.2 12 条(加 LLM 治理原则)→ v2.4 第 12 条收紧。

---

# Part IV:工具栈与架构选型

> **重要**:本章节列出的工具选型**全部是当前假设**,需要 Phase 0/1 PoC 验证。
>
> 任何工具如果破坏"确定性调度者"原则,都必须降级为 executor 或替换。
>
> **架构决策 vs 实现选择**:Orchestrator 是架构决策(不可变),LangGraph 是实现选择(可替换)。不能倒过来。

## 整体物理架构

```
┌─────────────────────────────────────────────────────────────────┐
│  一台机器(16 核 64G 内网服务器) + 1 台监控机                       │
│                                                                  │
│  docker-compose 起所有组件:                                       │
│  ┌────────────────────────────────────────────┐                │
│  │ Postgres (+ pgvector V2)                    │                │
│  │ Langfuse (observability,自部署)             │                │
│  │ LangGraph runtime (orchestrator 主进程)     │                │
│  │ Memory Service + Curator                    │                │
│  │ Hermes-as-gateway (仅入口层,可选)            │                │
│  │ Caddy (反向代理 + HTTPS)                     │                │
│  └────────────────────────────────────────────┘                │
│                                                                  │
│  Worker 池(按需 spawn,Git worktree 隔离):                       │
│  ┌────────┐ ┌────────┐ ┌────────┐                               │
│  │ Claude │ │ Codex  │ │ Other  │                               │
│  │ Code   │ │ CLI    │ │ models │                               │
│  └────────┘ └────────┘ └────────┘                               │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
   Git 仓库 (artifact + 配置) + 远程备份
```

**注意**:上图是**目标架构**,Phase 0 不需要全部到位。Phase 0A 只需要文件系统 + Git,Phase 0B 加上 LangGraph 进程,Phase 0C 才接 Postgres 和 Langfuse。

## 核心工具选型表(全部为当前假设)

| 层 | 工具(假设) | 角色 | 验证状态 | 失败后 fallback |
|---|---|---|---|---|
| **编排** | LangGraph | 状态机骨架 | 待 PoC | 自写状态机 |
| **角色执行** | Claude Agent SDK | 角色 LLM 调用 | 待 PoC | 直接调 Anthropic API |
| **代码执行** | Claude Code CLI | Developer 改代码 | 待 PoC | Codex CLI / mock executor |
| **状态存储** | Postgres | 任务状态 + 记忆 + 队列 | 成熟工具 | SQLite(单机降级) |
| **观测** | Langfuse(自部署) | trace + cost + eval | 待 PoC | structlog + events 表 |
| **隔离** | Git worktree | 任务执行环境 | 待 PoC | 独立 clone |
| **入口** | 飞书 SDK 自写 / Hermes gateway | 任务接收 | 待选 | Slack / CLI / Web UI |
| **schema** | Pydantic | 数据校验 | 成熟工具 | dataclass + jsonschema |
| **日志** | structlog | 结构化日志 | 成熟工具 | logging + json |
| **CI** | GitHub Actions | 质量门 | 成熟工具 | 自托管 runner |
| **secret 扫描** | gitleaks | 防 secret 泄露 | 待 PoC(本地 vs CI) | trufflehog |
| **代码扫描** | Semgrep(可选) | 自定义安全规则 | 可延后 | - |
| **PR 操作** | GitHub CLI (gh) | 创建/查/管理 PR | 待 PoC | GitHub API |

## Part IV.5:PoC 验证门(Phase 0/1 必跑)

任何"待 PoC"工具进入主路径前,必须先跑 PoC 验证以下问题。失败则走 fallback。

### LangGraph PoC

```text
1. checkpoint 是否在 long-running 任务里可靠
2. 中途 kill orchestrator 后是否能从 checkpoint 恢复
3. 外部 CLI 进程(Claude Code)的启停控制是否容易
4. 节点 timeout 是否可靠(不靠 LLM 自觉)
5. budget exceeded 能不能硬中断状态机
6. task event 是否能完整回放
```

**通过标准**:1-5 全部为"是"。6 是 nice to have。

**失败 fallback**:退回自写状态机(Python + 简单 state enum + Postgres 持久化)。架构不变,只是实现替换。

### Claude Code PoC

```text
1. -w worktree 指定执行的稳定性(连续 50 次成功率)
2. 输出能不能稳定结构化解析(JSON 模式)
3. 失败时退出码是否明确(0 / 非 0 + 原因码)
4. 长任务(>5 分钟)是否会无声卡死
5. 多个 Claude Code 实例并发是否冲突
```

**通过标准**:1、3 必须为"是"。2 可以靠包装层弥补。

**失败 fallback**:Codex CLI 或 mock executor(Phase 0/1 阶段 mock 即可)。

### Claude Agent SDK PoC

```text
1. 是否适合做 role runner(独立 session 管理)
2. tool use 和 streaming 是否稳定
3. 跟 LangGraph 集成的样板代码量
4. 跟 Langfuse trace 集成的便捷度
```

**通过标准**:1、2 必须为"是"。

**失败 fallback**:直接调 Anthropic API,自己写薄包装。

### Langfuse PoC

```text
1. 自部署版能不能正确接收 OpenTelemetry trace
2. cost 计算是否准确(跨模型 / 跨 token type)
3. 高频写入下是否稳定(每任务可能几十次 LLM 调用)
4. 自部署的备份恢复是否简单
```

**通过标准**:1、2 为"是"。3 是性能问题,可以后续优化。

**失败 fallback**:structlog + events 表自己实现 trace,失去 UI 但保留数据。

### GitHub CLI PoC

```text
1. 能不能稳定创建 PR 并附带长 body(几 KB markdown)
2. 能不能查询 PR 的所有 CI check 状态
3. 失败时错误信息是否可读
```

**通过标准**:1、2 为"是"。

**失败 fallback**:GitHub API + 自己拼请求。

### gitleaks PoC

```text
1. 本地 pre-commit gate 是否稳定
2. CI gate 是否能覆盖 git history
3. 误报率(False Positive)是否可控
```

**通过标准**:1 或 2 至少有一个稳定。建议**两边都装**(深度防御)。

**失败 fallback**:trufflehog 或自写 regex 扫描。

## PoC 验证的执行原则

```text
1. PoC 不写正式代码,只验证能力
2. 每个 PoC 给硬时间盒(最多 1 天)
3. 不通过立即走 fallback,不要"调一调说不定行"
4. PoC 通过后,工具进入主路径前再补正式集成
5. PoC 结论写入 docs/poc-results.md,后续 review 时参考
```

## Hermes 取舍

经过深度分析(详见附录),**Hermes 的当前定位是"自演化单 agent",不是 multi-agent 框架**。它的招牌(skill 自演化)对应你系统的 H 域,但不能整体引入。

**最终决策**:不引入 Hermes 软件,**借鉴它的 skill curator 设计**用 Postgres 自实现(~400 行)。详见 Part VI。

如果想省时间,**可以保留 Hermes 当入口层**(只用它的 18 平台 gateway),不进入核心架构。

## 业界开源工具的"轮子之争"

以下是经过讨论的取舍记录,避免重新发明轮子:

| 想自己写 | 业界开源选择 | 选定方案 | 节省 |
|---|---|---|---|
| state_machine.py | LangGraph / Temporal | **LangGraph** | 1-2 周 |
| event_store.py | Postgres + 表 | 自己写(10 行) | - |
| role_runner.py | Claude Agent SDK | **Claude Agent SDK** | - |
| 记忆 markdown | Langfuse Datasets / Postgres | **Postgres + markdown 双轨** | - |
| observability | Langfuse | **Langfuse 自部署** | 1 周 |
| Git worktree 管理 | Claude Code `-w` 原生 | **Claude Code 原生** | 几天 |
| Queue | Postgres SKIP LOCKED / Inngest | V1: **Postgres** / V2+: 评估 Inngest | - |
| 向量检索 | Pinecone / pgvector | V1: 无 / V2: **pgvector** | 不增加组件 |

## 工具不引入的清单

明确**不引入**的工具(避免过度工程):

- **LangChain**:已选 LangGraph,LangChain 是冗余抽象层
- **CrewAI / AutoGen**:跟你的设计哲学不匹配,且生产能力弱于 LangGraph
- **Vector DB**(Pinecone / Weaviate / Qdrant 独立服务):V1 用 SQL 检索,V2 上 pgvector
- **Kubernetes**:单机 docker-compose 够,K8s 是负担
- **Inngest / Temporal**:V1 用 LangGraph + Postgres,任务量大再评估
- **mem0 / Letta**:记忆需求用 Postgres 自实现更可控

## 模块边界保护(v2.3 新增)

agent-org 是 **modular monolith**——单进程部署,但内部严格模块边界。

**核心问题**:AI 迭代下(Claude.ai 帮写、V1.5+ agent-org 自服务),模块边界容易腐烂。AI 没有"模块洁癖",优化的是"完成任务",会写最快的代码即使越界。

**核心原则**:每个模块有**显式声明的 public API**。这是其他所有保护手段的前提——没有 public/internal 区分,linter / prompt / review 都无从下手。

### 落地三件套

#### 1. _internal/ + __init__.py(基础,最重要)

每个能力模块的目录结构:

```
orchestrator/memory/
├── __init__.py            # public API 唯一暴露处
├── _internal/             # 内部实现,跨模块禁止访问
│   ├── store.py
│   ├── curator.py
│   └── _shared.py
└── protocols.py           # (可选)Protocol 声明
```

`__init__.py` 只 export public 函数:

```python
# orchestrator/memory/__init__.py
"""
Memory module: project knowledge storage and retrieval.

Public API only. Other modules NEVER import from memory._internal.
"""
from ._internal.store import (
    get_relevant_memory,
    add_memory_candidate,
    mark_active,
    export_to_markdown,
)

__all__ = [
    "get_relevant_memory",
    "add_memory_candidate",
    "mark_active",
    "export_to_markdown",
]
```

**约定**:
- `_internal/` 目录下所有文件视为模块私有
- 跨模块 import 必须只 import top-level namespace(`from orchestrator.memory import get_relevant_memory`)
- 想 export 新功能 → **必须改 `__init__.py`**(这是显式决策,不是偶然)

#### 2. coding-subagent-prompt 加"模块边界纪律"

让 AI 在写代码时就知道这个规则。详见 `docs/operations/coding-subagent-prompt.md`。

关键引导:

```text
- 跨模块 import 只用 top-level namespace
- 需要其他模块的内部细节 → 先改它的 public API,再 import
- 优先依赖 Protocol,不依赖具体类
- 跨模块"快捷方式"是腐烂的开始
```

#### 3. import-linter 强制

`importlinter.cfg`(Phase 0A 就建,CI 跑):

```ini
[importlinter]
root_package = orchestrator

[importlinter:contract:no_cross_internal_access]
name = No cross-module access to _internal
type = forbidden
source_modules =
    orchestrator.dispatcher
    orchestrator.roles
    orchestrator.state_machine
forbidden_modules =
    orchestrator.memory._internal
    orchestrator.artifact._internal
    orchestrator.event_log._internal
    orchestrator.budget._internal

[importlinter:contract:layered]
name = Layered architecture
type = layers
layers =
    _runtime
    state_machine
    dispatcher
    roles
    execution
    llm
    memory | event_log | artifact | escalation | budget
    _shared
```

CI 跑 `lint-imports`,违反就 fail。

### 跟宪法第 12 条的关系

这套保护**就是第 12 条宪法在"开发流程"上的应用**:

```text
LLM 输出 = AI 写的代码(可能违反边界)
确定性兜底 = import-linter / _internal 约定(强制守边界)
```

跟 dispatch_plan validator 的设计哲学完全一致——**LLM 起点,确定性兜底**。

### 不做的事(避免过度工程)

V1 不做:

- ❌ 架构测试(import-linter 已覆盖)
- ❌ pre-commit hook(CI 已覆盖,只是反馈早一点)
- ❌ 完整 Protocol/ABC 体系(V1.5 视情况加)
- ❌ 模块版本号 / 模块独立打包(过度抽象)

**判断原则**:有"public API 显式化"+"linter 自动 enforcement"这两项,V1 阶段足够。后续真出现腐烂模式再加新工具。

---

# Part V:V1 分阶段实施路线

## V1 总原则

V1 不追求一次性实现完整 autonomous multi-agent 研发组织。

**V1 目标**:跑通最小自治闭环:

```text
Owner 发任务
→ PM_PLANNING:PM 业务拆解 + 角色调度(输出 raw dispatch plan)
→ Validator:确定性校验 + 规则补齐 → normalized dispatch plan
→ DISPATCH:按 role_sequence(step 排序)调用角色
→ ROLE_EXECUTING:Developer / Reviewer / Tester / Architect / Security Reviewer 按需执行
→ CI + Reviewer 质量门
→ PR_READY 或 ESCALATED_TO_OWNER
→ 全过程写入 event log、artifact store、memory candidates
```

**关键约束**:Architect / Tester / Security Reviewer 都是**可选角色**,不在状态机里写死。具体调用谁由 PM 输出 + validator 校验决定。

## V1 保留 vs 暂缓

| V1 必须保留 | V1 暂时不做 |
|---|---|
| 确定性调度者 | 复杂多项目 Program-PM |
| 角色定义 | 3 模型 Reviewer Panel |
| 状态机(LangGraph) | Debate round |
| 消息中转 | Arbiter 自动仲裁 |
| 事件日志 | 角色 A / B 灰度 |
| 项目记忆 | 自动参数调优 |
| 失败升级 | 完整成本归因 dashboard |
| 产物归档 | 跨项目学习 |
| 预算硬上限 | 完整自我改进系统 |
| gitleaks + 受保护路径 | Dashboard UI |

## 7 个 Phase 总览(基于 codex review 重新分期)

> **节奏原则**:每个 phase 1 周硬时间盒。跑不完不延期,而是**降级当前 phase 的范围**:把没做完的能力推到下一个 phase 或 V2。这避免单人探索性项目陷入"反正不赶时间"的拖延陷阱。
>
> 总周期 **6-8 周**(包含 Phase 0 拆分后的两段 + 各 phase 的弹性)。

| Phase | 名称 | 核心目标 | 周期 | 关键约束 |
|---|---|---|---|---|
| **Phase 0A** | 文件骨架 | 建 repo 结构、role、task、event 契约 | 2-3 天 | 不接 DB,不接外部服务 |
| **Phase 0B** | 最小 runtime | 读 task.yaml,写 events.jsonl,跑固定状态 | 2-3 天 | 不接 Git,不接 Claude Code,Developer 可 mock |
| **Phase 0C** | 基础设施替换 | events.jsonl → Postgres,加 Langfuse | 2-3 天 | 跑通 PoC 验证门后才上 |
| **Phase 1** | 单任务 LLM 闭环 | PM + Architect + Reviewer 输出结构化结果 | 1 周 | Developer 可 mock |
| **Phase 2** | Git 执行环境 | branch/worktree/diff/protected path | 1-2 周 | 不自动 PR |
| **Phase 3** | 质量门 + PR | test/lint/build/gitleaks/reviewer/PR_READY | 1-2 周 | **不 auto-merge**,Owner 手动 merge |
| **Phase 4** | 最小记忆 | failures/decisions/context_pack | 1 周 | **Markdown 单向导出**,DB 是真相源 |
| **Phase 5** | 多任务并行调度 | task queue + worktree 资源调度 + 跨任务的 LLM rate limit 处理 | 1 周 | 项目记忆隔离 |

**关键设计选择**:

- Phase 0 拆为 0A / 0B / 0C(避免基础设施先行卡死核心闭环)
- Phase 3 不 auto-merge(V1.5 才上)
- Phase 4 改单向同步(双向推迟到 V2)
- 周期 6-8 周(每 phase 硬时间盒,跑不完降级)

---

## Phase 0A:文件骨架(2-3 天)

### 阶段目标

建立**纯文件层**的系统骨架,不引入任何外部服务。这一阶段验证的是**架构契约是否清晰**,不验证任何运行能力。

**反模式警告**:不要在 Phase 0A 安装 Postgres、Langfuse、Claude Code。这些都推迟到 0C。

### 目录结构

```text
agent-org/
  README.md
  constitution.md                   # 12 条系统宪法
  CLAUDE.md                          # 给 Claude Code 的项目说明

  roles/
    _template/                       # v2.1 模板目录(cp -r 起步)
    pm/        { role.yaml, system_prompt.md, golden_dataset/ }
    developer/ { role.yaml, system_prompt.md, golden_dataset/ }
    reviewer/  { role.yaml, system_prompt.md, golden_dataset/ }
    architect/ { role.yaml, system_prompt.md, golden_dataset/ }   # 可选

  meta_prompts/                      # v2.1 LLM 辅助生成
    generate_role_prompt.md
    generate_golden_dataset.md

  scripts/
    generate_role_prompt.py
    generate_golden_case.py

  projects/
    example-api.yaml                 # 至少 1 个示例项目(含 roles / role_groups)
    example-api.dispatch_policy.yaml # v2.2 dispatch_policy 配置

  tasks/
    inbox/                           # 待处理任务
    active/                          # 正在执行
    done/                            # 已完成
    failed/                          # 失败归档

  runs/                              # 每次执行的产物

  schemas/
    task.schema.json
    event.schema.json
    role.schema.json
    project.schema.json
    dispatch_policy.schema.json      # v2.2
    role_invocation.schema.json      # v2.2 输入/输出 protocol
    pm_dispatch_plan.schema.json     # v2.2 PM artifact
    vocabulary.md                    # D1 全局词汇表

  docs/
    role_prompt_structure.md         # v2.1
    golden_dataset_format.md         # v2.1
    poc-results.md                   # 0C 跑完才填
    decisions/
```

### Phase 0A 完成标准

```text
1. agent-org repo 创建完成,所有目录就位(含 meta_prompts/、scripts/、roles/_template/)
2. 必需角色的 role.yaml 写完(PM / Developer / Reviewer)
3. constitution.md 落地(12 条宪法 v2.2)
4. vocabulary.md 落地
5. 至少 1 个 project.yaml(含 roles / role_groups)
6. 至少 1 个 dispatch_policy.yaml(含 mandatory_role_rules / pm_deviation_policy)
7. 至少 1 个 task.yaml 示例
8. schemas 通过 jsonschema 校验
9. docs/role_prompt_structure.md + docs/golden_dataset_format.md 落地
10. meta_prompts 文件就位,scripts/generate_role_prompt.py 跑通(能调 Claude API)
11. 所有内容在 Git 里,可以 diff
```

**没有完成 = 不准进 Phase 0B**。

---

## Phase 0B:最小 runtime(2-3 天)

### 阶段目标

跑通**最小可执行的状态机**。Developer 用 mock,其他角色可以是 LLM 也可以是 mock。重点是验证**状态推进、事件记录、失败 escalation 的契约**。

### 关键约束

- **不接 Postgres**:状态写 `events.jsonl` 文件
- **不接 Git**:任务不真的改代码,Developer mock 出 "假装我改了 src/foo.py"
- **不接 Claude Code**:执行器是 mock 或者直接调 Anthropic API
- **不接 Langfuse**:日志用 structlog 写本地 JSON
- **不接 worktree**:不需要,Phase 2 才用

### 最小 runtime 应该能做的事

```text
1. python -m orchestrator run tasks/inbox/task-001.yaml
2. orchestrator 读 task.yaml
3. 推进状态机:CREATED → PM_PLANNING → DISPATCH → ROLE_EXECUTING → DISPATCH → ... → DONE / ESCALATED
4. 每步把事件写 runs/task-001/events.jsonl
5. PM 调真实 LLM,输出 business_breakdown + raw dispatch plan
6. Validator 校验 plan,生成 normalized dispatch plan
7. 其他角色(Developer / Reviewer / Architect 等)mock 实现(v2.4 明确)
8. 所有角色输出符合 role_invocation_protocol
9. 成功 → 生成 runs/task-001/final_report.md
10. 失败 → 生成 runs/task-001/escalation.md
```

### Phase 0B 完成标准

```text
1. 一行命令能跑完一个 task.yaml
2. PM 输出结构化(含 business_breakdown + role_sequence,v2.4 结构)
3. Validator 能校验 plan(漏 mandatory / 不存在的 role_id / 循环依赖 / step 不连续等)
4. Validator 失败时两级处理(RETRY_PM / FATAL,v2.4:删 autofix)生效
5. DISPATCH 能按 normalized plan 的 step 顺序调用角色
6. 各角色输出符合 role_invocation_output schema(含 attempt 字段)
7. 同 (subtask, role) attempt 上限 2 次,超过强制 escalate
8. Schema 错误 / high+immediate_escalate signal / budget exceeded 时能停在 ESCALATED_TO_OWNER
9. events.jsonl 记录每一步,含 PLAN_RETRY_REQUESTED / ATTEMPT_LIMIT_REACHED 事件
10. final_report.md 或 escalation.md 生成
11. 失败时能从命令行看到清晰原因
12. 整个 runtime 不超过 800 行 Python
```

**注意**:这一阶段允许"丑陋",但**契约必须正确**。所有 schema、字段、状态转换都要跟最终架构一致。特别是 **Architect 不能出现在状态机骨架里**——它只是一种可选角色。

---

## Phase 0C:基础设施替换(2-3 天)

### 阶段目标

把 Phase 0B 的"文件版"runtime 升级到"基础设施版"。**前提是 PoC 验证门全部跑通**。

### 工作内容

```text
1. events.jsonl → Postgres task_events 表
2. structlog → Langfuse trace
3. 本地 Python 进程 → docker-compose 起 Postgres + Langfuse
4. role 调用 → 加 budget 跟踪
5. PoC 验证清单跑完,结论写 docs/poc-results.md
```

### Phase 0C 完成标准

```text
1. docker-compose up 起 Postgres + Langfuse
2. 同一个 task.yaml 跑出来,事件全部进 Postgres
3. Langfuse 能看到完整 trace
4. PoC 验证结果文档化(LangGraph / Claude Code / Langfuse 全部验证)
5. 任一 PoC 失败,走对应 fallback(架构不变)
6. 备份脚本就位(Postgres dump + Git push)
```

**Phase 0 整体完成标志**:0A + 0B + 0C 全部 ready,可以进 Phase 1。

---

---

## Phase 1:单任务闭环(v2.0:动态调度)

### 阶段目标

跑通 LangGraph **PM_PLANNING + DISPATCH 循环**:PM 业务拆解 → 调度者按 PM 的 role_sequence(step 排序)派活 → 每个角色按 role_invocation_protocol 调用 → 完成或 escalate。

### LangGraph 状态机(v2.0)

```text
CREATED
  ↓
PM_PLANNING (一次性)
  - PM 业务拆解
  - PM 决定每个子任务的 role_sequence(step + role_id)
  - PM 输出 dispatch plan
  ↓
DISPATCH (循环节点)
  - 看 task_state.pending_roles
  - 如果还有未执行的角色 → ROLE_EXECUTING
  - 如果全部完成 → DONE
  - 如果累计 high signals ≥ 3 → ESCALATED
  - 如果 budget exceeded → ESCALATED
  ↓
ROLE_EXECUTING
  - 按 PM 的调度顺序调用下一个 ready 角色
  - 角色返回 output (含 signals)
  - 调度者处理 signals
  ↓ (回到 DISPATCH)

终态:
  DONE
  ESCALATED_TO_OWNER
  BUDGET_EXCEEDED
```

### LangGraph 实现要点(v2.0)

```python
# orchestrator/graph.py
from langgraph.graph import StateGraph, END

graph = StateGraph(TaskState)

# 静态节点
graph.add_node("pm_planning", pm_planning_node)
graph.add_node("dispatch", dispatch_node)
graph.add_node("role_executing", role_executing_node)
graph.add_node("escalate", escalation_node)

graph.set_entry_point("pm_planning")
graph.add_edge("pm_planning", "dispatch")

# DISPATCH 是核心:动态决定下一步
graph.add_conditional_edges("dispatch", route_after_dispatch, {
    "execute": "role_executing",
    "done": END,
    "escalate": "escalate"
})

# 角色执行完回到 DISPATCH
graph.add_edge("role_executing", "dispatch")
graph.add_edge("escalate", END)

# Postgres checkpoint(自带的持久化)
app = graph.compile(checkpointer=postgres_checkpointer)
```

```python
def route_after_dispatch(state):
    """DISPATCH 节点的路由逻辑"""
    
    # 兜底检查
    if state.cost_used_usd >= state.budget_usd:
        state.escalation_reason = "BUDGET_EXCEEDED"
        return "escalate"
    
    if count_high_signals(state) >= 3:
        state.escalation_reason = "HIGH_SIGNALS_OVERFLOW"
        return "escalate"
    
    # 找下一个 ready 角色
    next_role = find_next_ready_role(state)
    if next_role is None:
        # 所有角色完成
        return "done"
    
    state.current_role = next_role
    return "execute"


def find_next_ready_role(state):
    """按 PM 调度顺序找下一个能跑的角色(v2.4:按 role_sequence.step 排序)"""
    for subtask in state.business_breakdown:
        if subtask.status == "done":
            continue
        if not subtask.dependencies_met(state):
            continue
        
        # 按 step 排序,找该子任务下一个未执行的角色
        ordered = sorted(subtask.role_sequence, key=lambda x: x.step)
        for item in ordered:
            if not subtask.role_completed(item.role_id):
                return (subtask.subtask_id, item.role_id)
    
    return None
```

### 关键产出契约(v2.0)

PM 输出(详见 A 域):

```yaml
pm_planning_output:
  parsed_intent: ...
  assumptions: [...]
  complexity: {...}
  
  business_breakdown:
    - subtask_id: ...
      description: ...
      task_type: simple_feature | complex_feature | ...
      success_criteria: [...]
      role_sequence:
        - {step: 1, role_id: architect}
        - {step: 2, role_id: developer}
        - {step: 3, role_id: reviewer}
      dependencies: []
  
  role_dispatch_notes:
    - subtask: ...
      deviation_from_template: ...
      reason: ...
  
  confidence: 0.0
  signals_to_other_roles: []
```

各角色输出(统一 role_invocation_protocol,详见 D 域):

```yaml
role_invocation_output:
  role_id: developer | architect | reviewer | ...
  task_id: ...
  subtask_id: ...
  verdict: success | needs_changes | escalate
  artifact: {...}
  signals_to_other_roles: [...]
  cost_used: {...}
```

### 预算护栏(每个角色执行后)

```python
def role_executing_node(state):
    role_id = state.current_role.role_id
    output = invoke_role(role_id, state.context_pack)
    
    state.cost_used_usd += output.cost_used.usd
    state.role_outputs.append(output)
    
    # 预算硬上限
    if state.cost_used_usd > state.budget_usd:
        state.escalation_reason = "BUDGET_EXCEEDED"
    
    return state
```

### Phase 1 完成标准(v2.0)

```text
1. 输入一个 task.yaml
2. PM_PLANNING 节点能生成 business_breakdown + role_sequence(step+role_id)
3. DISPATCH 节点能按 PM 决定按顺序派 ≥ 2 个角色
4. 不同的 task_type 能走不同的角色组(simple → [dev, reviewer],complex → [arch, dev, reviewer])
5. 每一步都写入 task_events 表
6. 角色 signals 能影响下一步流向
7. 失败时生成结构化 escalation
8. 预算超限立即停止
9. Langfuse 能看到完整 trace
10. 配置加新角色(改 project.yaml)能被 PM 识别和调用
```

### V2.0 重要约束

```text
V1 阶段子任务之间先串行 (即使无依赖也不并行)
  原因:并行子任务需要多个 worktree 同时管理,V1 简化
  V1.5 / V2 加子任务并行
```

---

## Phase 2:Git 执行环境

### 阶段目标

调度者为任务创建真实执行环境(branch + worktree),Developer agent 在 worktree 内执行,收集 diff,**受保护路径强制阻止**,**数据库/端口隔离(全栈项目)**。

### project.yaml 示例

```yaml
project_id: example-api
name: Example API
repo_url: git@github.com:owner/example-api.git
main_branch: main
local_main_path: /srv/agent-projects/main/example-api
worktree_root: /srv/agent-projects/worktrees/example-api
commands:
  install: pnpm install
  test: pnpm test
  lint: pnpm lint

# 三级 protected paths (基于 codex review 反馈)
protected_paths:
  # hard_block: 任何 agent 不允许改,基础设施层强制拦截
  hard_block:
    - .env
    - .env.*
    - secrets/
    - private_keys/
    - .github/workflows/deploy.yml

  # approval_required: 可以改,但 PR body 标红 + Owner 必须单独 review
  # 不允许 auto-merge (V1.5 也不允许)
  approval_required:
    - package.json
    - pnpm-lock.yaml
    - yarn.lock
    - package-lock.json
    - Dockerfile
    - Dockerfile.production
    - docker-compose.yml
    - migrations/

  # warn_only: 允许改,PR body 中提示有改动
  warn_only:
    - README.md
    - docs/

isolation:
  database: branch  # neon / supabase / pg_branch
  port_offset: random  # PORT=$((3000 + $RANDOM % 1000))
```

**三级护栏的含义**(对应宪法第 6 条"硬护栏在基础设施层强制,软风险由质量系统判断"):

```text
hard_block        → 基础设施层强制拦截,agent 永远改不了
approval_required → agent 可以改,但走特殊审批流(Owner 单独 review)
warn_only         → agent 可以改,PR body 提示
```

### Worktree 结构

```text
/srv/agent-projects/
  main/
    example-api/           # 主仓库
  worktrees/
    example-api/
      task-2026-05-23-001/
      task-2026-05-23-002/
```

### 分支命名规则

```text
agent/{task_id}-{short-title}
```

### Developer 执行抽象

```python
# orchestrator/role_runner.py
def run_role(
    role: str,
    executor: str,  # "claude-code" | "codex-cli"
    context_pack: ContextPack,
    repo_path: str,
    worktree_path: str,
) -> RoleOutput:
    ...
```

### Phase 2 完成标准

```
1. orchestrator 能为 task 自动创建 branch
2. orchestrator 能为 task 自动创建 worktree
3. Worktree 内 deps 自动安装(pnpm/yarn 全局 store)
4. Developer agent 能在 worktree 内执行
5. 执行后能收集 git diff
6. 受保护路径被检测并阻止(硬护栏,基础设施层)
7. 所有命令与输出归档
8. 端口/数据库隔离(全栈项目)
9. 任务结束 worktree 自动清理
10. 7 天以上 stale worktree 定时清理
```

### Phase 2 Executor 最小保护(v2.2 新增)

> Git worktree 是工程隔离,不是安全沙箱。V1 接受这个风险,但实施时加最小保护:

```text
1. executor working_dir 固定到 task worktree(避免误入主仓库)
2. executor 环境变量使用白名单(只传必要的环境变量)
3. 不把 orchestrator DB URL 传给 executor(防止 LLM 误操作 DB)
4. 不把 production secrets 挂进 worktree
5. protected_paths_check 必跑(基础设施硬护栏)
6. gitleaks 必跑
7. executor 输出只能通过 artifact protocol 回传(不直接读 stdout)
```

### V2 安全沙箱选项(不在 V1 范围)

```text
V2 再评估:
1. Docker sandbox
2. Firecracker / microVM
3. per-task Unix user
4. read-only mounted repo + explicit writable diff dir
```

---

## Phase 3:质量闭环

### 阶段目标

从"agent 能改代码"升级为"系统能判断是否可提交"。**这是 V1 最关键的 phase,质量门必须扎实**。

### 静态质量门(基础设施层强制)

```yaml
quality_gates:
  hard_gates:  # 不过就 block
    - tests_pass
    - lint_pass
    - build_pass
    - gitleaks_pass            # ★ 防 secret 提交
    - protected_paths_check
    - diff_size_limit          # ★ 改超过 N 行直接 block
    - max_files_changed: 20

  soft_gates:  # warn but don't block
    - coverage_delta >= 0
    - semgrep_pass (可选)
```

### Tester 阶段

Tester 在 V1 是**确定性命令执行器**(不是 LLM):

```text
install → lint → test → build → gitleaks → diff_check
```

失败进入 `TEST_FAILED → FIXING → TESTING`。

### Reviewer 阶段

V1 用**单 reviewer**,但接口预留 panel:

```python
class ReviewerPanel:
    def __init__(self, reviewers: list[Reviewer]):
        self.reviewers = reviewers

    def review(self, pr_context) -> PanelVerdict:
        if len(self.reviewers) == 1:
            return self.reviewers[0].review(pr_context)
        else:
            # V2: 跨模型并行 + 严格一票否决
            return self._aggregate_with_veto(...)
```

### Reviewer 输出契约(v2.4 重命名)

```yaml
review_result:
  verdict: approve | request_changes | reject
  blocking_issues: []
  non_blocking_issues: []
  must_escalate_to_owner: true | false   # v2.4:替代 security_or_data_loss_risk
  escalation_reason: string              # v2.4:must_escalate=true 时必填
  suggested_fixes: []
```

### 一票否决的 V1 简化版

```python
if review.must_escalate_to_owner:
    return REJECT  # 直接拒,不允许自动 PR
```

### PR 生成

```text
1. push branch
2. create PR (gh pr create)
3. PR body 自动附:
   - task 摘要
   - PM 输出
   - 测试结果
   - reviewer 结论
   - 风险说明
   - 改动了哪些 approval_required 路径(如有)
4. 状态推进到 PR_READY,任务结束
5. Owner 收到飞书通知,手动 merge
```

**关键变化**(基于 codex review):

```text
V1   PR_READY → Owner 手动 merge
V1.5 低风险项目可开启 auto-merge
V2   3-reviewer panel 稳定后,全面 auto-merge
```

**为什么 V1 不 auto-merge**:

```text
1. V1 reviewer 仍然是单 reviewer
2. 质量门未经长期验证
3. 记忆和失败沉淀还不成熟
4. auto-merge 会把系统错误直接放大到主干

Owner 不在 review loop ≠ 没有任何人工 gate
保留 merge 决定权,是廉价但关键的护栏。
```

### Phase 3 完成标准

```text
1. 测试失败会进入 FIXING
2. reviewer request_changes 会进入 FIXING
3. 最多自动重试 1 次
4. 超过重试次数进入 ESCALATED_TO_OWNER
5. gitleaks 扫到 secret 直接 block
6. diff 超过 limit 直接 block
7. 通过后能生成 PR (状态 PR_READY)
8. PR body 包含完整 trace 摘要
9. PR body 明确列出 approval_required 改动(如有)
10. PR_READY 通过飞书通知 Owner
11. Owner 手动 merge(V1 不 auto-merge)
```

V1 的成功终点是 **PR_READY**,不是 MERGED。

---

## Phase 4A:可用记忆(1 周)

### 阶段目标

让系统开始具备"持续认知"——但只做**最小可用记忆**,治理推迟到 4B。

**Postgres 是真相源,Markdown 是单向导出**(V1 不做双向同步)。

完整实现见 [Part VI](#part-vi记忆机制实现层)。

### Phase 4A 范围

```text
1. memory_items 表落地(E3 项目记忆 schema)
2. 两类 memory:decisions(成功任务沉淀)+ failures(失败任务沉淀)
3. 手动 active / inactive(Owner 直接改数据库或用 SQL 脚本)
4. context_pack 能按 project_id + tags + recency 检索
5. PM 在 PM_PLANNING 时拿到相关 memory
6. Markdown 单向导出(DB → docs/memory/*.md)
7. H1b 失败聚类告警(轻量版,同类失败 N 次告警 Owner)
```

### Phase 4A 完成标准

```text
1. 成功任务可以沉淀 decision memory candidate(自动写入 pending_review)
2. 失败任务可以沉淀 failure memory candidate(H1a 结构化存档)
3. Owner 可以手动 approve / reject / deactivate memory
4. PM context_pack 能读到 active memory
5. Markdown export 能生成 docs/memory/*.md
6. 同类失败 ≥ N 次 → 飞书告警 Owner(H1b)
```

### Phase 4A 不做的

```text
- 不做 Curator cron(治理推迟到 4B)
- 不做 PR review 飞书 Pending Review 队列(治理推迟到 4B)
- 不做自动 active 策略(治理推迟到 4B)
- 不做 stale memory 检测(治理推迟到 4B)
```

---

## Phase 4B:记忆治理(后续,非强制)

### 阶段目标

降低 Owner 维护记忆的成本。**不阻塞 V1 验收**(V1 跑稳后再做)。

### Phase 4B 范围

```text
1. Curator cron 跑通(打分 + 淘汰)
   - 频率参考 Hermes(7 天 + idle 2 小时)
2. 不同 memory layer 不同的自动 active 策略
3. Pending Review 队列推飞书
4. Owner 反馈结构化收集(H4)
5. stale memory 检测
```

### Phase 4B 入口条件

- Phase 4A 跑稳 2-4 周
- 项目记忆条目 ≥ 30 条(否则治理没意义)
- Owner 真实感受到"手动管理太累"

### 关键设计选择

```text
V1:  DB → Markdown 单向导出
V1:  不做 H 域 self-evolution
V2:  评估 Markdown → DB 反向同步(目前不做)
V3+: 重新考虑 self-evolution(等业界数据成熟)
```

**为什么不做双向**:

```text
1. 冲突处理复杂(Owner 改 markdown vs Curator 写 DB)
2. 谁是真相源不清
3. schema 变化时同步逻辑要重写
4. 单人维护成本太高

V1 阶段 Owner 想改记忆,直接改 DB 或写 SQL 脚本。
```

**为什么不做 self-evolution**:

```text
1. unobservable learning:agent 学坏了不会 loud failure,只会 silent drift
2. 单人维护没人能帮 Owner 看出 drift
3. LLM 错误高度相关,skill 自演化容易陷入 optimization-loop gaming
4. Hermes 社区自己也在讨论"学坏怎么办"
```

---

## Phase 5:多任务并行调度

### 阶段目标

实现多个 task 之间的真正并行执行,任务间不串行(每个 task 有独立 worktree)。

### 并发模型

```text
任务间: 默认并行,每个 task 有独立 worktree + task_id
任务内: 角色顺序执行(状态机)
唯一硬约束: 同 worktree 同时只跑一个 task(自动满足,每个 task 创独立 worktree)
```

### Queue 实现

```sql
-- Postgres + SKIP LOCKED 实现 queue,不增加组件
-- 注:不再按 project_id 串行,任务间直接并行
WITH next_task AS (
  SELECT task_id FROM tasks
  WHERE status = 'queued'
    AND NOT EXISTS (
      -- 唯一约束:同一 worktree 不能有正在运行的任务
      SELECT 1 FROM tasks t2
      WHERE t2.worktree_path = tasks.worktree_path
        AND t2.status = 'running'
    )
  ORDER BY priority DESC, created_at ASC
  LIMIT 1
  FOR UPDATE SKIP LOCKED
)
UPDATE tasks SET status = 'running'
WHERE task_id IN (SELECT task_id FROM next_task)
RETURNING *;
```

### 调度规则

```text
1. Queue FIFO + priority 排序
2. 任务间默认并行(没有 project 级锁)
3. 同 worktree 串行(由 worktree_path 唯一性保证)
4. 全系统并发上限由 G4 配额管理(防 LLM rate limit 爆)
5. system budget exceeded 则暂停新任务
6. starvation prevention:排队超 N 天提升优先级
```

### Owner 强制串行的逃生口

如果 Owner 想让某两个任务串行(罕见,但合法),可以在 task.yaml 标记:

```yaml
task_id: task-2026-05-24-002
blocking_on: task-2026-05-24-001  # 必须等 task-001 完成
```

调度器会查 blocking_on,等待依赖任务完成再启动。

### Phase 5 完成标准

```
1. 至少 3 个并行 task 能同时跑
2. 每个 task 有独立 worktree(物理隔离)
3. 每个 task 有独立 task_id 和 state(逻辑隔离)
4. 每个 project 有独立 memory(项目隔离)
5. 任一 task 失败不影响其他 task
6. blocking_on 字段工作正常(Owner 强制串行)
7. G4 全系统并发上限工作正常(防 LLM rate limit 爆)
8. starvation prevention 工作正常
9. system-wide budget 兜底
```

---

## V1 完成判定

V1 成功不是看系统多复杂,而是看下面这些问题能否稳定回答"是":

```
1. Owner 能不能只发任务,不亲自拆任务?
2. PM 能不能稳定产出结构化理解?
3. Architect 能不能拦住明显错误拆解?
4. Developer 能不能在隔离 worktree 里改代码?
5. 测试失败能不能自动进入修复?
6. Reviewer 能不能阻止明显坏 diff?
7. 系统能不能生成可读 PR?
8. 失败时 Owner 能不能看到结构化求助?
9. 每次失败能不能沉淀到记忆库?
10. 多个 task 能不能真正并行跑?(独立 worktree + 独立 state)
11. 预算超限能不能可靠拦住?
12. gitleaks 能不能拦住 secret 提交?
```

如果以上问题都能回答"是",V1 就完成了。

---

# Part V.5:State / Event / Artifact / Memory 分层(v2.2 新增)

设计文档同时出现多种存储层:LangGraph checkpoint、Postgres task_events、runs/ artifacts、Postgres memory、Markdown 导出、Git。这些都合理,但缺少分层定义会导致实现混乱。

## 分层定义

| 层 | 真相源 | 是否可变 | 用途 |
|---|---|---:|---|
| **task_state** | LangGraph checkpoint / Postgres tasks 表 | 可变 | 当前任务恢复、调度进度 |
| **event_log** | Postgres `task_events` (append-only) | 不可变 | 审计、回放、debug |
| **artifact_store** | `runs/<task_id>/artifacts/` + artifact metadata | 不可变 | 角色产物、报告、patch、review |
| **memory** | Postgres `memory_items` | 可变,有版本 | 跨任务知识 |
| **markdown_export** | Git markdown 文件 | 派生物(不作为写入源) | 人类可读 |
| **PR / branch** | GitHub / Git | 可变 | 交付物、代码 review |

## 核心规则

```text
1. task_state 用于恢复,不用于审计
   - 可被覆盖、可被 checkpoint 回滚
   - 调试看 event_log,不要看 task_state

2. event_log 是审计真相源,只 append,不 update
   - Postgres task_events 表是不可变事件流
   - 一切重要事件都在这里(STATE_CHANGED / ROLE_INVOKED / SIGNAL_RECEIVED / 
     PLAN_RETRY_REQUESTED / PLAN_VALIDATION_FATAL / ATTEMPT_LIMIT_REACHED /
     IMMEDIATE_ESCALATE_TRIGGERED / 等等)
   - Phase 0B 是 events.jsonl,Phase 0C+ 是 Postgres,本质一致
   - v2.4 修订:删除 PLAN_AUTOFIXED 事件(因为 autofix 这一档被删了)

3. artifact 一旦写入不可变(v2.4 明确 attempt 机制)
   - 新版本生成新 artifact_id,旧版保留
   - role retry 产生的是新 attempt(attempt N+1),老的标 superseded_by 新 artifact_id
   - dispatcher 取"当前 artifact" = (subtask, role) 下 max(attempt)
   - 同 (subtask, role) attempt 上限默认 2,第 3 次强制 ATTEMPT_LIMIT_REACHED → escalate
   - artifact_id 是 UUID,由调度者生成

4. memory 的真相源是 Postgres,不是 markdown
   - Curator 写 Postgres
   - Postgres → markdown 是单向导出
   - markdown 被人手改了,系统不读回(下次 Curator 写时会覆盖 markdown)

5. markdown 只能单向导出,不支持反向同步
   - V1 阶段不做 markdown → DB 反向同步(冲突处理太复杂)
   - V2+ 评估

6. PR body 可以引用 artifact,但不是 artifact 真相源
   - PR body 是人类可读的总结
   - 真实产物在 artifact_store
```

## 跨层关系图

```text
┌─────────────────────────────────────────────────┐
│  Owner / Reviewer                                │
│  ↓ 看                                            │
│  PR / Markdown(派生物,人类可读)                │
│  ↑ 派生                                          │
├─────────────────────────────────────────────────┤
│  artifact_store(不可变)─── 角色产物             │
│  memory(可变,Postgres 真相源)─── 跨任务知识    │
├─────────────────────────────────────────────────┤
│  event_log(append-only,审计真相源)             │
│  ↑ 记录                                          │
│  task_state(可变,恢复用)                       │
├─────────────────────────────────────────────────┤
│  Orchestrator + Roles                            │
└─────────────────────────────────────────────────┘
```

## 实施层影响

```text
Phase 0B:
  - events.jsonl 模拟 event_log
  - runs/<task_id>/ 模拟 artifact_store
  - 内存 state 模拟 task_state
  - 没有 memory(Phase 4 才有)
  - 没有 markdown export

Phase 0C+:
  - event_log → Postgres task_events
  - artifact_store → 仍然是 runs/ + Postgres metadata
  - task_state → LangGraph checkpoint(Postgres backed)

Phase 4A:
  - 加 memory(Postgres memory_items)
  - 加 markdown export(单向)
```

## 反模式(不该做的)

```text
❌ 用 task_state 做审计(它可变,审计需要不可变)
❌ 改 event_log(append-only,改了就破坏审计)
❌ 直接编辑 markdown 期望系统读回(markdown 是派生物)
❌ task retry 时删旧 artifact(应该生成新 artifact_id)
❌ memory 跨项目共享(违反"项目完全隔离")
```

---

# Part VI:记忆机制实现层

## 来源

讨论起点是"每个角色一个 Hermes 实例复用记忆"——经过分析否决了这个方案,原因:

1. **记忆维度混淆**:Hermes 实例会混合"项目级"和"角色级"记忆,违反"项目完全隔离"原则
2. **设计形态不匹配**:Hermes 记忆是"AI 助手陪伴单用户成长",不是"AI 角色多项目执行任务"
3. **违反"角色无状态"假设**:Hermes 是有状态进程,跟 PM 项目级"逻辑常驻"架构冲突
4. **失去 LangGraph 核心价值**:两份 state(LangGraph + Hermes)互相不可见,调试地狱
5. **运维灾难**:5 项目 × 5 角色 = 25 个 Hermes 实例

**最终选择**:抄 Hermes 的**设计模式**,用 Postgres 自己实现,~400 行代码。

## 借鉴 Hermes 的核心 idea

```
1. 经验自动转 skill (不手动写)
2. cron 周期性 grade (打分)
3. 差的自动淘汰 (不堆积)
4. 用时按相关性注入 (不全量塞)
```

## 三层记忆结构

```
┌─────────────────────────────────────────────────────────┐
│  Layer 1: 项目记忆 (per project, 所有角色共享)             │
│  - facts (项目事实)                                        │
│  - conventions (项目约定)                                  │
│  - decisions (历史决策)                                    │
│  - failures (失败教训)                                     │
│  - preferences (Owner 偏好)                                │
│  生命周期: 项目级,长期稳定                                  │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 2: 角色记忆 (per role + per project, 角色特有)      │
│  - skills (角色自己积累的做事方法)                          │
│  生命周期: 角色 × 项目维度,中期演化                         │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│  Layer 3: 任务上下文 (per task, 短期)                     │
│  - events / artifacts / state                              │
│  生命周期: 任务级,短期(任务结束归档,部分提炼到 Layer 1/2)  │
└─────────────────────────────────────────────────────────┘
```

## Postgres Schema

```sql
-- 项目
CREATE TABLE projects (
    project_id      TEXT PRIMARY KEY,
    name            TEXT NOT NULL,
    repo_url        TEXT NOT NULL,
    main_branch     TEXT DEFAULT 'main',
    config          JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Layer 1: 项目记忆
CREATE TABLE project_memory (
    id              BIGSERIAL PRIMARY KEY,
    project_id      TEXT REFERENCES projects(project_id),
    layer           TEXT NOT NULL,   -- facts | conventions | decisions | failures | preferences
    content         TEXT NOT NULL,
    structured      JSONB,
    tags            TEXT[] DEFAULT '{}',
    source          TEXT,             -- manual | task_distillation | code_scan | failure_proposal
    source_task_id  TEXT,
    status          TEXT DEFAULT 'pending_review',
    -- active | active_candidate | pending_review | deprecated | superseded

    superseded_by   BIGINT REFERENCES project_memory(id),
    score           REAL DEFAULT 1.0,
    use_count       INT DEFAULT 0,
    last_used_at    TIMESTAMPTZ,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_pm_project_layer ON project_memory(project_id, layer, status);
CREATE INDEX idx_pm_tags ON project_memory USING GIN(tags);

-- Layer 2: 角色 skills
CREATE TABLE role_skills (
    id              BIGSERIAL PRIMARY KEY,
    project_id      TEXT REFERENCES projects(project_id),
    role            TEXT NOT NULL,
    skill_title     TEXT NOT NULL,
    skill_content   TEXT NOT NULL,
    skill_type      TEXT,             -- pattern | pitfall | recipe | preference
    tags            TEXT[] DEFAULT '{}',
    triggers        TEXT[],
    score           REAL DEFAULT 1.0,
    success_count   INT DEFAULT 0,
    failure_count   INT DEFAULT 0,
    use_count       INT DEFAULT 0,
    last_used_at    TIMESTAMPTZ,
    status          TEXT DEFAULT 'active_candidate',
    -- active | active_candidate | deprecated | pending_review

    source_task_id  TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_skills_project_role ON role_skills(project_id, role, status);
CREATE INDEX idx_skills_tags ON role_skills USING GIN(tags);
CREATE INDEX idx_skills_triggers ON role_skills USING GIN(triggers);

-- Layer 3: 任务执行
CREATE TABLE tasks (
    task_id         TEXT PRIMARY KEY,
    project_id      TEXT REFERENCES projects(project_id),
    title           TEXT,
    status          TEXT,
    state           JSONB,
    budget_usd      REAL,
    cost_used_usd   REAL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE task_events (
    id              BIGSERIAL PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(task_id),
    event_type      TEXT NOT NULL,
    actor           TEXT,
    payload         JSONB,
    occurred_at     TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_events_task ON task_events(task_id, occurred_at);
CREATE INDEX idx_events_type ON task_events(event_type);

CREATE TABLE task_artifacts (
    artifact_id     TEXT PRIMARY KEY,
    task_id         TEXT REFERENCES tasks(task_id),
    producer_role   TEXT,
    artifact_type   TEXT,
    content         JSONB,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

-- Curator 工作记录
CREATE TABLE curator_runs (
    id              BIGSERIAL PRIMARY KEY,
    run_type        TEXT,
    target_table    TEXT,
    target_ids      BIGINT[],
    changes         JSONB,
    triggered_by    TEXT,
    occurred_at     TIMESTAMPTZ DEFAULT NOW()
);
```

## Curator 核心算法

### 触发时机

```
1. 任务完成时 (event-driven)         → distill_from_task (提议进 pending_review)
2. 每 7 天 + 系统 idle 2 小时 (cron) → score_recalculation + deprecate_low_score
                                       (参照 Hermes 保守频率)
3. 任务失败时 (event-driven)         → 写 failure record (H1a),不自动 distill 成 skill
4. 角色 skill 使用后 (event-driven)  → update_use_stats
```

**为什么频率从每天改为 7 天**:

```text
- Hermes 实践:默认 7 天 + idle 2 小时,业界唯一有规模的 self-evolution 案例
- 每天跑会过度刷新分数,小样本下噪声盖过信号
- 每天跑增加 LLM 成本但收益不明确
```

### 打分公式

```python
def calculate_skill_score(skill):
    """score = 使用价值 × 时间衰减 × 成功率,范围 0-10"""

    use_value = min(math.log1p(skill.use_count) * 2, 5.0)

    total = skill.success_count + skill.failure_count
    success_rate = skill.success_count / total if total > 0 else 0.5

    if skill.last_used_at:
        days_idle = (datetime.now() - skill.last_used_at).days
        time_decay = math.exp(-days_idle / 30)
    else:
        time_decay = 0.5

    return round(use_value * success_rate * time_decay, 2)
```

### 淘汰规则

```python
# 规则 1: 长期低分
deprecate where score < 0.5 AND age > 14 days

# 规则 2: 长期未使用
deprecate where last_used_at < 90 days ago AND age > 30 days

# 规则 3: 失败率过高 → pending_review (Owner 审批)
pending_review where failure_count >= 3 AND failure_count > success_count * 2
```

`deprecated` 不删除,保留可追溯。

### 失败提炼流程

```
任务失败
   ↓
PM 角色分析根因
   ↓
PM 提议 distillation:
  - lesson_type: skill | project_memory | neither
  - target_role / target_layer
  - title / content / tags / triggers
  - confidence: 0.0-1.0
   ↓
按 layer 分级处理(见下面分级表)
   ↓
最终状态: active | active_candidate | pending_review
```

**关键**:PM 不直接改记忆,是**提议**。改进决策权在 Owner。

### Curator 自动写入策略(按 layer 分级)

> **基于 codex review**:不能只用 `confidence > 0.7` 一刀切,不同 layer 风险不同。

| Memory Layer | V1 自动写入策略 | 理由 |
|---|---|---|
| **failures** | 可自动 `active`,带 `source_task_id` | 失败教训沉淀越快越好,有来源可追溯 |
| **decisions** (成功任务) | 自动 `active`,标记 `system_generated` | 历史决策记录,可追溯就行 |
| **facts** | 必须 `active_candidate`,经多次任务命中后转 `active` | LLM 提取的 facts 经常是局部事实,误当项目级会污染 |
| **role skills** | `active_candidate`,经成功使用 N 次后转 `active` | skill 是行为级影响,先试运行 |
| **conventions** | 必须 `pending_review` | 项目约定影响长期行为,Owner 审批 |
| **preferences** | 必须 `pending_review` | Owner 偏好,Owner 自己决定 |
| **prompt / role behavior 相关** | 必须 `pending_review` | 改 prompt 是 Owner 特权 |

### 新增状态:`active_candidate`

原状态机:`active / pending_review / deprecated / superseded`

新增 `active_candidate`(试用期):

```
active_candidate → 试用中,会被注入到 context pack(但加"试用"标记)
                ↓ N 次成功命中
            active(正式启用)
                
                ↓ 多次失败或长期未命中
            deprecated
```

晋升规则示例:

```python
def promote_active_candidate(memory):
    """active_candidate → active 的晋升判定"""
    if memory.success_count >= 3 and memory.failure_count == 0:
        memory.status = 'active'
    elif memory.failure_count >= 2:
        memory.status = 'deprecated'
    # 否则保持 active_candidate
```

### 冲突检测

新记忆写入前,查同 project + 同 layer + 标签重叠的现有记忆,让 PM 判断是否冲突。有冲突时,旧的标记 `superseded`,新的 `superseded_by` 指向旧 ID。

## 跟 LangGraph 的集成

### 角色调用前:build context pack

```python
def build_context_pack_for_role(state, role):
    project_id = state.task.project_id
    pack = ContextPack(task=state.task, prior_artifacts=state.artifacts)

    # 注入 active 记忆
    pack.project_facts = memory_store.query(
        project_id=project_id,
        layers=['facts', 'conventions', 'preferences'],
        status='active',
    )

    # 注入 active_candidate 记忆(带"试用"标记,角色知道是试运行)
    pack.candidate_memories = memory_store.query(
        project_id=project_id,
        layers=['facts', 'conventions'],
        status='active_candidate',
    )

    pack.relevant_history = memory_store.search_relevant(
        project_id=project_id,
        layers=['decisions', 'failures'],
        query=state.task.title + " " + state.task.description,
        top_k=5,
    )

    pack.role_skills = memory_store.match_skills(
        project_id=project_id,
        role=role,
        task_context=state.task,
        min_score=2.0,
        top_k=8,
        include_candidates=True,  # 包含 active_candidate
    )

    memory_store.track_usage(...)
    return pack
```

### 角色完成后:回填效果

```python
def task_complete_callback(task_id, outcome):
    used = memory_store.get_usage_records(task_id)
    for record in used:
        if outcome.success:
            memory_store.mark_helpful(record.id)
            # active_candidate 累积成功次数,达标自动晋升
            memory_store.try_promote(record.id)
        else:
            memory_store.mark_unclear(record.id)
```

## 单向 Markdown 导出(V1)

> **基于 codex review**:V1 不做双向同步,只做 DB → Markdown 导出。

```
┌─────────────────────────────┐
│  Postgres (真相源)            │
│  - 程序读写                    │
│  - 评分、检索、统计             │
│  - Curator 工作对象             │
└──────────┬──────────────────┘
           │
           │ 每日 cron 单向导出
           ▼
┌─────────────────────────────┐
│  Markdown 文件 (Git 仓库)     │
│  - 人类阅读                    │
│  - 版本追溯                    │
│  - **只读**,Owner 不直接改     │
└─────────────────────────────┘
```

**V1 不支持的事**:

- ❌ Owner 直接编辑 markdown 文件
- ❌ markdown → DB 反向同步
- ❌ markdown 跟 DB 双向校验

**Owner 想改记忆时,V1 阶段的做法**:

- 通过 pending_review 队列批准/拒绝
- 直接连 DB 执行 SQL(高级用法)
- 或者写一个 admin 脚本

**V2 再评估**:markdown → DB 导入(需要冲突处理、版本管理)。

## 检索升级路径

```
V1: 纯 SQL 全文检索 (Postgres tsvector)
V2: 加 pgvector (同一个 Postgres,加扩展)
V3: 混合检索 (embedding + 关键词 + 评分)
```

**关键**:用 pgvector 而不是 Pinecone / Qdrant,因为它**就在 Postgres 里**,不增加组件。

## 记忆系统 9 条铁律

```
1. 项目级严格隔离 (查询永远带 project_id,跨项目不允许)
2. 角色级隔离 (Developer skills 跟 Reviewer skills 完全分开)
3. 不可变 + 版本化 (不修改,supersede)
4. 按 layer 分级写入,不一刀切
   - failures/decisions: 可自动 active
   - facts/role_skills: 走 active_candidate
   - conventions/preferences/prompt: 必须 pending_review
5. 新增 active_candidate 状态作为"试用期",降低写入风险
6. 使用统计驱动 curator (用得多 + 成功 = 晋升 active 或加分)
7. V1 单向持久化 (DB → markdown,Owner 不直接编辑 markdown)
8. 失败比成功更重要 (失败立刻 distill)
9. Owner 是最终裁判 (pending_review 进审批队列)
```

## 工作量估算

| 模块 | 代码量 | 工作量 |
|---|---|---|
| Schema (SQL) | 60 行 | 1 小时 |
| Memory Service (Python) | 200 行 | 1 天 |
| Curator (Python) | 150 行 | 1 天 |
| Cron 调度 | 30 行 | 半天 |
| Markdown 同步 | 80 行 | 半天 |
| Pending Review UI (飞书 bot) | 100 行 | 半天 |
| **总计** | **~620 行** | **3-4 天** |

---

# Part VII:V1 完成后的演进路径

## V1 vs 终局的差距

V1 完成后是一个**半自治、固定路径的 multi-agent pipeline**,不是真正的 autonomous 系统。从 V1 到终局的关键演进:

| 终局原则 | V1 实现 | 演进方向 |
|---|---|---|
| PM 全程咨询,动态调度 | LangGraph 固定状态机 | conditional_edges 演化成动态 |
| 3-reviewer 跨模型 panel | 单 reviewer | V2 加 Panel + 一票否决 |
| 任务间并行,任务内串行 | 完整实现 | ✅ |
| 调度者纯确定性 | LangGraph 节点是 LLM | LangGraph node 是代码 + 调 LLM,架构上分得清 |
| 角色不直接说话强制中转 | state 传递 | ✅ |
| H 域自我改进 | 完全不做 | V2+ |
| 跨模型冗余 | 不做 | V2+ |

**关键收益**:LangGraph 的 conditional_edges 可以演化成动态调度,**不需要重写代码**。这是选 LangGraph 的核心价值。

## V2 预留方向

### Program 层(跨 repo 任务)

```yaml
program_id: login-v2
projects:
  - project_id: api
    task: add captcha backend
  - project_id: web
    task: add captcha frontend
```

新增角色:**Program PM**,职责:跨 repo 拆解、依赖识别、多 PR 一致性、发布顺序、最终验收。

### Reviewer Panel(V2 可选,不强制)

- 评估前提:V1 单 LLM Reviewer 跑稳几个月后,看是否真的需要 panel
- 如果做,**只在高风险场景启用**(改受保护路径、删大量代码),不是所有 PR 都 panel
- 注意:研究证据表明跨模型聚合无法消除 LLM 通病,慎重投入(详见 design-history.md)

### Arbiter

V2 可选。最强模型(Opus)处理 reviewer 分歧、PM / Architect 分歧、多次失败、高风险变更。

只在 F2 分歧仲裁链的"辩论仍不决"阶段才用,不作为常规步骤。

### 向量记忆

markdown 记忆稳定后,加 pgvector + embedding search + failure similarity search。

V2 启动条件:记忆条数 ≥ 几千。

### H 域自我改进(推迟到 V3+)

```text
推迟到 V3+,等业界数据成熟

V2 不做:
  - Skill 自演化
  - Prompt 自动改进提案
  - 软参数自动调整

V2 改为:
  - 完善 H 域数据收集(H1a/H1b/H4)
  - 给 Owner 提供更好的"看数据 → 改 prompt" 体验
  - Owner 改 prompt 走 B5 角色质量门验证
```

## V1.5 中间阶段

> 基于 codex review:不要在 V1 直接跳到 V2,中间有个过渡。

| 能力 | V1 状态 | V1.5 状态 | V2 状态 |
|---|---|---|---|
| Auto-merge | 关闭 | 低风险项目可开启 | 全面开启(配合 panel) |
| Markdown 同步 | 单向(DB → MD) | 单向(优化) | 双向(待评估) |
| Active candidate 晋升 | 手动配置规则 | 半自动 | 全自动 |
| Reviewer | 单 LLM Reviewer | 单 reviewer + self-consistency | (V2)高风险场景跨模型 |
| Owner 介入频率 | 每天看 | 每周看 | 月度 review |

**V1.5 入口标准**:V1 跑稳 1 个月,关键指标稳定。
**V1.5 → V2 标准**:V1.5 跑稳 2-3 个月。

## V2 不需要重写的部分

- LangGraph 状态图(只是加节点 + 改 conditional_edges)
- 记忆系统 schema(只是加 embedding 列)
- 角色契约(D1 词汇表)
- 项目并发模型
- 预算护栏机制

## V2 需要新增的部分

- Program-PM 角色(跨 repo 编排)
- 跨模型 reviewer 调用层
- Arbiter 角色
- Curator 自我改进逻辑
- pgvector + embedding

## V1 → V2 的判断标准

什么时候该启动 V2?

- V1 跑稳 ≥ 3 个月
- 月任务量 ≥ 30 个
- 单 reviewer 漏掉的问题已经能定性分析(说明有 V2 需求)
- 跨 repo 任务出现频率 ≥ 30%(说明需要 Program 层)
- 记忆条数 ≥ 几千(说明需要 pgvector)

---

# Part VIII:Owner 工作量与系统边界

## Owner 工作量(预期稳态)

| 触发 | 频率 | Owner 动作 |
|---|---|---|
| 任务派发 | 主动,按需 | 飞书发任务 |
| F5 升级请求 | < 3 次 / 周(健康指标) | 飞书读、回复决策 |
| Pending review 队列(记忆/skill) | 每周 1-3 次 | review 提案,approve / 修改 / 拒绝 |
| H1b 失败聚类告警 | 偶尔 | 看告警,决定是否改 prompt |
| 角色质量门 PR | Owner 主动 | 改 prompt → PR → 看 diff 报告 → merge |
| G1 预算硬上限解锁 | 罕见 | 决定是否释放 |
| 异常告警 | 罕见 | 看告警,判断要不要介入 |
| 定义新角色 / 改宪法 | 想做的时候 | 写 role.yaml / 写宪法 markdown,push 到 Git |

**目标**:稳态时 Owner 每周花在系统上的时间 **< 2 小时**。

## 系统边界条件

### 系统在以下情况下**优雅工作**

- 项目并发数 ≤ 10
- 单任务子任务数 ≤ 30
- 单任务迭代轮次 ≤ 10
- 单任务持续时间 ≤ 几天
- escalation 频率 < 3 次 / 周
- pending_review 队列 < 10 项

### 系统在以下情况**触发降级或 escalation**

- 死循环检测命中(F4)
- 预算硬上限(G1)
- API rate limit 满(G4)
- 系统能力空白(B 域识别不到合适角色)

### 系统**绝不应该**发生的情况(基础设施强制保证)

- 数据丢失(硬护栏)
- 安全漏洞合并(一票否决)
- 跨项目数据污染(项目隔离)
- 任务静默失败(必有 trace)
- Agent 修改受保护文件(D3 + CI 强制)
- 预算无限烧(G1 硬上限)
- Secret 进入代码库(gitleaks)

## Owner 心理建设

单人 + 高自动化野心 + AI 工具辅助的常见陷阱:

### 陷阱 1:完美主义

"不赶时间,把每个细节想清楚再开干"——半年过去还在写文档。

**解药**:每个 phase 定**硬时间盒**,1 周内必须跑通,不论多丑。

### 陷阱 2:技术贪婪

"反正有 AI 辅助,把 Langfuse、Inngest、Temporal、E2B 都上一遍"——维护负担压垮自己。

**解药**:每个 phase 跑稳 1 周,再加下一个组件。已经在文档里明确**不引入的工具清单**。

### 陷阱 3:AI 万能

"AI 帮我修就行"——核心代码不读懂,定时炸弹。

**解药**:核心代码(编排、状态机、failure handling)必须读懂能复述。AI 给的关键操作方案,第一次必须手动跑一遍。

### Owner 灾难演练 SOP

- **每月 1 次**:手动 kill 主进程,确认重启恢复
- **每月 1 次**:手动 kill Postgres,从 dump 恢复
- **每季度 1 次**:完整迁移演练(新机器从零部署)
- **每次大版本升级前**:在 staging 环境跑一遍

---

# Part IX:已知未解决问题

实现层后续需要展开的具体问题:

## 整体层

1. **PM 的 system prompt 怎么设计**:PM 这个角色的灵魂
2. **PM 的工具集**:PM 需要哪些工具(搜代码、查记忆、调子 agent 等)
3. **Claude Code 跟"角色"的关系**:Claude Code 是 Developer 的载体,还是底层 LLM 接口
4. **入口层飞书接入**:lark-oapi-python 怎么用,webhook 怎么处理
5. **Arbiter 角色的具体设计**(V2):跟普通 Reviewer 有什么不同

## 记忆层

6. **embedding 模型选哪个**(V2):OpenAI text-embedding-3-small / Voyage / 本地?
7. **pending_review 的 UI**:飞书消息卡片 还是 简单 web 页面?
8. **markdown 渲染格式**:是否要支持嵌入图表 / 链接到 PR?
9. **跨任务的"成功标签"**:任务成功了,哪些被使用的记忆算"功臣"?需要更细的归因
10. **Owner 直接编辑 markdown 时的冲突处理**:V2 才考虑(V1 是单向)
11. **Failure distill 的 prompt 设计**:PM 怎么写这个 prompt,关系到 distill 质量
12. **DB → Markdown 单向导出格式如何定**(新增):导出的 markdown 结构、命名、分组规则
13. **active_candidate 到 active 的晋升规则**(新增):多少次成功才晋升?跨任务还是跨周期?

## 工程层

14. **GitHub PR 状态查询**:CI 在跑、merge 冲突、approval_required 改动这些状态怎么映射到飞书通知
15. **Worktree 累积的清理**:7 天清理够不够?磁盘满了怎么办?
16. **Hermes-as-gateway 跟自写飞书的取舍**:具体省多少时间?入口故障怎么处理?
17. **跨模型 reviewer 的并发与超时**:3 个家族同时调,有一个慢/挂怎么办

## PoC 验证问题(新增,基于 codex review)

18. **LangGraph 是否满足 long-running CLI 任务恢复?**(见 Part IV.5)
19. **Claude Code 指定 worktree 执行的稳定性如何?**
20. **Claude Code 输出如何结构化解析?**
21. **PR_READY 到 MERGED 的人工/自动边界是什么?**:Owner 一键 merge 的 UX,失败时怎么标
22. **approval_required 文件变更如何审批?**:在 PR 上加 label?另开飞书审批流?

## 流程层(新增)

23. **escalation.md 的标准格式**:Phase 0B 就要定,避免后续重写
24. **events.jsonl 到 Postgres 的迁移路径**:Phase 0C 的具体迁移脚本
25. **task.yaml 的 owner_request 自然语言怎么解析**:需要 PM prompt 设计配合

---

# 附录:讨论历程与关键决策点

## 讨论的演进路径

整套设计经历了 **5 个阶段** 的螺旋上升:

### Stage 1:工具层探索

- 起点:"Hermes 是否能调 Claude CLI?"
- 探索 Hermes / ACP / Claude Code 计费模式
- 关键认知:6 月 15 日 Anthropic 计费拆分,TUI 模式保订阅、print/ACP 走 Agent SDK credit

### Stage 2:框架层探索

- 转向:"用 Claude 能实现多 agent 协作吗?"
- 业界框架对比(LangGraph / CrewAI / AutoGen / Anthropic Research)
- 关键认知:Orchestrator-Worker 模式是业界共识

### Stage 3:架构层成型

- 多次反复:从"AI 辅助工具"到"自治组织"的根本性认知升级
- 关键决策:调度者 vs PM 必须分离
- 关键决策:Runtime + PM 配合,不是替代

### Stage 4:能力体系完成

- 8 个能力域逐一过完(A → H)
- 并发模型定型:任务间并行 + 任务内串行(worktree 物理隔离实现)
- 12 条系统宪法落地
- "做什么"文档沉淀

### Stage 5:实现层启动

- Codex V1 方案对比 + 业界工具补全
- Hermes 真实定位澄清(自演化单 agent,非 multi-agent)
- 记忆机制实现层方案(否决"每角色一 Hermes",定 Postgres + Curator)
- 本完整文档整合

## 关键认知拐点

讨论过程中的**根本性认知升级**:

1. **每天 3 个任务≠任务量小**:这是"杠杆放大"的起点,不是"任务自动化"
2. **autonomous != 无人值守**:Owner 不在 loop 里 review,但始终在 loop 里改进系统
3. **调度者 vs PM**:基础设施 vs 应用,不是同一层
4. **"管理大脑"是错误命名**:用 Runtime / Orchestrator,避免跟 PM 混淆
5. **任务间并行,任务内串行**:用 worktree 物理隔离实现真正并行,不需要项目级锁
6. **质量来自结构化评估 + 硬护栏**:不是冗余对抗(LLM 错误高度相关,跨模型聚合无效)
7. **硬护栏 vs 软对齐**:数据丢失 / 安全在基础设施层强制,代码质量靠结构化评估
8. **H 域只沉淀数据,不自动改系统**:LLM self-evolution 在 2026 还不成熟
9. **codex V1 方案高质量,但缺成本护栏**:必须在 Phase 1 补
10. **Hermes 是单 agent 框架,不是 multi-agent**:借鉴设计,不引入软件
11. **LangGraph 是 V1 → 终局的桥梁**:conditional_edges 自然演化成动态调度
12. **"每个角色一 Hermes"是 trap**:违反 5 条架构原则
13. **记忆系统是周末项目**:~620 行代码,3-4 天工作量,不是大工程
14. **角色不直接调用,但可发 signals**:"硬约束 vs 偏好"边界要清晰
15. **A/B 灰度不适合小项目**:每天 3 任务样本量不够。golden dataset 才是务实做法
16. **预算护栏是终极防死循环**:其他多层防御都是冗余

## 关键决策点对照表

| 决策点 | 选择 | 关键理由 |
|---|---|---|
| 系统形态 | autonomous multi-agent 组织 | 不是 AI 辅助工具 |
| 编排框架 | LangGraph | 业界事实标准 + V1→V2 自然演进 |
| 角色执行 | Claude Agent SDK | Anthropic 官方推荐组合 |
| 状态存储 | Postgres | 一个组件解决多个问题 |
| 观测 | Langfuse 自部署 | MIT + OpenTelemetry 原生 |
| 隔离 | Git worktree | Claude Code 原生支持 |
| 入口 | 自写飞书 SDK(或 Hermes-gateway) | 1-2 天工作量,核心架构干净 |
| Hermes | **不引入** | 借鉴设计不引入软件 |
| 记忆机制 | Postgres + Curator 自实现 | ~620 行代码,可控 |
| 检索 | V1 SQL,V2 pgvector | 不增加组件 |
| Review Panel | V1 单 reviewer,V2 跨 3 模型 | 接口预留 |
| 部署 | 单机 docker-compose | 单人维护友好 |
| PM 实现模式 | 模式 2:逻辑常驻 + 状态持久化 + 按需 hydration | 跟 LLM 无状态本质匹配 |
| 项目边界 | 每个 Git 仓库 = 一个项目 | monorepo 当一个项目 |
| 项目隔离 | 完全隔离,无跨项目咨询 | 简单 + 安全 |
| 并发模型 | 任务间并行 + 任务内串行 | worktree 物理隔离已足够,不需要项目级锁 |
| 角色通信 | 角色不直接调用对方,但可发 signals;调度者读后决定 | 一致性 + 可控 + 不损失信息流 |
| 一票否决范围 | security + data_loss + 严重 bug | 不容忍数据损失 |

## 5 个核心反模式(避坑提醒)

1. **不要把工作流引擎当编排器**:Superset / dashboard / n8n 这类是"人操作多 agent",不是"调度者调度多角色"
2. **不要让管理 LLM 调度执行 LLM**:全 LLM 链路调试地狱、token 爆炸
3. **不要 GroupChat 多 agent 互相对话**:容易死循环,辩论只在仲裁场景用
4. **不要共享全局上下文**:每个 agent 独立上下文窗口才是 Anthropic Research 90% 提升的核心
5. **不要让 Monitor / Deploy 是 agent**:这些是基础设施,LLM 做实时监控和部署是定时炸弹

---

## 文档元数据

- 整合日期:2026-05-24
- 文档版本:**v2.4**(Phase 0A 开工前的设计收紧)
- 状态:**长期总纲完成,Phase 0A 开工 ready(所有 5 个开放问题已敲死)**
- 配套文档:
  - Phase 0-1 Execution Spec v2.4(开工施工图)
  - design-history.md v2.4(设计修订历史档案)
- 子能力总数:32

## 自测题(沉淀检验)

放下文档,凭记忆回答。题目分两组——

### 组 A:关于"现在的设计"(读完本文档应该能答)

1. 调度者和 PM 的区别是什么?为什么要分开?
2. 为什么任务间并行,任务内串行?worktree 在其中起什么作用?
3. 三层记忆的边界和写入者分别是什么?
4. Curator 打分公式的三个维度?为什么这么设计?
5. 失败提炼时为什么 PM 不能直接改记忆?
6. 为什么用 LangGraph?如果 LangGraph PoC 失败怎么办?
7. V1 → V2 哪些代码不需要重写?为什么?
8. 单人维护的 3 个陷阱是什么?分别怎么解?
9. Phase 0 为什么要拆成 0A / 0B / 0C?
10. V1 为什么不 auto-merge?Owner 不在 review loop 跟人工 merge 矛盾吗?
11. protected_paths 三级分别是什么?为什么 package.json 不能 hard_block?
12. active_candidate 状态解决什么问题?
13. signals_to_other_roles 字段允许哪些事?禁止哪些事?
14. F1 单 LLM Reviewer 的 rubric 有哪几个字段?哪个字段是一票否决?
15. "调度者控制 state"具体通过什么机制实现?

### 组 B:关于"为什么这么设计"(可能要查 design-history.md)

16. 为什么不用每个角色一个 Hermes?
17. "硬约束"和"偏好"的区别是什么?如何判断一条原则该是宪法级还是偏好级?
18. H 域为什么不做"自我改进"?unobservable learning 是什么?
19. 为什么不做 A/B 灰度发布?golden dataset 怎么替代它?
20. 为什么不做跨模型 reviewer panel?LLM 错误相关性是什么?
21. 压力测试的 4 个标准问题是什么?
22. 为什么 V1 不需要文件权限系统?底层天然隔离是什么?

**评分**:

- 组 A 答出 12+ 题 → 当前设计已经吃透,可以开工
- 组 B 答出 4+ 题 → 你能抵御未来重新犯错的诱惑
- 都达标 → 设计 + 决策理由都内化了

组 B 答不上来不要紧——它不阻塞开工,只是提醒你**未来想加某个"业界标配"前**,回去翻 design-history.md。
