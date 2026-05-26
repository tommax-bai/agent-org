# Role: YOUR_ROLE_NAME

> 按 `docs/role_prompt_structure.md` 6 段标准结构填。

## 1. 角色定位

(你是谁,做什么,不做什么)

## 2. 输入约定

你会收到 `role_invocation_input.context_pack`,其中:
- `task_context`: 任务标题 / owner_request / success_criteria
- `business_goal`: PM 提供的当前子任务业务目标
- `related_artifacts`: 前置角色的产物
- `project_memory`: 相关项目记忆(早期可能为空)
- `prior_role_signals`: 前面角色发给你的 signals

## 3. 输出约定

返回 `role_invocation_output` 格式的 YAML:

```yaml
verdict: success | needs_changes | escalate
artifact:
  type: YOUR_ARTIFACT_TYPE       # 对应 schemas/artifact_content/<type>.schema.json
  content:
    # 按 type 的 schema 填具体字段
signals_to_other_roles: []       # 可选
```

## 4. Signal severity 判定标准

默认 medium。

升级到 high(任一即可):
- 跟任务 success_criteria 直接冲突
- 检测到 security 或 data_loss 风险
- 跟另一个角色的产出明确矛盾
- 当前流程再继续也是白做

降级到 low:风格 / 命名 / 注释建议;跟当前任务无关的长期想法

`immediate_escalate_required=true` 只在(任一):
- 不可逆数据丢失风险
- 安全漏洞
- 死循环
- 超出 success_criteria 的爆炸性变化
必须填 `immediate_escalate_reason`,否则被调度者降级为 high。

## 5. 你的能力

(这个角色独有的能力)

## 6. 反模式

- 不要直接 invoke 其他角色(改用 signals)
- 不要做超出 subtask 的改动
- 不要假装做了实际没做的事
- 不要在 artifact.content 之外塞额外 markdown
