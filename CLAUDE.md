# 协作纪律(读文档前先看这个)

这个仓库是 **agent-org**——autonomous multi-agent 研发系统的实际代码 + 设计文档。

设计内容在 `docs/`(从 `docs/INDEX.md` 开始读),这份文件只讲**怎么跟 Owner 协作**。

---

## 沟通

**说人话**。默认用自然段+口语,不要默认套"背景 / 选项 / 推荐 / 副作用 / 没想清楚的"
五段式 + 表格 + 伪代码。读 Owner 的提问,如果两句话能说清就两句话,
别为了显得专业堆形式。

**只在真需要时才上结构**:
- 多个选项要并列对比 → 表格 / 列表
- 讨论具体 schema / yaml / 代码 → 给示例
- Owner 主动说"整理一下" → 结构化
- 内容超过 2-3 屏读者要导航 → 小标题

讨论设计取舍、给判断/论据时,**自然段比表格更好**。

---

## 设计原则(给 AI 自己警惕用)

**多层保护 / 防御性设计 / 冗余兜底,大概率是设计本身有问题**。
如果发现自己在堆 2 层以上"保护"(字段名层 + 结构层 + validator 层这种),
先停下来问"为什么单一层不够?"。通常根因是:数据结构没拆干净、
边界不清、责任分配错位。修方案的方向是**合并到单一事实源**,不是堆更多层。

(校验/格式合法性不算"层",那是基本卫生。)

---

## 讨论节奏

- **一次深聊一个问题**。批量给"5 个问题各 3 句话"会被反驳"太泛看不懂"。
  每次一个问题:完整论据 + 真实数据 + 反例 + 副作用。
- **被反驳认错快,不要找补**。Owner 反驳通常论据扎实,别为了维护原方案而辩护。
  先认错、再给修订方案,不要又一次给 3 个选项让 Owner 选。
- **先聊清楚再动手**。即使 Spec 已经很完整,开放问题没敲死前不要急着写代码。

---

## 不要做的事

- **不要推销 subagent / 框架 / 业界标配**。系统已经经过 14 次修订 + 2 次 codex
  review,Owner 看过的设计陷阱清单在 `docs/design-history.md` Part IV。提建议前
  先查"这是不是已否决过"。
- **不要替 LLM 补漏**(宪法第 12 条 v2.4)。validator 只 retry 或 escalate,不 autofix。
  这个原则在跟 AI 协作时也适用——别"贴心地"帮 Owner 做超出他要求的事。
- **不要写废话注释 / 文档**。Owner 已经做过多次精简,看到冗余会要求删。

---

## 文档导航

```
docs/INDEX.md                              先读这个,5 分钟知道有哪些文档
docs/key-design-summary.md                 1500 字速览,5 分钟建立全局
docs/autonomous-agent-system-design.md     主设计 v2.4(长期总纲)
docs/phase-0-1-execution-spec.md           开工施工图 v2.4
docs/design-history.md                     14 次修订 + 已否决清单
docs/phase-1-report.md / phase-2-report.md 各阶段实测报告
docs/deployment-decision.md                部署架构
docs/dependencies.md                       工具栈版本约束
docs/operations/coding-subagent-prompt.md  开发期 AI 助手 prompt
docs/operations/ops-subagent-prompt.md     运维期 AI 助手 prompt
constitution.md                            12 条宪法(从主文档抽出,真相源在主文档)
openspec/changes/                          Phase 3 起的 change proposal(OpenSpec workflow)
openspec/specs/                            归档的 capability spec(OpenSpec archive 后填)
```

讨论中提到"宪法第 X 条""第 Y 条修订""已否决清单"时,去这些文件里查,别凭印象。

---

## 开发规则:基于 OpenSpec(Phase 3 起强制)

**所有跨架构层 / 跨模块 / 引入新 capability 的改动,MUST 先写 OpenSpec change,
proposal/design/specs/tasks 4 个 artifact 全过 validate,Owner 看完批准,再开始 implement**。

不允许"先写代码,事后补 spec"。

### 强制走 OpenSpec 的场景

- 跨多个 orchestrator/ 子模块的功能(如 PR 生成 / 记忆系统 / executor 改造)
- 新增 capability(`openspec/specs/<name>/spec.md` 没有就是新)
- 改动会让 spec 行为变(MODIFIED Requirements)
- 引入新外部依赖 / 新基础设施(docker service / SDK / 外部 API)
- 用户提的新需求需要 pre-implementation review

### 可以直接 commit(不走 OpenSpec)

- 单文件 bug fix / prompt 文本调优
- 重构(行为不变)
- 文档错别字 / 格式调整
- 现有 OpenSpec change 的 tasks 在 implement 中(已经在 change 里了,不要重复包一层)

### 标准流程

```bash
# 1. 创建 change(kebab-case)
npx -y @fission-ai/openspec new change <name>

# 2. 按顺序写 4 个 artifact(每个用 instructions 命令拿模板)
npx -y @fission-ai/openspec instructions proposal --change <name>
# → 写 openspec/changes/<name>/proposal.md(why + what + capabilities 划分)
npx -y @fission-ai/openspec instructions design --change <name>
# → 写 design.md(技术决策 + alternatives + risks)
npx -y @fission-ai/openspec instructions specs --change <name>
# → 写 specs/<capability>/spec.md(ADDED/MODIFIED Requirements + scenarios)
npx -y @fission-ai/openspec instructions tasks --change <name>
# → 写 tasks.md(checkbox 实施步骤)

# 3. 验证
npx -y @fission-ai/openspec validate <name>
npx -y @fission-ai/openspec status --change <name>     # 必须 4/4 complete

# 4. Owner 看完批准 → 按 tasks.md 实施
# 5. 实施完 archive
npx -y @fission-ai/openspec archive <name>
# → spec 移到 openspec/specs/<cap>/spec.md(真相源)
# → change 移到 openspec/changes/archive/<name>/
```

### 新 session 开始时

进入 agent-org 仓库,先看 `openspec/changes/` 下有没有 **in-flight change**:
- 有 → 优先确认是不是要继续这个,不要并行开新 change
- 没有 → 按用户需求判断是否需要新 change

### 跟 design-history.md 的关系

- **OpenSpec changes**:per-change 的完整提案 + spec delta + 实施清单(开发流程)
- **design-history.md**:跨 change 的元层教训(已否决清单 / 设计味道警告)+ 修订历史叙事

两个并存,不冗余。OpenSpec 是"做这次改动的工程文档",design-history 是"为什么这个项目长这样的叙事"。

详细引入背景见 [design-history.md Part IV "OpenSpec 引入触发条件"](docs/design-history.md)。

---

## 模块边界纪律(v2.3 落地)

agent-org 是 **modular monolith**——物理单体,逻辑严格模块化。

**核心规则**:
1. 跨模块 import 只能用 top-level namespace(`from orchestrator.memory import X`)
2. `_internal/` 子目录视为私有,跨模块禁止访问
3. 需要其他模块内部细节时,改它的 `__init__.py` 显式 export,不要绕过接口
4. 优先依赖 Protocol,不依赖具体类
5. 改 `__init__.py` / `importlinter.cfg` 必须走 PR(架构变更)

CI 跑 `lint-imports` 自动拦截违规。详见 `docs/autonomous-agent-system-design.md` Part IV 末尾"模块边界保护"段。
