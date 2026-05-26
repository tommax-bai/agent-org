# Vocabulary - 全局词汇表(v2.4)

> 所有 role 的 input/output 字段必须使用本词汇表里的标准词。
>
> 真相源:本文件。主文档 D1 子能力描述跟这里有冲突时,以本文件为准。

---

## 任务相关

- `task_id`: 任务唯一标识(格式:`task-YYYY-MM-DD-NNN`)
- `subtask_id`: 子任务唯一标识(v2.0)
- `owner_request`: Owner 原始需求文本
- `parsed_intent`: 解析后的意图
- `success_criteria`: 成功标准

## 业务拆解(v2.0 新增 / v2.4 改 role_sequence)

- `business_breakdown`: PM 输出的业务子任务列表
- `subtask`: 业务子任务,含 `description / task_type / role_sequence / dependencies`
- `task_type`: 任务类型(`simple_feature / complex_feature / bug_fix / refactor / ...`)
- `role_sequence`: 该子任务的角色执行顺序(v2.4 替代 `required_roles`)
  - 结构:`[{step: 1, role_id: X}, {step: 2, role_id: Y}, ...]`
  - 顺序由 `step` 字段决定(从 1 起连续递增),list 位置无语义
  - dispatcher 按 step 排序派活
- `role_dispatch_notes`: PM 对角色调度的说明(偏离默认模板时记录原因)

## 角色配置(v2.4 方案 Y)

- `is_orchestrator`: boolean,标记某角色是任务编排者(担任 PM 职责)
  - **framework 唯一硬约束**:`project.yaml` 里恰好一个角色标 true
  - 校验失败 → 系统拒绝启动
- `role.yaml`: Owner 配置的角色定义
- `examples/role_templates/`: framework 提供的角色参考模板(不是内置角色)

## 角色调用(v2.0 改:统一 role_invocation_protocol)

- `role_invocation_input`: 调度者调用角色的标准输入
- `role_invocation_output`: 角色返回给调度者的标准输出
- `context_pack`: 调度者为角色准备的上下文
- `artifact`: 角色产生的产物
- `artifact_id`: 产物唯一标识,可被后续角色引用
- `attempt`: int,同 (subtask, role) 第几次尝试(v2.4 新增,从 1 起)
- `superseded_by`: 被哪个新 artifact_id 取代(可选,追溯链)

## 决策相关

- `verdict`: 角色返回的判定(`success | needs_changes | escalate`)
- `assumptions`: 假设清单
- `confidence`: 置信度(0.0-1.0)
- `concerns`: 关注点列表

## 状态相关

- `state`: 任务当前状态
- `transition`: 状态转换
- `escalation`: 升级事件
- `budget`: 预算
- `cost_used`: 已消耗成本

## 状态机节点(v2.0)

- `PM_PLANNING`: PM 业务拆解 + 角色调度阶段(任务入口,一次性)
- `DISPATCH`: 调度者派活的核心节点(循环)
- `ROLE_EXECUTING`: 角色执行中
- `ESCALATED_TO_OWNER`: 升级给 Owner
- `DONE`: 任务完成

## Signals 相关

- `signals_to_other_roles`: 角色发给其他角色的信号列表(可选输出字段)
- `signal_target`: 信号目标角色(角色 id,由 project.yaml 定义)
- `signal_type`: 信号类型
  - `question`: 提问,需要被询问角色回应才能继续
  - `concern`: 关注点,提醒对方注意但不阻塞
  - `suggestion`: 建议,被建议角色下次执行时可参考
  - `collaboration_request`: 协作请求
- `signal_severity`: `low | medium | high`
- `signal_content`: 自然语言描述
- `immediate_escalate_required`: boolean(v2.2,默认 false)
- `immediate_escalate_reason`: string(当 `immediate_escalate_required=true` 时必填)

## Dispatch 相关(v2.2 / v2.4)

- `dispatch_plan`: PM 输出的执行计划(含 `business_breakdown + role_sequence`)
- `normalized_dispatch_plan`: validator 校验通过的计划(才能被 DISPATCH 执行)
- `dispatch_policy`: Owner 配置的强制规则(`mandatory_role_rules + pm_deviation_policy`)
- `mandatory_role_rules`: dispatch_policy 的硬规则(validator 必须强制执行)
- `pm_deviation_policy`: PM 偏离 role_groups 模板的权限

## Validator 处理(v2.4 两级)

- `PASS`: 校验通过,进 DISPATCH
- `RETRY_PM`: LLM 可能改对的错误(漏 mandatory / 删 mandatory / role_id 拼错 / role_sequence step 不连续 / task_type 不存在 等)
  - 上限 1 次(可配置),超过即 escalate
- `FATAL`: 只有 Owner 能改的错误(引用不存在的 role_id / 依赖成环 / dispatch_policy 配置错)
  - 直接 ESCALATED_TO_OWNER

(v2.4 删除 v2.2 的 `autofix` 档,见宪法第 12 条)

## Reviewer artifact 关键字段(v2.4 改名)

- `must_escalate_to_owner`: boolean(v2.4 替代 `security_or_data_loss_risk`)
  - true 时 verdict 必须是 escalate(一致性校验)
  - 触发条件:安全风险 / 数据损失 / 合规风险 / 生产稳定性 / 不可逆架构变更
- `escalation_reason`: string(`must_escalate_to_owner=true` 时必填)

## Event 类型(v2.4 更新)

事件 enum 见 `schemas/event.schema.json`(待建)。v2.4 关键变化:
- 删除:`PLAN_AUTOFIXED`(autofix 档已删)
- 新增:`PLAN_RETRY_REQUESTED`, `PLAN_VALIDATION_FATAL`, `ATTEMPT_LIMIT_REACHED`

完整列表:
```
TASK_CREATED, STATE_CHANGED, DISPATCH_DECISION,
ROLE_INVOKED, ROLE_RETURNED, SIGNAL_RECEIVED,
BUDGET_CONSUMED, ESCALATED,
TASK_COMPLETED, TASK_FAILED,
PLAN_RETRY_REQUESTED, PLAN_VALIDATION_FATAL,
ATTEMPT_LIMIT_REACHED,
IMMEDIATE_ESCALATE_TRIGGERED, IMMEDIATE_ESCALATE_REJECTED,
ARTIFACT_VALIDATION_FAILED
```
