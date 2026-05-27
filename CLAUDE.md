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

## 变更工作流(Phase 3+ 用 OpenSpec)

Phase 0A-2 用 commit message + design-history 记录变更。**Phase 3 起**,跨架构层的
新功能(多文件 / 跨模块 / 新基础设施)走 OpenSpec workflow:

```bash
# 1. 创建 change(kebab-case 名字)
npx -y @fission-ai/openspec new change <name>

# 2. 写 4 个 artifact(看 .github/skills/openspec-*/SKILL.md 模板)
#    openspec/changes/<name>/proposal.md   # why + what
#    openspec/changes/<name>/design.md     # how(技术决策)
#    openspec/changes/<name>/specs/<cap>/spec.md   # ADDED/MODIFIED Requirements + scenarios
#    openspec/changes/<name>/tasks.md      # checkbox 实施步骤

# 3. 验证
npx -y @fission-ai/openspec validate <name>
npx -y @fission-ai/openspec status --change <name>

# 4. 实施完成后 archive
npx -y @fission-ai/openspec archive <name>
# → spec 文件移到 openspec/specs/<cap>/spec.md(真相源)
# → change 移到 openspec/changes/archive/<name>/
```

**什么时候用 OpenSpec(不要每个 commit 都用)**:
- 跨架构层的多步骤改动(Phase 3 PR 生成 / Phase 4 记忆系统等)
- Owner 提的新 feature 需要 pre-implementation review
- 改动会引入新 capability(新 spec 文件)

**什么时候直接 commit(不走 OpenSpec)**:
- 单文件 bug fix / prompt 调优
- 小重构
- 文档错别字

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
