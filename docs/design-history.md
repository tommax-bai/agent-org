# Autonomous Multi-Agent 研发系统 - 设计修订历史

> **文档定位**:设计决策历史档案
>
> 本文档记录主设计文档(autonomous-agent-system-design.md)的修订历史。
>
> **配套主文档**:autonomous-agent-system-design.md v2.4
>
> **何时翻这份文档**:
> - 想给系统加某个"业界标配",先来查一下是不是之前已经讨论过否决了
> - 想改某个看起来反直觉的设计,先来查一下是为什么这么设计的
> - 重构时,判断某条设计能不能删
> - 跟人(或未来的自己)解释为什么这么设计
>
> **不需要在以下场景读**:Phase 0A 开工写代码、日常使用文档查 API、新加角色 / 配置

---

## 文档结构

```
Part I:版本演进路线图           (一句话概览每次修订)
Part II:压力测试方法论           (元层经验总结,最值钱的部分)
Part III:详细修订日志            (每次修订的来龙去脉)
Part IV:被否决的设计清单         (汇总所有"看起来合理但故意不做"的设计)
```

---

# Part I:版本演进路线图

| 版本 | 日期 | 触发 | 核心修订 |
|---|---|---|---|
| v1.0 | 2026-05-24 | 整合初稿 | 8 能力域 + 10 宪法 + V1 路线 |
| v1.1 | 2026-05-24 | codex review | Phase 0 拆 0A/0B/0C, PoC 验证门, 不 auto-merge |
| v1.2 | 2026-05-24 | Owner 质疑宪法第 2 条 | 角色不直接调用但可发 signals |
| v1.3 | (并入 v1.4) | Owner 质疑自我进化 | H 域 self-evolution 删除 |
| v1.4 | 2026-05-24 | 4 次压力测试 + 重叠扫描 | 子能力 38→32, 多个虚高设计被砍 |
| v1.5 | 2026-05-24 | Owner 追问"控制权限" | 通信原则表述澄清(代码约定不是权限) |
| v1.6 | 2026-05-24 | Owner 追问 worktree 并发粒度 | 并发模型从项目级改为任务级(删 project lock) |
| v1.7 | 2026-05-24 | Owner 追问"大中小"判定 | C4 的"小中大"明确为 D5 severity,加可执行判定标准 |
| v2.0 | 2026-05-24 | Owner 提出 PM/Architect 现实世界分工 | **范式升级**:固定角色 → 动态角色(Orchestrator-Worker) |
| v2.1 | 2026-05-24 | Owner 追问角色创建脚手架 / LLM 辅助生成 | 主文档 B 域加"角色创建工程实践":模板 + 6 段 prompt 结构 + golden dataset 格式 + meta_prompts 启动门槛工具 |
| v2.2 | 2026-05-25 | 第二次 codex review + Owner 二次审视 | 一致性压平 + 8 条 codex 建议 + 4 个盲区补充 + 新增第 12 条宪法 |
| v2.3 | 2026-05-25 | Owner 问"AI 迭代下如何保证模块化" | 加"模块边界保护"小节:modular monolith + _internal/ + import-linter |
| v2.4 | 2026-05-26 | Phase 0A 开工前 Owner 跟 Claude 敲死 5 个开放问题 + 清掉 v2.0 没改干净的固定角色残留 | 删宪法第 12 条 autofix 档 / required_roles → role_sequence / security_or_data_loss_risk 重命名 / artifact 加 attempt 字段 / 角色配置方案 Y(is_orchestrator)/ 0B mock 边界明确 |

**累计影响**:节省 3000-5000 行代码,3 个月以上的弯路。

> **v2.0 不是表述精简,是架构升级**。前 9 次修订都是在简化(删 / 砍 / 精准化),v2.0 是改变核心范式。
>
> **v2.4 是 Phase 0A 开工前的最后一次设计收紧**——把过去几次修订没改干净的地方收拾掉,把 Spec 没收死的 5 个开放问题敲死,确保开工时所有文档一致。

---

# Part II:压力测试方法论(最值钱的部分)

回看 7 次修订(含元层修订),Claude 反复出现一个**根本模式**:

```text
1. Hermes 引入       → "业界招牌"     → 删
2. 宪法第 2 条       → "硬约束"       → 改
3. H 域 self-evolve  → "飞轮叙事"     → 删
4. B5 灰度 A/B       → "生产标配"     → 改
5. F1 跨模型 panel   → "研究表明"     → 改
6. 6 层防死循环      → "稳妥防御"     → 改
7. 通信原则表述      → "权威但模糊"   → 改
```

**共同问题**:Claude 倾向于用"业界标准 / 生产标配 / 研究表明"这类术语**包装未经验证的设计选择**。

## 压力测试的 4 个标准问题

对任何"业界 X / 标配 Y / 研究表明 Z"的设计,问:

```
1. 这是真验证过的实践吗?有几个生产案例?
2. 在我每天 3 个任务的场景下成立吗?
3. 单人维护下,这个设计的成本/收益怎么样?
4. 如果删掉这条,系统会变怎样?
```

每次问完这 4 个问题,有显著比例的"业界标配"会暴露为虚高设计。

## 关于表述的元教训(v1.5)

除了"设计虚高",还有"**表述模糊**"这个独立问题:

写"控制权 / 决定权 / 标配"这种**听起来权威但缺乏机制**的描述时,要警惕——它可能让人误以为有保护层但实际没有,或反过来误以为系统比实际更复杂。

精确的表述应该是:"**通过 X 机制保证 Y**",不是"X 掌握 Y 的决定权"。

## 关于"混合方案"的元教训(v2.2)

第 12 次"业界标配陷阱"出现在 v2.2 修订过程中:

```
codex 原提案:signal 加 risk_class enum + 关键词匹配兜底
  - codex 出于"想要硬护栏"的合理动机
  - 但兜底机制(关键词匹配 LLM 输出)本身不可靠

Claude 准备接受 codex 的方案
  - 因为"混合方案听起来稳妥"
  - 没真审视关键词对 LLM 输出的有效率

Owner 反问:"通过关键字能匹配的概率会很低?"
  - 一句话戳破

Claude 二次审视:
  - 反例 1: "this migration changes the user table without backup"
    → 关键词没有 backup
  - 反例 2: "overwrite existing records when conflict"
    → 关键词没有 overwrite
  - 结论:LLM 写 signal content 的方式千变万化,关键词抓不住
```

**元教训**:

> **"混合方案"听起来稳妥,但如果兜底机制本身不可靠,加上去反而是噪声。**

要么完全依靠 LLM(明确告诉它什么时候用 + Owner 通过 dashboard 监督)。
要么完全依靠确定性代码(任务级 mandatory rules,基于明确的输入)。

**混合,只在两个机制都可靠时才有意义**。

这也是宪法第 12 条的来源——v2.2 加入"LLM 输出 + 确定性兜底"原则,强调"兜底机制本身必须可靠"。

## 关于"列工具菜单"的元教训(v2.3)

第 13 次反问出现在 v2.3 修订过程中:

```
场景:Owner 问"AI 迭代下如何保证模块化"
Claude 反应:列 6 层防御工具(import-linter / _internal / Protocol / 架构测试 / prompt / pre-commit)
Owner 反问:"这一堆防御,太冗余了,最重要最基本的会是哪个?"
```

Claude 反复犯的错:**列工具菜单当作"全面回答"**。但 6 个工具的真实关系是:

```
真正最基础:_internal/ + __init__.py(public API 显式化)
            └── 是其他所有工具的前提

第二层:    prompt 引导 + import-linter
            └── 一个事前,一个事后,组合够用

可以去掉:  Protocol(V1 进阶)、架构测试(linter 覆盖了)、pre-commit(CI 覆盖了)
```

**元教训**:

