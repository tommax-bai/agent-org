# Golden Dataset 格式

> 每个角色都有 5-30 个 golden case,用于:
> - 改 system_prompt 时跑回归(Phase 1+,B5 角色质量门)
> - 验证角色对边界情况的处理
>
> 详细见 `docs/autonomous-agent-system-design.md` B 域"角色创建的工程实践"。

---

## 目录结构

```
roles/<role_id>/
├── role.yaml
├── system_prompt.md
└── golden_dataset/
    ├── README.md                  # 说明这个 dataset 覆盖了哪些场景
    ├── case_001.yaml
    ├── case_002.yaml
    └── ...
```

## 单个 case 的格式

```yaml
case_id: case_001
description: "PM 输出对一个常规 bug fix 任务的拆解"
tags: [bug_fix, simple, single_subtask]

# 输入:context_pack(role_invocation_input)
input:
  task_id: test-task-001
  role_id: pm
  context_pack:
    task_context:
      title: "Fix login timeout"
      owner_request: "登录偶发 30 秒 timeout,改成 5-10 秒并加重试"
      success_criteria:
        - "timeout 5-10s 生效"
        - "测试通过"
    business_goal: ""             # PM 不需要(它自己拆)
    related_artifacts: []
    project_memory: {}

# 期望输出:role_invocation_output 的关键字段(允许部分匹配)
expected:
  verdict: success
  artifact:
    type: dispatch_plan
    content:
      business_breakdown:
        - subtask_id: subtask-001
          task_type: bug_fix
          role_sequence:
            - {step: 1, role_id: developer}
            - {step: 2, role_id: reviewer}
  signals_to_other_roles: []      # 期望 PM 不发 signal
  confidence_range: [0.7, 1.0]    # 接受范围,不是精确值

# 期望不应该出现的反模式
forbidden:
  - "verdict=escalate"
  - "role_sequence 含 architect"  # 简单 bug fix 不该用 architect
  - "subtask_count > 2"           # 不该过度拆解
```

## 评估方式

Phase 1+ 用 LLM-as-judge:

```python
# 跑一遍
actual = role_runner.execute(case.input)

# 对比期望
judge_prompt = f"""
对比 expected 和 actual,给一个 score(0-100):
- 关键字段一致:+50
- forbidden 都不出现:+30
- confidence_range 在范围内:+10
- 整体合理性:+10
"""
score = judge_llm.call(judge_prompt)
```

通过线:**单 case ≥ 70 分,全 dataset 平均 ≥ 80 分**。

---

## 写 case 的建议

1. **覆盖范围**:
   - 常规 case 5-10 个(覆盖主流任务类型)
   - 边界 case 3-5 个(空输入 / 矛盾需求 / 角色冲突)
   - 反模式 case 2-3 个(故意给坏输入,看 LLM 会不会乱来)

2. **每个 case 都要有 `description`**——3 个月后看自己写的能看懂。

3. **不要追求精确匹配 expected**。LLM 输出每次不一样,用 `confidence_range` / `subtask_count >= X` / forbidden 这类**容忍度**判定。

4. **case 难度递增**:case_001 是最简单的,后面越来越难。这样跑 dataset 时能看到哪一档失败。

5. **case 数量上限 30**。超过就拆 dataset(`golden_dataset/regression/` + `golden_dataset/edge_cases/`)。
