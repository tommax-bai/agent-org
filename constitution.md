# 系统宪法(v2.4)

> 这是系统的根本原则。任何工具、实现选择都不能违反这些原则。
>
> **真相源**:`docs/autonomous-agent-system-design.md` Part III。本文件是抽出的精简版。
>
> 修订历史:`docs/design-history.md` Part I。

---

## 1. 任务间并行,任务内串行

- **任务间**:每个 task 有独立 worktree + 独立 task_id,默认可并行
- **任务内**:子任务按依赖顺序,角色按 PM 调度顺序执行
- **唯一硬约束**:同一 worktree 同时只跑一个 task(自动满足,每个 task 一个 worktree)

(并发模型的基础)

## 2. 角色不直接调用对方,但可以在输出里发 signals;所有执行调度由调度者决定

- **允许**:角色输出引用其他角色的产出、提出疑问、给出反馈、请求协作
- **禁止**:角色在自己的执行过程中直接 invoke 另一个角色或修改对方产出
- 调度者读取 signals,根据规则决定下一步流向

(隔离与可控的基础)

## 3. 项目之间完全隔离

(简单性与安全性)

## 4. PM 是任务编排者,调度者是执行者

- PM 做业务拆解 + 角色调度(决定调用哪些角色)
- PM 不做技术决策、不写代码、不审查
- 调度者按 PM 决定派活,纯确定性,不做语义判断
- 各个角色(Architect、Developer、Reviewer 等)做自己专业范围的工作

(Orchestrator-Worker 范式)

## 5. 角色由 Owner 配置,不固定数量(v2.4 落实方案 Y)

- 所有角色(包括 PM)都是 Owner 配置,framework 不预设
- `role.yaml` + `system_prompt.md` 即可注册新角色
- **framework 唯一硬约束**:`project.yaml` 里恰好一个角色标 `is_orchestrator: true`(担任 PM 职责)
- 起步路径:从 `examples/role_templates/` 拷贝想要的角色到 `projects/<x>/roles/` 改
- `project.yaml` 配置 `role_groups` 模板(任务类型 → 默认角色组,PM 起点)
- 角色必须遵守 role_invocation_protocol(见主文档 D 域)
- 简单任务可不调用 Architect,复杂任务可调用多个 reviewer

(角色可扩展)

## 6. 质量来自结构化评估 + 硬护栏

- 单 LLM Reviewer + 结构化 rubric + 硬护栏 + golden dataset 回归

(autonomous 质量保证)

## 7. 硬护栏在基础设施层强制,不靠 LLM 判断

(安全底线)

## 8. "更新 agent" 完全是 Owner 决定

系统只沉淀数据,所有改进决策权在 Owner。

(控制权归属)

## 9. 所有决策可解释、可追溯

(可调试性)

## 10. 失败和介入沉淀为数据,辅助 Owner 改进

系统不自动改自己,Owner 看数据改 prompt。

(可观测性)

## 11. Owner 不在 loop 里 review,但始终在 loop 里改进系统

(Autonomous != 失控)

## 12. LLM 输出 + 确定性兜底(v2.4 修订)

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

---

## 宪法演化

- v1.0:10 条
- v2.0:11 条(加第 5 条角色配置)
- v2.2:12 条(加第 12 条 LLM 治理)
- v2.4:第 12 条收紧(删 autofix 档,只 retry 或 escalate)

详细见 `docs/design-history.md`。