> **列工具菜单 ≠ 给出方案**。
>
> 真正的方案必须说清楚:
> - 哪个是基础(其他工具的前提)
> - 哪个是衍生(可以延后)
> - 哪个是冗余(可以去掉)
>
> 没有这种区分,看起来"全面"的列表反而是另一种"业界标配陷阱"。

跟 v2.2 的"混合方案陷阱"互补——一个是"机制不可靠还要加",一个是"工具太多没说清依赖"。两者本质都是"看起来稳妥但实际给不出方案"。

## 关于"流量小≠系统小"的元教训(v2.3)

同一次修订里 Claude 还犯了另一个错:

```
场景:讨论该不该拆微服务
Claude:"你每天 3 任务,流量小,不需要微服务"
Owner 纠正:"每天 3 任务是承载的并行任务量,不是系统本身"
```

**元教训**:

> **"流量小"≠"系统小"**。
>
> 不要用工作负载的规模反推系统本身的规模。
> 系统规模由**功能丰富度**决定,不由**流量**决定。
>
> agent-org 每天跑 3 任务还是 300 任务,系统本身的代码复杂度是一样的。
> 中型系统(5000-10000 行)该怎么设计,跟流量无关。

这个错出现过很多次(回头看 13 次修订日志),每次都需要 Owner 纠正。值得反复提醒未来的 Claude。

## 关于"多层保护是设计味道"的元教训(v2.4)

第 14 次反问出现在 v2.4 修订过程中:

```
场景:Q3 讨论 PM 输出 list 顺序的强制
Claude 反应:三层保护
  - 字段名 role_sequence(语义层)
  - 每个 item 加 step: N(结构层)
  - validator 查 step 连续(校验层)
Owner 反问:"多层的设计,大概率是设计有问题,要谨慎"
```

Claude 重新审视后发现:层 1(字段名)和层 2(step 字段)在干同一件事
——告诉 LLM 顺序重要。两层都需要 = 任何单独一层都不够 = **顺序没有
单一事实源**。

正确做法是把"sort"和"content"拆开到每个 item 的独立字段:
- step 字段是顺序的唯一来源
- role_id 字段是内容
- list 位置不再 load-bearing(打乱也无所谓,dispatcher 按 step 排序)

从 3 层退化到 1 层(结构层),反而更清晰。

**元教训**:

> **多层保护 / 防御性设计 / 冗余兜底,大概率是设计本身有问题**。
>
> 通常根因:
> 1. 数据结构没拆干净(同一信息在多个字段表达)
> 2. 边界不清(谁负责什么没定)
> 3. 责任分配错位(角色 A 该做的事推给 framework 兜底)
>
> 修方案的方向是**合并到单一事实源**,不是堆更多层。
>
> 校验/格式合法性不算"层",那是基本卫生(schema 校验输入合法 ≠ 多层保护)。
>
> 真的需要多层的场景(罕见):不同维度的需求(安全 + 性能 + 可用性)各有
> 独立保护——这不是同维度的冗余。但默认假设是"我堆多层 = 我没想清楚"。

跟 v2.2"混合方案陷阱"和宪法第 12 条同源——都是"职责分清,不要让一个组件
偷偷帮另一个组件擦屁股"。v2.4 把宪法第 12 条进一步收紧(删 autofix 档),
就是这条教训的体现。

## 给未来的自己

如果 3 个月后你想给系统加某个"业界标配",**先来这份文档查**——很可能它已经被否决过了,而你忘了为什么。

如果你跟新的 AI 协作设计,**把 Part II 的 4 个问题当作标准武器**。让 AI 每次给你"看起来稳妥"的设计时,先回答这 4 个问题。

特别地:

- 看到"混合方案"(LLM + 兜底)时,问:**兜底机制本身可靠吗?**(v2.2)
- 看到"列工具菜单"时,问:**哪个是基础,哪些是衍生,哪些冗余?**(v2.3)
- 看到"流量小所以系统小"时,问:**系统规模真的由流量决定吗?**(v2.3)
- 看到"多层保护"时,问:**为什么单一层不够?是不是该合并到单一事实源?**(v2.4)

---

# Part III:详细修订日志

### v2.4(2026-05-26):Phase 0A 开工前设计收紧 + 固定角色残留清理

**起因**:Owner 决定 Phase 0A 开工前,把 Spec 没收死的 5 个开放问题敲死,
顺便清掉 v2.0 没改干净的"固定角色"残留。

**讨论过程**:Owner 和 Claude 一个一个聊,每个问题给完整论据 + 真实数据
+ 副作用 + 没想清楚的。详见对话存档(memory: project-discussion-state-2026-05)。

**5 个 Q + 方案 Y 的修订**:

#### Q1: validator 失败回路 → 删 autofix 档

**修订前(v2.2)**:三级处理 autofix / retry / fatal。
- autofix: validator 自动补漏(如漏了 mandatory role 就自动加)
- retry: PM 重做
- fatal: escalate

**修订后(v2.4)**:两级处理 RETRY_PM / FATAL。删 autofix。

**Owner 论据**:
> "两个东西负责同一件事情,职责会变得混淆。validator 不替 PM 补漏,
> 只 retry 或 escalate。"

深层理由(Claude 复盘后认同):
1. autofix 让 LLM 失败模式被掩盖 → Owner 看不见 → 改不动 PM prompt → 系统不进化(违反第 10、11 条)
2. 模糊职责边界(validator 干了 PM 的活,违反第 4 条 Orchestrator-Worker)
3. 兜底凭模板/policy 补漏,这俩变更时可能补错(已否决清单同源问题)

**升级为普遍原则**:Owner 决定把这条做成宪法第 12 条的修订
(从"autofix 优先,retry 次之,escalate 最后" → "只 retry 或 escalate"),
影响系统**所有** LLM 输出 + 确定性兜底场景。

#### Q2: artifact.content 校验边界 + Reviewer 字段重命名

**Q2 主体**:
- 角色 runner **出口**(role 返回时)用 schema 校验 artifact.content
- `orchestrator/dispatcher/` 和 `orchestrator/artifact/` **完全不解析 content**,当 dict / JSONB 传
- 模块边界清晰:加新角色不用改 dispatcher,只要新角色实现 protocol + 给个 schema 文件就行

**Reviewer 字段重命名**:
- 原名 `security_or_data_loss_risk: bool` 描述风险**类型**
- 但系统真正在乎的是**效果**(必须 escalate)
- 出现新类别(合规、稳定性)时旧名字塞不下
- 改为 `must_escalate_to_owner: bool` + `escalation_reason: string`
- schema 描述里列五类触发条件(安全/数据/合规/稳定性/不可逆架构变更),写进 Reviewer prompt

Owner 原话:
> "security_or_data_loss_risk 这个名字是不是不太好,其实是需要报告的问题?"

#### Q3: 同 subtask 内角色排序 → role_sequence(step + role_id 结构)

**修订前(v2.3)**:`required_roles: [architect, developer, reviewer]` plain list,
list 位置 = 执行顺序(隐式)。

**修订后(v2.4)**:
```yaml
role_sequence:
  - step: 1
    role_id: architect
  - step: 2
    role_id: developer
  - step: 3
    role_id: reviewer
```

list 位置无语义,dispatcher 按 step 排序。

**讨论过程**(展示了"多层设计是设计味道"原则的产生):

第一次 Claude 提"三层保护":字段名 + step 字段 + validator。Owner 反驳
"多层的设计大概率是设计有问题",Claude 复盘发现层 1(字段名)和层 2
(step 字段)在干同一件事 → 单一事实源没有 → 退化为只用 step 字段
一层即可。

这次反驳产生了 Part II"多层保护是设计味道"的元教训。

#### Q4: needs_changes 时 artifact 处理 → 追加 attempt,不覆盖

