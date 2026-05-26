# ADR: Validator 不替 LLM 补漏(只 retry 或 escalate)

- **日期**:2026-05-26
- **状态**:已接受
- **关联修订**:v2.4 宪法第 12 条修订
- **触发问题**:Spec 5 个开放问题之 Q1(PM 输出违反 dispatch_policy 时 validator 怎么回路)

---

## 决策

**所有** LLM 输出 + 确定性兜底场景,validator/guardrail 不能替 LLM 补漏,只能:
- `RETRY_LLM`(LLM 可能改对的)
- `ESCALATE`(只有 Owner 能改的,或 retry 后仍失败)

删除原 v2.2 宪法第 12 条的 `autofix` 档(从"autofix 优先,retry 次之,escalate 最后" → "只 retry 或 escalate")。

retry 必须有硬上限(默认 1 次,可配置),超过即 escalate。

---

## 上下文

v2.2 把宪法第 12 条定为"autofix 优先,retry 次之,escalate 最后"。dispatch_plan validator 的三级处理:
- **autofix**:漏 reviewer / 漏 developer / mandatory role 漏 → 自动补
- **retry**:role_id 不存在 / 循环依赖 → PM 重做
- **fatal**:retry 后仍失败 → escalate

v2.4 讨论 Q1 时,Owner 反驳:"两个东西负责同一件事情,职责会变得混淆"。

---

## 论据

### 为什么 autofix 看起来好但实际不好

1. **LLM 失败模式被掩盖**。漏 mandatory role 被 validator 静默补上,Owner 看不见这个失败,PM prompt 永远不会被优化。违反第 10、11 条(系统沉淀失败为数据,Owner 改 prompt)。

2. **模糊职责边界**。validator 干了 PM 该干的事(选角色)。违反第 4 条(Orchestrator-Worker,PM 编排,调度者只执行)。

3. **兜底机制本身脆弱**。autofix 凭"模板里没有 + policy 要求"补角色,policy/模板改了之后,autofix 可能补错。跟"已否决清单"里 `risk_class enum + 关键词匹配兜底` 同源问题(兜底机制不可靠,加上去反而是噪声)。

### 短期代价 vs 长期收益

| | 短期代价 | 长期收益 |
|---|---|---|
| autofix | 每任务省 ~$0.3-0.5 retry 成本,任务跑得"顺" | LLM 失败被掩盖,PM 永远不进化 |
| 只 retry/escalate | 每任务多 ~$0.3-0.5 retry,偶尔卡 | 失败可见,Owner 改 prompt,系统持续优化 |

在 autonomous 系统(Owner 不在 loop 里 review)里,长期收益压倒短期代价。

---

## 实施

### dispatch_plan validator 两级处理

```
违反类型                                    → 处理
─────────────────────────────────────────────────────
漏 mandatory role(模板没有,PM 也没加)      → RETRY_PM
主动删 mandatory role(违反 cannot_remove)   → RETRY_PM
role_id 拼错(Levenshtein 距离 ≤ 2)         → RETRY_PM
task_type 不存在于 role_groups               → RETRY_PM
role_sequence step 不连续 / 重复             → RETRY_PM

引用 project.yaml 不存在的 role_id           → FATAL
依赖图成环                                    → FATAL
retry_pm 后仍失败(连续两次同类错误)         → FATAL
validator 自身遇到配置错(dispatch_policy 矛盾)→ FATAL
```

### Event log

新增 / 调整事件类型:
- 删除:`PLAN_AUTOFIXED`
- 新增:`PLAN_RETRY_REQUESTED`、`PLAN_VALIDATION_FATAL`

### 一致性校验也适用

Reviewer 输出 `must_escalate_to_owner=true` 但 verdict 不是 escalate → 不一致,**不自动改 verdict**,改成 `RETRY_LLM`(Reviewer 自己重写)。

---

## 不做什么

- 不为了"性能"加 autofix 例外
- 不做"轻 autofix 重 retry"这种混合方案(变相加层,违反"多层设计是设计味道"原则)

---

## 修订风险

- 每任务平均成本 +$0.3-0.5(autofix 删除后,类型 A 错误现在 retry 而非静默修复)
- 在 $20 任务预算下可忽略

---

## 关联文档

- `constitution.md` 第 12 条
- `docs/autonomous-agent-system-design.md` 宪法第 12 条 + A 域 Dispatch Plan Validator 段
- `docs/design-history.md` v2.4 修订日志
- memory: `feedback-no-autofix-in-validators`(用户偏好层面的记录)