**修订**:
- artifact 加 `attempt: int` 字段(从 1 起)
- 重试产生新 attempt,老的不删,加 `superseded_by` 字段追溯
- dispatcher 取"当前 artifact" = 同 (subtask, role) max(attempt)
- **硬上限**:同 (subtask, role) attempt 上限 2 次,第 3 次强制 escalate
- 新事件:`ATTEMPT_LIMIT_REACHED`

理由:
- 宪法第 9 条要求可追溯,覆盖了就追溯不了
- Phase 4 记忆系统需要历史数据
- 存储成本可忽略

#### Q5: Phase 0B mock 边界 → 只 PM 真 LLM,其他 mock

**修订前**:Spec F.3 模糊说"必须有至少 PM 跑通真实 LLM"。

**修订后**:0B 阶段**只 PM 真 LLM,其他角色全 mock**。

理由:
- 0B 目标是验证状态机 + dispatch validator + signals + attempt 上限
- 这些跟 LLM 输出**内容**无关,只跟**结构**有关
- Reviewer 跑真 LLM 看 mock Developer 的固定数据没有验证价值
- Phase 1 才把其他角色换成真 LLM,集中打磨 prompt

#### 方案 Y: 角色配置(framework 不预设角色)

**起因**:Owner 问"会预设 reviewer 角色的原因是什么?角色应该是用户运行时配置定义的么?"

Claude 一开始建议"PM 是 framework,其他角色是配置",但仔细检查主文档后发现:
- 宪法第 5 条原话:"角色由 Owner 配置,不固定数量"
- 主文档原意是把 PM 视为一种**特殊职责的角色**(任务编排者),不是 framework
- 但 spec 把 PM/Developer/Reviewer 标 `required: true` 是说一套做一套
- D 域出现"V1 内置的"措辞是 v2.0 没改干净的痕迹

**修订(方案 Y)**:
- 所有角色(包括 PM)都是 Owner 配置,framework 不预设任何角色
- 删除 `required: true / false` 概念
- framework 唯一硬约束:project.yaml 里恰好一个角色标 `is_orchestrator: true`(担任 PM 职责)
- `roles/` 目录改为 `examples/role_templates/`(参考模板)
- Owner 启动新项目时,从 examples 拷贝想要的到 `projects/<x>/roles/` 改
- 同步删除 D 域"V1 内置的"措辞残留

**Claude 在这一步差点犯错**(后被 Owner 纠正):
- 第一反应是给"方案 X/Y/Z 三个选项",Owner 反驳:
  > "SHIT,你这个回答就是在找补之前的问题,说错了就说错了,直接说对的就行,还让我选择干什么?"
- 这条反馈产生了 user-discussion-style memory:"被反驳认错快,不要找补"

**修订内容**:

```text
1. 主文档 Part III 宪法第 12 条:删 autofix 档,只 retry/escalate
2. 主文档 Part II A 域 PM 输出契约:required_roles → role_sequence
3. 主文档 Part II A 域 dispatch_plan validator:删 autofix 三级,改两级
4. 主文档 Part II B 域:V1 默认角色清单段重写为方案 Y(is_orchestrator)
5. 主文档 Part II D 域:删"V1 内置的"措辞 + Reviewer schema 重命名 + artifact 加 attempt
6. 主文档 Part II F 域:Reviewer rubric 重命名
7. 主文档 Part V Phase 0B/1 完成标准:同步新字段 + mock 边界明确
8. spec phase-0-1-execution-spec.md:全文同步(A.2 目录 / A.3.x role.yaml / A.4 完成标准 / B.4-B.12 / F.3 / vocabulary.md)
9. design-history.md:加 v2.4 修订条目 + Part II 加"多层设计是设计味道"教训
10. INDEX.md:版本号 v2.3 → v2.4 + 关键决策表加新行
11. coding-subagent-prompt.md:引用第 12 条措辞更新 + 已否决清单加 2 条
```

**新增元层教训**(进 Part II):

> **多层保护 / 防御性设计 / 冗余兜底,大概率是设计本身有问题**。
>
> 修方案的方向是合并到单一事实源,不是堆更多层。

详细见 Part II"多层保护是设计味道"段。

**实施层影响**:

- event.schema.json: 加 `PLAN_RETRY_REQUESTED` / `ATTEMPT_LIMIT_REACHED` / `PLAN_VALIDATION_FATAL`,删 `PLAN_AUTOFIXED`
- role.schema.json: 加 `is_orchestrator: boolean`
- project.schema.json: 加约束"恰好一个 role 标 is_orchestrator: true"
- pm_dispatch_plan.schema.json: 用 role_sequence 结构
- schemas/artifact_content/: 新增子目录,按 type 分 schema(code/design/review/dispatch_plan/analysis)
- Phase 0A 目录结构: `roles/` → `examples/role_templates/`
- 平均成本影响: +$0.3-0.5/任务(autofix 删除后,类型 A 错误现在 retry 而非静默修复)

**元层认知**:

```
v2.4 是 Phase 0A 开工前的最后一次设计收紧。

v2.0-v2.3 是"在主文档层面做修订",每次都有"主文档说一套、spec 没改干净"
的残留(比如 spec 里 roles/ 预建 4 个、required: true 标记)。v2.4 把这些
残留一次性清掉,确保开工时所有文档一致。

讨论模式上,Owner 引入了几条新原则:
  - 一次深聊一个问题(批量太泛会被反驳)
  - 说人话(默认自然段,不堆五段式表格)
  - 多层设计是设计味道(堆 2 层以上保护要警惕)
  - 被反驳认错快(不要找补)

这些原则记进 CLAUDE.md 和 memory,以后所有协作都按这个走。
```

---

### v2.3(2026-05-25):模块边界保护(modular monolith)

**起因**:v2.2 完成"一致性压平"后,Owner 在工程实施层面问了两个有连贯性的问题:

1. "服务是否需要拆分微服务?"(架构形态)
2. "如果不物理隔离,如何在迭代中,AI 能做到保障模块化"(模块边界腐烂)

**Claude 的反复犯错(被 Owner 纠正)**:

```
错误 1:用"每天 3 任务"作为系统规模论据反对微服务
  被 Owner 纠正:"每天 3 任务是承载的并行任务量,不是系统本身"
  → Claude 把"流量小"等同于"系统小",这是错的
  → 系统本身复杂度由功能丰富度决定,不由流量决定
  → 中型系统(5000-10000 行)该不该拆,需要真严肃讨论

错误 2:列 6 层防御工具,看起来"全面"但没说清楚哪个是基础
  被 Owner 纠正:"这一堆防御,太冗余了,最重要最基本的会是哪个"
  → Claude 列工具菜单,但没说依赖关系
  → 真正最基础的是"public API 显式化"(_internal/ + __init__.py)
  → 其他工具都是这个基础上的衍生
```

**修订内容**:

#### 1. 架构形态决策(主文档 Part IV 末尾新增"模块边界保护"小节)

```text
✅ modular monolith(物理单体,逻辑严格模块化)
❌ 不拆微服务(单人项目过度工程)
❌ 不拆 git 仓库(单仓 + 内部模块化)

理由:
  - 单体的真问题(测试慢、模块腐烂、改动面大)是真的
  - 微服务的代价(网络通信、分布式事务、运维基础设施)对单人项目过大
  - modular monolith 是中型系统的甜蜜点
```

#### 2. V1 模块边界保护最小集

```text
1️⃣ _internal/ + __init__.py(基础,最重要)
   - 每个模块 _internal/ 子目录放私有实现
   - __init__.py 显式 export public API
   - 是其他保护手段的前提

2️⃣ coding-subagent-prompt 加"模块边界纪律"段
   - 5 条具体规则
   - 让 AI 写代码时主动遵守
   - 减少违规代码产生

3️⃣ importlinter.cfg 强制 enforcement
   - CI 跑 lint-imports
   - 跨模块 _internal 访问被拦截
   - 兜底兜底
```

#### 3. V1 不做的(避免过度工程)

```text
❌ 完整 Protocol/ABC 体系(V1.5 视情况)
❌ 架构测试(import-linter 已覆盖)
❌ pre-commit hook(CI 已覆盖,只是反馈早一点)
❌ 模块版本号 / 独立打包(过度抽象)
```

#### 4. 跟宪法第 12 条的关系

```text
v2.2 第 12 条:LLM 输出 + 确定性兜底

v2.3 模块边界保护正是第 12 条在"开发流程"上的应用:
  LLM 输出 = AI 写的代码(可能违反边界)
  确定性兜底 = import-linter / _internal 约定

跟 dispatch_plan validator 设计哲学完全一致。
```

#### 5. 落地文档

```text
✅ 主文档 Part IV 加"模块边界保护"小节(~120 行)
✅ Spec Phase 0A 目录结构升级(orchestrator/ 子模块 + _internal/)
✅ Spec Phase 0A 新增 importlinter.cfg 模板
✅ Spec Phase 0A 完成标准加 4 项
✅ coding-subagent-prompt.md 加"模块边界纪律"段
✅ Phase 0A 加 docs/module_boundaries.md
```

**Part II 新增元教训(第 13 个反问)**:

> **列工具菜单 ≠ 给出方案**。
>
> 真正的方案必须说清楚:
> - 哪个是基础(其他工具的前提)
> - 哪个是衍生(可以延后)
> - 哪个是冗余(可以去掉)
>
> 没有这种区分,看起来"全面"的列表反而是另一种"业界标配陷阱"。

也加一条:

> **"流量小"≠"系统小"**。
>
> 不要用工作负载的规模反推系统本身的规模。系统规模由功能丰富度决定。

这两个教训会反复出现,值得长期记忆。

---

### v2.2(2026-05-25):一致性压平 + codex review 整合

**起因**:Owner 把 v2.1 设计交给 codex 做第二次独立 review。codex 提出 8 条建议(P0/P1/P2 三档),Owner 和 Claude 二次审视发现 4 个盲区,合并整合为 v2.2。

**核心洞察**(来自 codex):

> "主设计已经升级到动态角色范式,但 V1 路线、Phase 0B、部分状态机描述仍残留固定角色范式。"

v2.0 范式升级时**没改干净**——主架构是 PM_PLANNING + DISPATCH 循环,但 V1 路线和 Phase 0B 还写着 `PM → Architect → Developer → Reviewer`。这是 codex 抓到的关键不一致。

**修订内容**:

#### P0 类(必改,8 条 codex 直接采纳)

1. **全文消除固定角色流程**
   - V1 目标:改为 PM_PLANNING + DISPATCH 循环
   - Phase 0B 状态机:CREATED → PM_PLANNING → DISPATCH → ROLE_EXECUTING → DISPATCH → ...
   - Architect 只能作为示例角色出现,不能出现在状态机骨架

2. **新增 Dispatch Plan Validator**(A 域和 B 域之间)
   - PM raw plan → validate_dispatch_plan() → normalized_dispatch_plan → DISPATCH
   - 确定性代码,不调 LLM
   - 校验规则:role_id 存在、必须有 developer/reviewer、mandatory rules 强制、依赖无环等

3. **新增 dispatch_policy.yaml**(B 域)
   - mandatory_role_rules:任务关键词 / 路径模式 → 强制角色
   - pm_deviation_policy:PM 偏离权限
   - exceptions:Owner 维护的例外清单
   - 优先级:mandatory > protected_paths > role_groups template > PM discretionary

4. **signal schema 加 immediate_escalate_required**
   - 替代 codex 原方案的 risk_class + 关键词匹配兜底(Owner 反问后改进)
   - 完全交给 LLM 判断,但必须填 reason
   - 任务级硬护栏由 dispatch_policy 提供;immediate_escalate 只处理任务中突发风险

5. **核心角色 artifact 子 schema**(D 域)
   - PM: dispatch_plan
   - Developer: code_patch
   - Reviewer: review
   - Architect: design
   - Security Reviewer: security_review(可选,推荐)
   - 新自定义角色 artifact.content 可先自由格式,稳定后加 schema

6. **State/Event/Artifact/Memory 分层**(新 Part V.5)
   - task_state: LangGraph checkpoint,可变,恢复用
   - event_log: Postgres task_events append-only,审计真相源
   - artifact_store: runs/ + Postgres metadata,不可变
   - memory: Postgres memory_items,可变(版本)
   - markdown: 派生物,不作为写入源
   - PR/branch: 交付物

7. **Phase 4 拆为 4A/4B**
   - 4A (1 周):可用记忆(decisions + failures + 手动 active + context_pack + 单向导出 + H1b 失败聚类)
   - 4B (后续):记忆治理(Curator cron + Pending Review 飞书 + 自动 active)
   - V1 完成 = Phase 4A 完成(4B 不阻塞)

8. **worktree 表述修正**
   - 改为"工程隔离,不是安全沙箱"
   - Phase 2 加 executor 最小保护(working_dir / 环境变量白名单 / 不传 DB URL)
   - Docker / microVM sandbox 推迟到 V2

#### P0 类(盲区补充,5 条)

9. **Validator 三级处理**(autofix / retry / fatal)
   - autofix:漏 reviewer/漏 developer/依赖顺序 → 自动补全
   - retry:不存在 role_id / 循环依赖 / task_type 错 → 让 PM 重试(上限 1 次)
   - fatal:retry 仍失败 / PM 重复同样错 → ESCALATED_TO_OWNER

10. **dispatch_policy 加 Owner 例外清单**
    - keyword 误报的逃生口
    - Owner 持续 tune 的地方

11. **Validator 修改透明,记 PLAN_AUTOFIXED 事件**
    - PM 不知道修改了什么(LLM 不"学习")
    - Owner 通过 dashboard 看到模式 → 改 PM prompt 或 dispatch_policy

12. **新增第 12 条宪法**:LLM 输出 + 确定性兜底
    - LLM 输出 = 起点,不是终点
    - autofix 优先,retry 次之,escalate 最后
    - 兜底机制必须可靠;不可靠的兜底反而是噪声

13. **删除 risk_class + 关键词兜底设计**
    - 这是 Owner 反问 codex 的"关键词匹配兜底"后,Claude 二次审视发现的问题
    - 替换为 immediate_escalate_required boolean
    - 详见下方"v2.2 元教训"

#### P2 类(文档卫生,1 条)

14. **术语和版本统一**
    - 文档头部 v2.0 / v2.1 / v2.2 残留全部统一为 v2.2
    - "10 条系统宪法" → "12 条系统宪法"
    - H 域旧名"自我改进" → "数据沉淀与 Owner 改进辅助"
    - Phase 0A 目录结构同步 v2.2(加 dispatch_policy.yaml 等)
    - Spec 文档同步

#### Part D(meta-lesson,1 条)

15. **v2.2 元教训**:"混合方案 ≠ 更好"

   - codex 原提案:signal 加 risk_class enum + 关键词匹配兜底
   - Owner 反问:"通过关键字能匹配的概率会很低?"
   - Claude 二次审视:**正确**——LLM 写 signal content 的方式千变万化,关键词匹配根本抓不住实质风险。
   - 修订:删 risk_class + keyword 兜底,改用 immediate_escalate_required boolean
   
   **元教训**:
   ```
   "混合方案"(LLM 判断 + 关键词兜底)听起来稳妥,
   但如果兜底机制本身不可靠,加上去反而是噪声。
   
   要么让 LLM 全权判断(明确告诉它什么时候用,Owner 通过 dashboard 监督滥用),
   要么用确定性硬护栏(dispatch_policy mandatory_role_rules,任务级硬规则)。
   
   混合,只在两个机制都可靠时才有意义。
   ```
   
   这是第 12 次"业界标配陷阱"——Claude 接过 codex 的方案,加上"关键词兜底"听起来标准,但没真审视它对 LLM 输出的有效率。如果不是 Owner 反问,就这么写进去了。

**修订规模**:约 1200 行 diff
- 主文档:~750 行净增(3415 → 4165 估算)
- Spec:~230 行净增
- design-history:~200 行净增

**没有改的核心(继续稳定)**:
- 12 条宪法的核心精神(隔离、autonomous、Owner 不在 review loop)
- 工具栈(LangGraph + Postgres + Claude Agent SDK + Git worktree)
- E 域记忆设计核心
- F 域质量门设计核心
- G 域成本管理
- 已否决设计清单(Part IV)

**接下来**:Phase 0A 实际动手。Owner 已经验证设计 12 次,不应该再讨论更多。

---

### v2.1(2026-05-24):角色创建工程实践

**修订前(v2.0)**:
v2.0 完成动态角色范式升级,但**没说 Owner 实际怎么加角色**。仅有 B5 角色质量门的抽象描述。

**修订后(v2.1)**:
主文档 B 域加"角色创建的工程实践"详细段落,定义:

```text
1. roles/_template/ 模板目录(cp -r 起步)
2. system_prompt.md 6 段标准结构
3. golden_dataset case 格式约定
4. meta_prompts/ LLM 辅助生成(启动门槛工具)
5. CI 模板
6. V1 不做的事(避免过度工程)
```

**起因**:Owner 沉淀 v2.0 时反问:
1. "B5 角色质量门让我在考虑,是否有必要建立一个 Agent 创建的脚手架?"
2. "system_prompt 结构 / golden dataset 格式 这两部分,其实也是需要借助 LLM 能力来生成的,人工撰写难度比较高"

**问题分析**:

v2.0 范式让"加角色"成为 Owner 常规操作,但:
- 人工从零写 system_prompt:门槛高,要懂 prompt engineering
- 人工写 golden dataset:5-30 个 case,几小时工作量
- 没有标准结构 → 不同角色的 prompt 风格不一致 → B5 角色质量门难做

**核心设计选择**:

| 选项 | 评估 |
|---|---|
| A: 不做任何工具,Owner 自己去 Claude.ai 问 | 太原始,meta prompt 不能沉淀 |
| B: meta_prompts 启动门槛工具 ✅ | 半天工作量,80% 价值 |
| C: 完整 CLI 工具 (`agent-org new-role`) | V1 阶段过度工程,角色数量不够多 |

选 B。

**meta_prompts 的定位**:

```text
是:启动门槛工具(让 Owner 从空白页面变成"有第一版可以改")
不是:一键自动化(生成结果必须 Owner review 后才提交)

工作量:
- 2 个 meta prompt 文件(50-100 行 markdown)
- 2 个 Python CLI 包装(~50 行)
- 总共半天
```

**演化路径**:

```text
V1:    模板 + meta_prompts + 手工生成
V1.5:  根据 V1 真实加角色频率,看是否需要 CLI 工具
V2:    考虑 role hub(可分享 / 复用角色配置)
V3+:   多人协作的角色管理
```

**元教训**:

这是 11 次修订里**最务实的一次**——不是删功能、不是改架构,是**补足 v2.0 之后真实出现的 Owner 操作门槛**。

Owner 这个反问的价值在于:**它指向了 v2.0 后被忽略的"日常使用流程"**。设计文档容易把架构写清楚,把"日常怎么用"写糊。v2.1 补上这个空白。

---

### v2.0(2026-05-24):范式升级 — 固定角色 → 动态角色(Orchestrator-Worker)

**修订前(v1.x)**:
- 固定 4 个角色:PM / Architect / Developer / Reviewer
- 固定状态机流程:PM_ANALYZING → ARCHITECT_REVIEWING → IMPLEMENTING → REVIEWING
- PM 做"任务拆解",Architect 是 reviewer
- A3 子能力强制 Architect 复核

**修订后(v2.0)**:
- 角色数量由 Owner 配置(任意,不固定 4 个)
- 状态机改为 PM_PLANNING + DISPATCH 循环
- PM 只做业务拆解 + 角色调度,不做技术决策
- Architect 是 Owner 可配置的一种角色,不是 reviewer

**起因**:Owner 追问"PM/Architect 分工怎么处理?"指出 v1.x 设计跟现实世界不一致——现实公司 PM 做业务拆解 + 人员组织,Architect 做系统设计 + 系统任务拆解,职责完全不同。

**问题分析**:v1.x 把 PM 设计成"既做业务理解也做系统拆解",把 Architect 降级为 reviewer。这有两个问题:

1. **跟现实世界不一致**:Owner 看着别扭,新加角色困难
2. **跟业界 best practice 不一致**:Anthropic 2025 multi-agent research 推荐 Orchestrator-Worker 模式(主 agent 拆解调度,子 agent 执行)

**业界证据**:

- Anthropic Multi-Agent Research (2025):"我们发现 orchestrator-worker 模式比 peer-to-peer 多 agent 协作效果好"
- Cognition (Devin) / Cursor:都是单一编排者(planner) + 多个 worker agent
- AutoGen / CrewAI 的固定角色组在新任务类型上表现差(论文 2025 多次提到)

**修订内容**:

1. **PM 重新定义**:任务编排者(业务拆解 + 角色调度),不做技术决策
2. **角色清单灵活化**:Owner 在 project.yaml 配置任意数量角色
3. **role_groups 模板**:Owner 配置"任务类型 → 默认角色组",PM 用模板作为起点可加减
4. **role_invocation_protocol**:所有角色统一调用协议(input/output schema)
5. **状态机改造**:PM_PLANNING + DISPATCH 循环,不再写死 PM→Architect→Developer→Reviewer
6. **A3 重新定义**:从"拆解 + Architect 复核"改为"业务拆解 + 角色调度"
7. **宪法新增第 5 条**:"角色由 Owner 配置,不固定数量"(原 10 条扩展为 11 条)
8. **B4 改造**:角色选择由 PM 在业务拆解时做(基于 role_groups 模板)

**关键洞察**:**V1 架构 = 终局架构**。固定角色范式在 V2 必然要改成动态,这意味着 V1 会重写。v2.0 让 V1 直接用动态范式,跳过这次重写。

**潜在风险**:

| 风险 | 缓解 |
|---|---|
| PM 责任变大,可能不稳定 | system_prompt 写仔细 + 强制走 role_groups 模板 + B5 角色质量门重点验证 PM |
| PM 调用角色不一致 | Owner 在 project.yaml 提供模板,PM 偏离模板要发 signal |
| 角色协议变化要改所有角色 | role_invocation_protocol 在 v2.0 定型,后续兼容性优先 |
| V1 实现复杂度上升 | LangGraph conditional_edges 本来就支持动态调度,实现成本可控 |

**实施层影响**:

- A 域:PM 输出 schema 重写(加 business_breakdown / required_roles / role_dispatch_notes)
- B 域:角色清单非固定,加 role_groups 模板
- C 域:状态机改 DISPATCH 循环
- D 域:加 role_invocation_protocol
- Part V:Phase 1 完全重写
- Part VIII:Owner 工作量加"配置角色组"
- project.yaml schema:加 roles / role_groups 配置

**元层认知**:

```
前 9 次修订都是在"精简"(删 / 砍 / 精准化)
v2.0 是"重构"(改变核心范式)

为什么 v2.0 来得这么晚?
  因为这种范式问题需要长时间的反复审视才能看清。
  Owner 在沉淀过程中,带着"现实世界怎么做"的视角回看,才发现 v1.x 跟现实脱节。

这是第 10 次修订,也是质量最高的一次。
  不再是"我把虚高设计删掉",而是"我用了一个更优雅的架构范式"。
```

**没有变的**:

- 10 条宪法的核心原则(隔离、autonomous、Owner 不在 review loop、数据沉淀...)
- 工具栈(LangGraph + Postgres + Claude Agent SDK + Git worktree)
- E 域记忆设计
- F 域质量门设计
- G 域成本管理
- H 域数据沉淀

**Phase 0-1 Execution Spec 需要同步修订**——这是后续工作。

---

### v1.7(2026-05-24):C4 severity 判定标准明确化

**修订前(v1.4-v1.6)**:
> C4 子能力描述含"小调整 PM 自主 / 中等通知 Owner / 大改 escalate"
> 但**没有可执行的判定标准**——什么算"小"、"中"、"大"?

**修订后(v1.7)**:
> "小/中/大"明确为 D5 signals 的 severity 字段(low/medium/high)
> D 域加上可执行的判定标准 + 调度者三级处理规则

**起因**:Owner 沉淀时追问"小调整 PM 自主 / 中等通知 Owner / 大改 escalate 如何判定大中小?"

**问题分析**:原版用"小/中/大"这种**模糊副词**,没说怎么判定。这跟之前几次修订(self-evolution / A/B 灰度 / 跨模型 panel / 6 层防御 / 控制权表述)是同一类问题——**听起来合理但无法落地**。

实际上,"小/中/大"已经被 v1.2 引入的 severity 字段(low/medium/high)覆盖了,**只是当时没把判定标准也一并下沉**。

**修订内容**:

1. D 域加上**可执行的 severity 判定标准**(可直接放进角色 system_prompt):
   - 默认 medium
   - 升 high 触发:跟 success_criteria 冲突 / security / data_loss / 角色矛盾 / 流程作废
   - 降 low 触发:风格建议 / 长期想法 / 不影响 success_criteria 的小优化

2. D 域加上**调度者三级处理规则**:
   - low: 仅记 events
   - medium: 记 events + pending_concerns
   - high: 改变流向;累计 ≥ 3 → escalate

3. C4 描述精准化:不再说"小/中/大",明确为 severity 在流程层的应用

**元教训**:

副词("小"/"中"/"大")是表述模糊的标志。**好的设计应该用可判定的字段**(severity = low/medium/high)和**可执行的触发条件**(具体的判定规则),而不是程度副词。

这是第 9 次修订,模式跟前 8 次完全一致:Owner 精准追问 → Claude 发现自己的模糊设计 → 改成可落地的版本。

---

### v1.6(2026-05-24):并发模型修订 — 任务间并行,删除 project lock

**修订前(v1.0-v1.5)**:
> 项目内串行,项目间并行
> 同一 project 同时只能跑一个 task,用 Postgres advisory_lock 实现

**修订后(v1.6)**:
> 任务间并行,任务内串行
> 唯一硬约束:同一 worktree 同时只跑一个 task(自动满足,每个 task 创独立 worktree)

**起因**:Owner 在沉淀时反问"不同的分支是可以并行的对吧?",然后精准定位"同一 worktree 需要串行,这样合理么?"

**问题分析**:原版"项目内串行"是从"避免冲突"的直觉来的,但**冲突源已经被 Git worktree 物理隔离了**——

```text
Phase 2 设计:每个 task 创建独立 worktree:
  /srv/agent-projects/worktrees/example-api/task-001/
  /srv/agent-projects/worktrees/example-api/task-002/

不同 worktree 物理隔离:
  - 文件不冲突 (Git worktree 设计意图)
  - 端口随机分配
  - DB 用 branch (neon/pg_branch)
```

**真实情况**:同一 project 的两个 task 完全可以并行,因为它们各自的 worktree 已经隔离。

**原版"PM 抢占问题"分析**:

我之前认为"PM 同时处理两个任务会 context 污染",但**LLM 角色没有跨任务 context**——每次调用是独立 prompt + state。"抢占"是把"会议室单线程领导"的概念误植到 LLM 上。

**LLM 不是领导,不会抢占**。

**风险审视**(都不需要项目锁):

```text
风险 1: project_memory 写竞争     → Postgres 事务已处理
风险 2: project.yaml 修改竞争     → 罕见,且 Owner 手动改
风险 3: LLM rate limit            → G4 配额管理,跟项目无关
风险 4: Owner 通知爆炸            → UX 问题,不是技术问题
风险 5: DB 资源竞争               → project.yaml isolation 已处理
```

**Owner 强制串行的逃生口**:

如果 Owner 确实想让两个任务串行(罕见但合法),task.yaml 可加:

```yaml
task_id: task-002
blocking_on: task-001  # 等 task-001 完成
```

**新粒度的真实表述**:

```text
串行单元 = worktree_path (不是 project_id)
  - 不同 worktree → 并行 OK
  - 同一 worktree → 串行(但每个 task 都有独立 worktree,这种情况不会发生)

实际效果 = 任务间并行,任务内串行
```

**实施层影响**:

- 删除 Postgres advisory_lock 相关代码
- Queue 查询条件从 "project_id NOT IN running" 改为 "worktree_path NOT IN running"
- task.yaml schema 加 blocking_on 字段(可选)
- 各处文档"项目内串行"措辞改为"任务间并行,任务内串行"

**元教训**:再一次,"看起来稳妥"的设计(项目级锁)经不起精准的粒度追问。

Owner 的反问"同 worktree 才需要串行,对吧?"完美命中了真实粒度——证明这种**精准粒度的反问**是发现过度保守设计的有效武器。

---

### v1.5(2026-05-24):通信原则表述澄清 — "控制"是代码约定不是权限系统

**修订前(v1.2-v1.4)**:
> 调度者掌握"谁读 state、谁写 state"的决定权

**修订后(v1.5)**:
> 调度者的"控制"是代码架构约定(LangGraph reducer 模式 + build_context_pack 入口),不是权限系统。

**起因**:Owner 在 Phase 0-1 开工前的概念追问:"调度者控制文档权限么?"

**问题分析**:原表述用了"决定权"这种听起来权威但**模糊的词**,混合了两个完全不同的概念:

```text
逻辑层 (代码架构约定):
  - 所有 state 修改通过 LangGraph reducer
  - 角色看到什么由 build_context_pack 决定
  - 这是 V1 真实做的事

物理层 (权限系统):
  - 文件系统权限 / ACL / 加密 / 多用户隔离
  - V1 完全不需要做
  - 底层隔离已天然存在 (LLM 无状态、worktree 物理隔离、DB 连接隔离)
```

原表述让 Owner 合理地以为"调度者控制 = 文件权限系统",但实际不是。

**修订后的核心表述**:

调度者的"控制"通过两个**代码机制**实现:

1. **LangGraph reducer 模式**:角色 node 通过 return 值更新 state,不直接 mutate state object
2. **build_context_pack 入口**:角色只能看到调度者给它的 input,不能"偷看"完整 state

不同 task 的 state 由 LangGraph checkpoint 按 task_id 隔离。

V1 阶段不需要任何额外的权限/ACL/加密设计。

**为什么不需要权限系统**:

```text
威胁 1:LLM 偷看 state          → 不存在,LLM 是无状态 API
威胁 2:Claude Code 读 state    → Phase 2+ worktree 隔离自然防住
威胁 3:角色代码 bug 损坏 state  → 不是权限问题,是代码质量问题(reducer 模式防)
威胁 4:并发任务污染 state       → LangGraph checkpoint 按 task_id 隔离
```

**元教训**:写"控制权"这种**听起来权威但缺乏机制**的描述时,要警惕——它可能让人误以为有保护层但实际没有,或反过来误以为系统比实际更复杂。

精确的表述应该是:"通过 X 机制保证 Y",不是"X 掌握 Y 的决定权"。

---

### v1.4(2026-05-24):压力测试 + 重叠消除

本次修订是连续 4 轮"压力测试"的集中收口。先列每轮的具体修订,再总结元层教训。

#### A. H 域大幅收缩(从"自我进化"降为"数据沉淀")

**修订前(v1.0-v1.3)**:
- H1 失败案例沉淀 → 包含失败反哺 PM 拆解
- H2 决策回顾 → 周报推送
- H3 流程进化 → 模式挖掘 + skill 自演化
- H4 反馈内化
- Tier 1/2/3 分级自治机制

**修订后(v1.4)**:
- H1a 失败结构化存档(纯日志)
- H1b 失败聚类与复发检测(纯监控)
- H4 Owner 反馈收集(纯 audit log)
- 删除 H1c / H2 / H3a / H3b 和 Tier 分级

**起因**:Owner 质疑"自我进化"的真实可行性。

**业界证据**:
- Hermes 社区(self-evolution 招牌项目)4 月文章:"问题不是 learning,问题是 unobservable learning。agent 学坏了不会 loud failure,只会 silent drift"
- Gartner 预测 40% 的 agentic AI 项目 2027 年前被取消
- ICML 2025 / 2026 多篇论文:LLM 错误高度相关,wisdom-of-crowds 在 LLM 上不成立

**结论**:H 域所有"自动改系统"的部分都是空头支票,删除。保留数据收集层,辅助 Owner 看数据手动改 prompt。

#### B. B5 改"角色质量门",合并 H5

**修订前**:B5 灰度发布(A/B 测试 + 流量切换);H5 黄金测试集(新增)

**修订后**:B5 = H5 = 角色质量门(Git PR + golden dataset 回归)

**起因**:Owner 质疑"灰度 A/B" 在每天 3 个任务下的可行性。

**业界数据**:
- 单 prompt A/B 至少需要 50-100 样本检测中等效果,200-500 样本检测细微效果
- 每天 3 任务 → 3-5 周才能验证一次 prompt 改动 → 不可行
- 业界对小项目的真实做法是 golden dataset + LLM-as-judge,不是 A/B 测试

**结论**:Owner 改 prompt 走 PR 流程,CI 用 golden dataset 跑 vN vs vN+1,LLM-as-judge 输出 diff 报告。Binary cutover。

#### C. F1 改单 LLM Reviewer

**修订前**:F1 = 3-reviewer 跨模型 panel + 严格一票否决

**修订后**:F1 = 单 LLM Reviewer + 结构化 rubric + 硬护栏 + 单字段(security_or_data_loss_risk,v2.4 重命名为 must_escalate_to_owner)一票否决

**起因**:Owner 质疑"跨模型 panel"的实际收益。

**业界证据**:
- ICML 2025 论文《Correlated Errors in Large Language Models》:LLM 错误显著相关,大模型之间 60% 一起错
- 2026 论文《Consensus is Not Verification》:aggregation 在 LLM 上没有持续超过单模型 baseline
- 单 LLM judge 达 80-85% 人类一致性,已经够了
- Claude + GPT + Gemini 三个旗舰同时调:3 倍成本 + 3 倍延迟,收益不明确

**结论**:单 LLM Reviewer 是 V1 主路径。跨模型 panel 推迟到 V2 评估,仅用于高风险场景。

#### D. 子能力重叠消除(全文扫描)

发现 7 处重叠:

| 重叠 | 处理 |
|---|---|
| E1 任务状态记忆 ↔ task state | 删 E1,归基础设施 |
| E2 决策历史 ↔ task_events | 删 E2,events 表已涵盖 |
| E5 角色表现 ↔ B2 角色能力建模 | 合并到 B2 |
| E4 跨任务学习 ↔ H1c 反哺 PM | 删 E4 大部分,保留架构层"PM 检索" |
| C4 流程偏离 ↔ D5 signals | C4 改为 D5 的流程层应用 |
| F2 辩论 ↔ D4 debate_round | D4 实现,F2 引用 |
| H1b 失败聚类 ↔ G3 异常检测 | H1b 保留,标注 V2 跟 G3 合并 |

**结论**:E 域从 5 个子能力收缩为 1 个核心。子能力总数从 38 减到 32。

#### E. 防无限执行机制的简化

**修订前**:6 层防死循环(预算 + 状态轮次 + signals 累计 + signal 循环检测 + 进展检测 + 超时)

**修订后**:1 层(预算硬上限)。其他指标(signals 数量、状态轮次、耗时)只做观测,不作为终止条件。

**起因**:Owner 反问"有必要这么复杂么?"

**核心洞察**:每天 3 个任务、每任务 $20 预算,**预算护栏就是终极护栏**。它比所有其他护栏都更可靠:不依赖 LLM 判断、不需要额外代码、不可能被绕过。其他层是"业界稳妥堆砌",在小规模场景下都是冗余。

---

### v1.3(2026-05-24,已并入 v1.4)

第一次压力测试:H 域 self-evolution 删除。详见 v1.4 A 部分。

---

### v1.2(2026-05-24):宪法第 2 条修订 — 角色信息流原则

**修订前**:
> 角色之间不直接通信,必须经过调度者中转(硬约束)

**修订后**:
> 角色不直接调用对方,但可以在输出里发 signals;所有执行调度由调度者决定

**起因**:Owner 在 Phase 0-1 开工前质疑"严格中转"是否合理。

**问题分析**:原版约束**混淆了两件事**——

- 架构层面禁止"角色凭意志互相调用"(应该禁止)
- 信息层面禁止"角色提到另一个角色的产出或反馈"(没必要禁止)

**典型场景代价**:

```text
原版下,Developer 觉得 PM 拆解有矛盾,要走 4 轮调度 + 2 次额外 LLM:
  Developer 输出 needs_clarification
  → 调度者识别属于 PM
  → 调度者调 PM
  → PM 修订 plan
  → 调度者传回 Developer

修订后,Developer 在输出里直接说:
  developer_output.signals_to_other_roles:
    - target: pm, type: concern, content: "step 2 跟 step 1 矛盾"
  调度者读 signal,自动调 PM 修订,1 轮完成。
```

**底层认知升级**:

```text
LLM 角色不是独立进程,是 prompt + 一次调用。
"通信"在 LLM 角色之间,本质是信息在 state 里流动。
调度者的工作是"决定谁读 / 谁写 state",不是"传递消息"。
这跟 LangGraph 的 graph state 模型一致。
```

(注:此处"决定权"的措辞在 v1.5 进一步精确化,见上面 v1.5 部分)

**实施层影响**:

- 每个角色输出 schema 加 `signals_to_other_roles` 字段(可选)
- 调度者读 signals,有明确处理规则(见 D 域设计)
- 防止滥用:角色提议,调度者有最终决定权
- signals 数量 + severity 累积过高 → ESCALATED_TO_OWNER

**保留的原则**:

- 调度者掌握所有调度决定权(没变)
- 角色不能直接修改对方产出(没变)
- 角色不能在 LLM 调用里 invoke 别的角色(没变)

**这次修订的元认知**:

> "完整设计文档"也会有错。
> 写"硬约束"时要警惕——是真的"违反就出事",还是"觉得这样比较干净"?
> 前者才是宪法,后者只是偏好。
> 这次差异:原版偏好被错误升格为宪法。修订把它降回偏好级别。

---

### v1.1(2026-05-24):整合 codex review 反馈

外部 reviewer(codex)对 v1.0 设计提出 10 条改进意见,全部采纳:

```text
1. Phase 0 拆分为 0A/0B/0C(纯文件骨架 / 最小 runtime / 基础设施替换)
2. LangGraph 从"事实标准"降级为"实现选择",新增 PoC 验证门
3. 工具能力全部标注"假设" + fallback,新增工具假设表
4. V1 不再 auto-merge(改为 PR_READY),auto-merge 推迟到 V1.5
5. 新增 V1.5 中间阶段(低风险项目可开 auto-merge)
6. protected_paths 分三级(hard_block / approval_required / warn_only)
7. Markdown 同步 V1 改为单向(DB → MD),双向推迟到 V2
8. Curator 自动写入策略按 layer 分级,新增 active_candidate 状态
9. V1 总周期改为 6-8 周(每 phase 1 周硬时间盒,跑不完降级范围)
10. Part IX 新增 PoC 验证问题、流程层问题
```

**起因**:Owner 让另一个 AI(codex)对 v1.0 做独立 review。

**元教训**:外部 reviewer 抓出来的问题,跟自己的盲区高度互补。哪怕都是 LLM,**视角不同就能看出不同的问题**。

---

# Part IV:被否决的设计清单

> 这是给"未来想加回某个业界标配"的自己的检查清单。
>
> 如果你看到这些设计很心动,**先回去看一遍它为什么被否决**。

## 已删除的设计

| 设计 | 名义价值 | 否决理由 | 详见 |
|---|---|---|---|
| **Hermes 全栈引入** | 借鉴自演化能力 | Hermes 是单 agent + 用户对话框架,不是 multi-agent 协作框架 | (历史讨论) |
| **角色严格中转通信** | 隔离与可控 | 偏好被升格为宪法,跨角色信息流要 2 次 LLM | v1.2 |
| **H 域 self-evolution** | 系统越用越好 | unobservable learning,2026 业界不成熟 | v1.4 A |
| **B5 灰度 A/B 测试** | 生产级标配 | 每天 3 任务样本量不够 | v1.4 B |
| **F1 跨模型 3-reviewer panel** | 消除 LLM 通病 | LLM 错误相关性高,跨模型无效 | v1.4 C |
| **固定 4 角色范式(PM/Architect/Developer/Reviewer)** | 简单可预测 | 跟现实世界脱节,Architect 沦为 reviewer,新加角色要改架构 | v2.0 |
| **固定状态机流程(PM→Arch→Dev→Reviewer)** | 调试方便 | 不能适配不同任务复杂度,V1 → V2 必然重写 | v2.0 |
| **A3 强制 Architect 复核** | 防拆错 | Architect 不应该是 reviewer,而是 Owner 可配置的角色 | v2.0 |
| **risk_class enum + 关键词匹配兜底** | 硬护栏识别 security/data_loss signal | LLM 写 signal 千变万化,关键词匹配漏报严重;改用 immediate_escalate_required boolean | v2.2 |
| **PM raw plan 直接执行** | 简单 | PM 可能漏角色/引用错 role_id/循环依赖,必须先经 validator | v2.2 |
| **"worktree 物理隔离已足够"表述** | 简化 | Git worktree 是工程隔离,不是 OS sandbox,V1 接受工程隔离风险但表述要诚实 | v2.2 |
| **validator autofix(替 LLM 补漏)** | 节省 retry 成本 | autofix 让 LLM 失败模式被掩盖 + 模糊职责边界 + 兜底机制本身脆弱;v2.4 改为 retry 或 escalate 两级 | v2.4 |
| **required: true/false 标记角色"必需"** | 起步默认配置 | 跟第 5 条宪法"Owner 配置不固定数量"自相矛盾;v2.4 改用 is_orchestrator 标记唯一 framework 约束 | v2.4 |
| **required_roles plain list 顺序** | 简单直观 | LLM 容易忽略 list 位置的隐式顺序;v2.4 改用 role_sequence(step + role_id)显式结构 | v2.4 |
| **artifact 覆盖式重试** | 存储节省 | 覆盖了就追溯不了;v2.4 改追加 attempt N + superseded_by | v2.4 |
| **0B 中间形态 mock(部分角色真 LLM)** | 提前打磨 prompt | Reviewer 跑真 LLM 看 mock 固定数据没验证价值;v2.4 明确 0B 只 PM 真 LLM | v2.4 |
| **6 层防死循环护栏** | 稳妥多重防御 | 预算护栏是终极护栏,其他都冗余 | v1.4 E |
| **H1c 失败反哺 PM** | 不重复犯错 | 没业界验证,易让 PM 过度保守 | v1.4 A |
| **H2 决策回顾周报** | 系统状态可观 | Langfuse 已有 dashboard,Owner 不一定看 | v1.4 A |
| **H3a 流程模板挖掘** | 优化常见流程 | V1 状态机本来固定 | v1.4 A |
| **H3b Skill 自演化** | Hermes 招牌能力 | 三大陷阱:gaming / drift / 无收益 | v1.4 A |

## 已合并/重组的设计

| 重组前 | 重组后 | 详见 |
|---|---|---|
| B5 角色升级 + H5 黄金测试集 | B5 角色质量门 | v1.4 B+D |
| E5 角色历史表现 | 合并到 B2 角色能力建模 | v1.4 D |
| E1 任务状态记忆 | 归入基础设施 task state | v1.4 D |
| E2 决策历史 | 归入 task_events 表 | v1.4 D |
| C4 流程偏离 | 改为 D5 signals 的流程层应用 | v1.4 D |
| F2 辩论 | 引用 D4 debate_round 实现 | v1.4 D |

## 推迟到 V2 / V3+ 的设计

| 设计 | 推迟到 | 推迟原因 |
|---|---|---|
| auto-merge | V1.5 低风险开,V2 全面开 | V1 reviewer 未经充分验证 |
| 双向 markdown 同步 | V2 评估 | 冲突处理复杂,单人维护成本高 |
| pgvector 向量检索 | V2 | 记忆条数不够多,SQL FTS 够用 |
| Program 层(跨 repo) | V2 | V1 单 repo 都没跑稳 |
| Reviewer Panel(跨模型) | V2 高风险场景 | LLM 错误相关性问题待解 |
| Arbiter(Opus 仲裁) | V2 可选 | V1 用不到 |
| H 域 self-evolution | V3+(等业界数据) | 2026 年还不成熟 |
| **OpenSpec 工作流** | **Phase 2 启动时 re-evaluate** | Phase 1 是 prompt 迭代,git commit + golden_dataset 已足够;OpenSpec 强在"多步骤改动 + pre-implementation review",Phase 2(worktree+executor 跨 spec+code+infra)才是它的场景。详见下方触发条件 |

### OpenSpec 引入触发条件(2026-05-27 Owner 询问 4 次后记下)

**满足以下任一**就 re-evaluate 引入:

1. **Phase 2 启动时**(Git worktree + executor 集成)
   - 改动跨 spec + 代码 + 新基础设施,典型 multi-step 场景
   - 这是设计上最自然的引入点

2. **出现 git log 看不出 why 的痛点**
   - 比如某次 prompt 改动后行为变了,翻 git log 找不到 reason
   - commit message 不足以追溯设计意图
   - 多个 prompt 改动同时在 in-flight,Owner 自己都不记得哪些已 merge

3. **agent-org 自己开始 propose 代码改动**(V2+ self-evolution,V1 已否决)
   - 那时 agent 需要提交结构化 proposal,Owner 异步 review
   - 这是 OpenSpec 价值最大化的场景

**不要因为**以下原因引入(已踩过的坑):
- "开始写代码了所以该用专业工具"——工具应该解决具体痛点,不是阶段标志
- "趁现在没多少 spec 先迁移省事"——迁移成本一次性,但维护成本持续;只要 git + design-history 还够用,就不引入
- "其他 multi-agent 项目用了"——参见 [[feedback-multi-layer-design-smell]]:多套并行流程是设计味道

**引入时要做的**(到时候直接抄):
- `openspec init` 在仓库根目录
- 把 `docs/decisions/` 现有 ADR 迁过去(可选,新 proposal 走 openspec/changes/)
- 把 OpenSpec workflow 写进 CLAUDE.md
- design-history.md 保留(它是历史档案,不是 change proposal 队列,跟 OpenSpec 不冲突)

---

## 文档元数据

- 文档版本:v2.4
- 创建日期:2026-05-24
- 配套主文档:autonomous-agent-system-design.md v2.4
- 维护原则:每次主文档修订后,这里也加一条
- 阅读策略:**不主动读,只在做决策时翻**
