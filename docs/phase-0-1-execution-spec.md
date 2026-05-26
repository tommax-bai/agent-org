# Autonomous Multi-Agent 研发系统 - Phase 0-1 Execution Spec

> **文档版本**:v2.4(同步主文档 v2.4 — Phase 0A 开工前的设计收紧)
>
> **文档定位**:开工施工图 / Execution Spec
>
> 本文档**只回答**:第一阶段(Phase 0A / 0B / 0C / 1)到底写哪些文件,跑什么命令,验收什么标准。
>
> **不回答**:为什么这么设计、长期演进、架构哲学(这些在主设计文档里)。
>
> **配套主文档**:`autonomous-agent-system-design.md` v2.4

## 版本变更摘要

### v2.3 → v2.4(2026-05-26)— 5 个开放问题敲死 + 角色配置方案 Y

```text
1. validator 删 autofix 档,只有 RETRY_PM / FATAL 两级(宪法第 12 条 v2.4)
   - B.5 / B.8 改:autofix 描述全部删,改 retry/escalate 两级
2. PM 输出契约 required_roles → role_sequence(显式 step + role_id 结构)
   - B.5 / vocabulary.md / B.7 PM artifact 全改
3. Reviewer artifact 字段重命名 security_or_data_loss_risk → must_escalate_to_owner
   - 加 escalation_reason 字段
   - B.7 / D.4 / A.3.4 role.yaml 全改
4. artifact 加 attempt 字段,同 (subtask, role) 上限 2 次
   - B.4 状态机 needs_changes 路径加 attempt 计数
   - B.7 各 artifact schema 加 attempt 字段
5. Phase 0B mock 边界明确:只 PM 真 LLM,其他角色 mock
   - B.12 / F.3 改
6. 角色配置方案 Y:
   - A.2 目录:roles/ → examples/role_templates/(模板),用户实例去 projects/<x>/roles/
   - A.3.5 project.yaml:删 required: true/false,加 is_orchestrator
   - A.4 完成标准重写
7. schemas/ 加 artifact_content/ 子目录(code/design/review/analysis 各一个 schema)
```

### v2.2 → v2.3(2026-05-25)— 模块边界保护(modular monolith)

```text
1. Phase 0A 目录结构升级:orchestrator/ 子模块都有 __init__.py + _internal/
2. Phase 0A 新增 importlinter.cfg(模块边界强制规则)
3. Phase 0A 新增 docs/module_boundaries.md
4. Phase 0A 完成标准加 4 个新项(目录骨架、import-linter、CI、coding subagent prompt)
5. pyproject.toml 声明 import-linter 依赖
```

### v2.1 → v2.2(2026-05-25)— 一致性压平 + codex review 整合

```text
1. 状态机 Phase 0B/1 全部改为 PM_PLANNING + DISPATCH 循环
2. 新增 dispatch_policy.yaml 模板(Phase 0A)
3. 新增 dispatch_plan validator(Phase 0B,确定性代码)
4. signal schema 改为 immediate_escalate_required(替代 risk_class+keyword)
5. 4 个核心角色 artifact 子 schema
6. Phase 4 拆为 4A/4B
7. Phase 2 加 executor 最小保护
8. constitution.md 升级到 12 条(加 LLM 输出+确定性兜底原则)
9. 全文术语/版本统一
```

### v2.0 → v2.1(2026-05-24)— 角色创建工程实践

```text
1. Phase 0A 目录结构加 meta_prompts/、scripts/、roles/_template/、docs/(role_prompt_structure 等)
2. Phase 0A 完成标准加 meta_prompts 生成器、模板就位
3. 主文档 B 域加"角色创建的工程实践"详细段落
4. 定位:meta_prompts 是"启动门槛工具",不全自动,Owner review 后提交
```

## 版本变更摘要

### v1.2 → v2.0(2026-05-24)— 同步主文档 v2.0 范式升级

**重大修订**:从"固定角色"范式升级到"动态角色"范式(Orchestrator-Worker)。

```text
1. 全局词汇表:加 dispatch / role_invocation_protocol / role_groups / business_breakdown
2. PM 输出契约重写:加 business_breakdown / required_roles / role_dispatch_notes
3. 删除独立的 Architect/Developer/Reviewer 契约,统一为 role_invocation_protocol
4. 状态机重写:固定流程 → PM_PLANNING + DISPATCH 循环
5. events.jsonl 示例更新
6. Phase 0A constitution.md 改为 11 条宪法
7. Phase 0A project.yaml 加 roles / role_groups 配置
8. Phase 0B mock 改 DISPATCH 模式
9. Phase 1 完成标准重写
```

### v1.1 → v1.2(2026-05-24)— 同步主文档 v1.4

```text
1. Reviewer 输出契约扩展:加 correctness/design_quality/test_coverage 字段
2. 失败处理简化:任务失败只写 H1a 结构化记录,不做 PM distillation 自动写入
3. Phase 0-1 完成标准微调
4. 同步主文档变更:H 域收缩、B5/H5 合并、F1 单 reviewer
```

### v1.0 → v1.1(2026-05-24)— 同步主文档 v1.2

```text
1. 宪法第 2 条同步修订(角色不直接调用,可发 signals)
2. 全局词汇表加 signals 相关词汇
3. event schema 加 SIGNAL_RECEIVED 事件类型
4. PM / Architect / Developer / Reviewer 4 个输出契约加 signals_to_other_roles 字段
5. 新增 B.8.5 调度者对 signals 的处理规则
6. 状态机加 signals 触发的额外路径(回炉、escalate)
7. events.jsonl 示例加 SIGNAL_RECEIVED
8. Phase 0B 和 Phase 1 完成标准加 signals 验证
9. 新增 F.7 / F.8 FAQ 说明 signals 用法
```

---

## 0. 这份 Spec 的边界

### 0.1 包含什么

```text
✅ Phase 0A: 文件骨架 (2-3 天)
✅ Phase 0B: 最小 runtime (2-3 天)
✅ Phase 0C: 基础设施替换 (2-3 天)
✅ Phase 1:  单任务 LLM 闭环 (1 周)
```

### 0.2 不包含什么

```text
❌ Phase 2-5 (Git worktree / 质量门 / 记忆 / 多项目)
❌ Postgres 在 0A/0B 阶段不引入
❌ Langfuse 在 0A/0B 阶段不引入
❌ Curator / Memory Service
❌ Markdown sync
❌ 飞书 bot
❌ GitHub PR / auto-merge
❌ Reviewer Panel / Arbiter
❌ pgvector
```

### 0.3 唯一目标

**验证最小自治闭环**:

```text
Owner 写一个 task.yaml
  ↓
PM 调真实 LLM,输出结构化理解
  ↓
Architect 调真实 LLM,复核 PM 输出
  ↓
Orchestrator 推进状态机
  ↓
Developer mock 执行(返回固定结果)
  ↓
Reviewer 调真实 LLM 或 mock 审查
  ↓
成功 → 生成 final_report.md
失败 → 生成 escalation.md
  ↓
全过程写 events.jsonl(0A/0B)→ Postgres(0C)
```

只要这个闭环跑通,再接 Git、Claude Code、CI、记忆系统。

---

## Part A:Phase 0A — 文件骨架(2-3 天)

### A.1 目标

只建文件,不写代码。

### A.2 完整目录结构(v2.3)

```text
agent-org/
├── README.md
├── constitution.md                   # 12 条系统宪法(v2.4)
├── CLAUDE.md                          # 给 Claude Code 的项目说明
├── pyproject.toml                     # Python 项目配置(声明 import-linter 依赖)
├── importlinter.cfg                   # v2.3: 模块边界强制规则
├── .gitignore
│
├── examples/                         # v2.4: framework 提供的"参考模板"(方案 Y)
│   └── role_templates/               # Owner 从这里拷贝起步,不是系统内置
│       ├── _template/                # v2.1: 通用模板目录(任何 role 起步)
│       │   ├── role.yaml
│       │   ├── system_prompt.md
│       │   ├── golden_dataset/
│       │   │   └── README.md
│       │   └── README.md
│       ├── pm/                       # PM 参考实现(可拷贝改)
│       ├── developer/                # Developer 参考实现
│       ├── reviewer/                 # Reviewer 参考实现
│       └── architect/                # Architect 参考实现
│
├── meta_prompts/                     # v2.1: LLM 辅助生成 prompt/dataset
│   ├── generate_role_prompt.md
│   ├── generate_golden_dataset.md
│   └── README.md
│
├── scripts/
│   ├── generate_role_prompt.py
│   └── generate_golden_case.py
│
├── projects/                         # v2.4: 用户项目实例(每个项目自己的 roles/)
│   ├── example-api/
│   │   ├── project.yaml              # 含 is_orchestrator 配置
│   │   ├── dispatch_policy.yaml      # mandatory_role_rules
│   │   └── roles/                    # 该项目实际用的角色(Owner 自己配)
│   │       ├── pm/                   # 从 examples/role_templates/pm/ 拷过来改
│   │       ├── developer/
│   │       └── reviewer/
│   └── README.md
│
├── tasks/
│   ├── inbox/
│   │   └── task-2026-05-24-001.yaml
│   ├── active/                       # .gitignore
│   ├── done/                         # .gitignore
│   └── failed/                       # .gitignore
│
├── runs/                              # .gitignore
│
├── schemas/
│   ├── task.schema.json
│   ├── event.schema.json
│   ├── role.schema.json              # v2.4: 加 is_orchestrator: boolean
│   ├── project.schema.json           # v2.4: 加"恰好一个 role is_orchestrator: true"约束
│   ├── dispatch_policy.schema.json
│   ├── role_invocation.schema.json   # v2.4: artifact 加 attempt 字段
│   ├── pm_dispatch_plan.schema.json  # v2.4: 用 role_sequence 结构(step+role_id)
│   ├── artifact_content/             # v2.4: 按 artifact.type 分的子 schema
│   │   ├── code.schema.json
│   │   ├── design.schema.json
│   │   ├── review.schema.json        # 含 must_escalate_to_owner + escalation_reason
│   │   ├── dispatch_plan.schema.json # PM 的 artifact.content schema
│   │   └── analysis.schema.json
│   └── vocabulary.md
│
├── orchestrator/                      # v2.3: modular monolith 骨架(Phase 0A 建)
│   ├── __init__.py
│   ├── _runtime/                     # 入口层
│   │   └── __init__.py
│   ├── state_machine/                # 状态机模块
│   │   ├── __init__.py               # public API
│   │   └── _internal/                # 私有实现
│   │       └── __init__.py
│   ├── dispatcher/                   # DISPATCH 模块
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── roles/                        # 角色调用框架(不是 role 配置)
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── llm/                          # LLM 抽象
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── memory/                       # 记忆访问
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── event_log/                    # 事件存储
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── artifact/                     # 产物存储
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── budget/                       # 成本管理
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   ├── escalation/                   # 升级通知
│   │   ├── __init__.py
│   │   └── _internal/
│   │       └── __init__.py
│   └── _shared/                      # 跨模块基础设施
│       ├── __init__.py
│       └── types.py                  # 共享类型(Task / Subtask 等)
│
└── docs/
    ├── role_prompt_structure.md      # v2.1
    ├── golden_dataset_format.md      # v2.1
    ├── module_boundaries.md          # v2.3: 模块边界保护说明
    ├── poc-results.md                # 0C 跑完才填
    ├── operations/
    │   ├── coding-subagent-prompt.md
    │   └── ops-subagent-prompt.md
    └── decisions/                    # 设计决策日志
```

**v2.3 关键变化**:

- 每个 orchestrator 子模块都有 `__init__.py` + `_internal/` 子目录
- Phase 0A 时这些都是空的(`__init__.py` 暂时只放注释说明)
- Phase 0B 写代码时,实现放进 `_internal/`,public API 在 `__init__.py` 显式 export
- `importlinter.cfg` 在 Phase 0A 就建好(规则可以从空开始,但配置文件先在)

### A.2.5 importlinter.cfg 模板(v2.3)

```ini
[importlinter]
root_package = orchestrator
include_external_packages = True

# 规则 1:跨模块禁止访问 _internal
[importlinter:contract:no_cross_internal_access]
name = No cross-module access to _internal
type = forbidden
source_modules =
    orchestrator.state_machine
    orchestrator.dispatcher
    orchestrator.roles
    orchestrator.llm
    orchestrator.memory
    orchestrator.event_log
    orchestrator.artifact
    orchestrator.budget
    orchestrator.escalation
forbidden_modules =
    orchestrator.state_machine._internal
    orchestrator.dispatcher._internal
    orchestrator.roles._internal
    orchestrator.llm._internal
    orchestrator.memory._internal
    orchestrator.event_log._internal
    orchestrator.artifact._internal
    orchestrator.budget._internal
    orchestrator.escalation._internal
allow_indirect_imports = false

# 规则 2:分层架构(上层可调下层,下层不能调上层)
[importlinter:contract:layered_architecture]
name = Layered architecture
type = layers
layers =
    orchestrator._runtime
    orchestrator.state_machine
    orchestrator.dispatcher
    orchestrator.roles
    orchestrator.llm
    orchestrator.memory | orchestrator.event_log | orchestrator.artifact | orchestrator.escalation | orchestrator.budget
    orchestrator._shared
```

**CI 集成**(GitHub Actions 示例):

```yaml
- name: Check module boundaries
  run: |
    pip install import-linter
    lint-imports
```

也可加到 pre-commit hook(可选,V1 不强制)。

### A.3 关键文件模板

#### A.3.1 `examples/role_templates/developer/role.yaml`(v2.4 位置改)

```yaml
role_id: developer
version: v0.1.0
name: Developer
description: 实现代码改动

model_policy:
  preferred: claude-sonnet-4-5
  fallback:
    - codex

capabilities:
  - read_code
  - modify_code
  - run_tests

inputs:
  required:
    - task_context
    - repo_path
    - implementation_plan

outputs:
  required:
    - summary
    - files_changed
    - commands_run
    - known_risks

safety:
  forbidden:
    - delete_repository
    - modify_secrets
    - force_push

budget:
  per_invocation_usd_max: 5
```

#### A.3.2 `examples/role_templates/pm/role.yaml`(v2.4 位置改)

```yaml
role_id: pm
version: v0.1.0
name: PM
description: 任务理解、拆解、智能建议

model_policy:
  preferred: claude-sonnet-4-5

capabilities:
  - understand_task
  - decompose_task
  - propose_plan

inputs:
  required:
    - owner_request
    - project_context

outputs:
  required:
    - parsed_intent
    - assumptions
    - complexity
    - proposed_plan
    - required_context
    - risks
    - confidence

budget:
  per_invocation_usd_max: 3
```

#### A.3.3 `examples/role_templates/architect/role.yaml`(v2.4 位置改)

```yaml
role_id: architect
version: v0.1.0
name: Architect
description: 复核 PM 的任务理解和计划

model_policy:
  preferred: claude-opus-4-7

capabilities:
  - review_decomposition
  - identify_risks

inputs:
  required:
    - pm_output
    - project_context

outputs:
  required:
    - verdict   # approved | changes_requested | reject
    - concerns
    - required_changes
    - suggested_execution_order

budget:
  per_invocation_usd_max: 3
```

#### A.3.4 `examples/role_templates/reviewer/role.yaml`(v2.4 位置改)

```yaml
role_id: reviewer
version: v0.1.0
name: Reviewer
description: 审查 Developer 产出

model_policy:
  preferred: claude-sonnet-4-5

inputs:
  required:
    - original_task
    - pm_output
    - architect_review
    - developer_output

outputs:
  required:
    - verdict   # approve | request_changes | reject
    - blocking_issues
    - non_blocking_issues
    - must_escalate_to_owner       # v2.4:替代 security_or_data_loss_risk
    - escalation_reason            # v2.4:must_escalate=true 时必填
    - suggested_fixes

budget:
  per_invocation_usd_max: 3
```

#### A.3.5 `projects/example-api/project.yaml`(v2.4 方案 Y)

```yaml
project_id: example-api
name: Example API
repo_url: git@github.com:owner/example-api.git
main_branch: main

# Phase 0 阶段这些不用,占位
local_main_path: /srv/agent-projects/main/example-api
worktree_root: /srv/agent-projects/worktrees/example-api

commands:
  install: pnpm install
  test: pnpm test
  lint: pnpm lint

# v2.4 方案 Y:所有角色都是 Owner 配,framework 不预设
# 唯一硬约束:恰好一个 role 标 is_orchestrator: true(担任 PM 职责)
# Owner 从 examples/role_templates/ 拷贝想要的到 projects/<x>/roles/ 再改
roles:
  - role_id: pm
    description: "业务拆解 + 角色调度(任务编排者)"
    is_orchestrator: true   # framework 唯一硬约束
  - role_id: developer
    description: "代码实现"
  - role_id: reviewer
    description: "产物审查 + 质量评估"
  - role_id: architect
    description: "系统设计(可选,复杂任务才用)"

# v2.0 新增:任务类型 → 默认角色组
# PM 识别任务类型后,用对应模板作为起点(允许加减,但要发 signal)
role_groups:
  simple_feature:
    description: "简单 CRUD、明确需求"
    roles: [developer, reviewer]
  
  complex_feature:
    description: "涉及多模块、需要系统设计"
    roles: [architect, developer, reviewer]
  
  bug_fix:
    description: "Bug 修复"
    roles: [developer, reviewer]
  
  refactor:
    description: "重构、性能优化"
    roles: [architect, developer, reviewer]

# 三级 protected paths
protected_paths:
  hard_block:
    - .env
    - .env.*
    - secrets/
    - private_keys/
    - .github/workflows/deploy.yml
  approval_required:
    - package.json
    - pnpm-lock.yaml
    - Dockerfile
    - migrations/
  warn_only:
    - README.md
    - docs/
```

#### A.3.5.b `projects/example-api.dispatch_policy.yaml`(v2.2 新增)

```yaml
# 强制角色规则(validator 必须强制执行)
mandatory_role_rules:
  - id: security_sensitive_task
    if_any:
      task_contains:
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
    require_roles:
      - reviewer
    require_approval_gate: true

# PM 偏离模板的权限
pm_deviation_policy:
  can_add_roles: true
  can_remove_template_roles: true
  cannot_remove_mandatory_roles: true
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
    rationale: "文档类任务,即使提到 auth/OAuth 也不需要 security review"
```

#### A.3.6 `tasks/inbox/task-2026-05-24-001.yaml`(示例任务)

```yaml
task_id: task-2026-05-24-001
title: Fix login timeout bug
project_id: example-api
priority: normal

owner_request: |
  修复登录接口偶发 timeout 的问题,并补充测试。
  
  现象:用户在网络较差时,登录请求会偶发 30 秒后才返回。
  期望:超时机制更合理(5-10 秒),并加上重试。

constraints:
  - 不允许修改数据库 schema
  - 不允许改动认证协议

success_criteria:
  - 相关测试通过
  - reviewer 通过
  - 生成 final_report.md

budget_usd: 20
```

#### A.3.7 `schemas/task.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Task",
  "type": "object",
  "required": ["task_id", "title", "project_id", "owner_request"],
  "properties": {
    "task_id": {"type": "string", "pattern": "^task-[0-9]{4}-[0-9]{2}-[0-9]{2}-[0-9]+$"},
    "title": {"type": "string", "maxLength": 100},
    "project_id": {"type": "string"},
    "priority": {"enum": ["low", "normal", "high", "urgent"]},
    "owner_request": {"type": "string", "minLength": 10},
    "constraints": {"type": "array", "items": {"type": "string"}},
    "success_criteria": {"type": "array", "items": {"type": "string"}},
    "budget_usd": {"type": "number", "minimum": 0, "maximum": 1000}
  }
}
```

#### A.3.8 `schemas/event.schema.json`

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Event",
  "type": "object",
  "required": ["time", "task_id", "type", "actor"],
  "properties": {
    "time": {"type": "string", "format": "date-time"},
    "task_id": {"type": "string"},
    "type": {
      "enum": [
        "TASK_CREATED",
        "STATE_CHANGED",
        "DISPATCH_DECISION",
        "ROLE_INVOKED",
        "ROLE_RETURNED",
        "SIGNAL_RECEIVED",
        "BUDGET_CONSUMED",
        "ESCALATED",
        "TASK_COMPLETED",
        "TASK_FAILED"
      ]
    },
    "actor": {"type": "string"},
    "payload": {"type": "object"}
  }
}
```

#### A.3.9 `schemas/vocabulary.md`(D1 全局词汇表)

```markdown
# Vocabulary - 全局词汇表

> 所有 role 的 input/output 字段必须使用本词汇表里的标准词。

## 任务相关
- task_id: 任务唯一标识
- subtask_id: 子任务唯一标识(v2.0)
- owner_request: Owner 原始需求文本
- parsed_intent: 解析后的意图
- success_criteria: 成功标准

## 业务拆解 (v2.0 新增 / v2.4 role_sequence)
- business_breakdown: PM 输出的业务子任务列表
- subtask: 业务子任务,含 description / task_type / role_sequence / dependencies
- task_type: 任务类型(simple_feature / complex_feature / bug_fix / refactor / ...)
- role_sequence: 该子任务的角色执行顺序(v2.4 替代 required_roles)
  - 结构:[{step: 1, role_id: X}, {step: 2, role_id: Y}, ...]
  - 顺序由 step 字段决定,list 位置无语义
  - dispatcher 按 step 排序派活
- role_dispatch_notes: PM 对角色调度的说明(偏离默认模板时记录原因)

## 角色调用 (v2.0 改:统一 role_invocation_protocol)
- role_invocation_input: 调度者调用角色的标准输入
- role_invocation_output: 角色返回给调度者的标准输出
- context_pack: 调度者为角色准备的上下文
- artifact: 角色产生的产物
- artifact_id: 产物唯一标识,可被后续角色引用

## 决策相关
- verdict: 角色返回的判定 (success | needs_changes | escalate)
- assumptions: 假设清单
- confidence: 置信度 (0.0-1.0)
- concerns: 关注点列表

## 状态相关
- state: 任务当前状态
- transition: 状态转换
- escalation: 升级事件
- budget: 预算
- cost_used: 已消耗成本

## 状态机节点 (v2.0)
- PM_PLANNING: PM 业务拆解 + 角色调度阶段(任务入口,一次性)
- DISPATCH: 调度者派活的核心节点(循环)
- ROLE_EXECUTING: 角色执行中
- ESCALATED_TO_OWNER: 升级给 Owner

## Signals 相关
- signals_to_other_roles: 角色发给其他角色的信号列表(可选输出字段)
- signal_target: 信号目标角色(角色 id,由 project.yaml 定义)
- signal_type: 信号类型
  - question: 提问,需要被询问角色回应才能继续
  - concern: 关注点,提醒对方注意但不阻塞
  - suggestion: 建议,被建议角色下次执行时可参考
  - collaboration_request: 协作请求
- signal_severity: low | medium | high
- signal_content: 自然语言描述
- immediate_escalate_required: boolean (v2.2 新增,默认 false)
- immediate_escalate_reason: string (当 immediate_escalate_required=true 时必填)

## Dispatch 相关 (v2.2 新增 / v2.4 role_sequence)
- dispatch_plan: PM 输出的执行计划(含 business_breakdown + role_sequence)
- normalized_dispatch_plan: validator 校验后的计划(才能被 DISPATCH 执行)
- dispatch_policy: Owner 配置的强制规则(mandatory_role_rules + pm_deviation_policy)
- mandatory_role_rules: dispatch_policy 的硬规则(validator 必须强制执行)
- pm_deviation_policy: PM 偏离 role_groups 模板的权限
- role_dispatch_notes: PM 偏离模板时的说明(deviation_type + reason)
```

#### A.3.10 `constitution.md`

```markdown
# 系统宪法

> 这是系统的根本原则。任何工具、实现选择都不能违反这些原则。

## 1. 任务间并行,任务内串行
- 任务间:每个 task 有独立 worktree + 独立 task_id,默认可并行
- 任务内:子任务按依赖顺序,角色按 PM 调度顺序执行
- 唯一硬约束:同一 worktree 同时只跑一个 task(自动满足)

## 2. 角色不直接调用对方,但可以在输出里发 signals
- 允许:在输出 signals_to_other_roles 字段里引用其他角色产出、提出疑问、给反馈
- 禁止:角色凭意志直接 invoke 另一个角色,或直接修改对方产出
- 调度者读 signals 决定下一步流向

## 3. 项目之间完全隔离
简单性与安全性。

## 4. PM 是任务编排者,调度者是执行者(v2.0)
- PM 做业务拆解 + 角色调度(决定调用哪些角色)
- PM 不做技术决策、不写代码、不审查
- 调度者按 PM 决定派活,纯确定性,不做语义判断
- 各个角色(Architect、Developer、Reviewer 等)做自己专业范围的工作
(Orchestrator-Worker 范式)

## 5. 角色由 Owner 配置,不固定数量(v2.0 / v2.4 落实方案 Y)
- 所有角色(包括 PM)都是 Owner 配置,framework 不预设
- role.yaml + system_prompt.md 即可注册新角色
- framework 唯一硬约束:project.yaml 里恰好一个角色标 is_orchestrator: true
- 起步路径:从 examples/role_templates/ 拷贝想要的角色到 projects/<x>/roles/ 改
- project.yaml 配置 role_groups 模板(任务类型 → 默认角色组,PM 起点)
- 角色必须遵守 role_invocation_protocol
- 简单任务可不调用 Architect,复杂任务可调用多个 reviewer

## 6. 质量来自结构化评估 + 硬护栏
- 单 LLM Reviewer + 结构化 rubric + 硬护栏 + golden dataset 回归

## 7. 硬护栏在基础设施层强制,不靠 LLM 判断
安全底线。

## 8. "更新 agent" 完全是 Owner 决定
系统只沉淀数据,所有改进决策权在 Owner。

## 9. 所有决策可解释、可追溯
可调试性。

## 10. 失败和介入沉淀为数据,辅助 Owner 改进
系统不自动改自己,Owner 看数据改 prompt。

## 11. Owner 不在 loop 里 review,但始终在 loop 里改进系统
Autonomous != 失控。

## 12. LLM 输出 + 确定性兜底(v2.4 修订)
- LLM 输出 = 起点,不是终点
- 确定性代码(validator / hard guardrails)= 兜底
- **兜底只能 retry 或 escalate,不能替 LLM 补漏**
- 理由:autofix 让 LLM 失败模式被掩盖 + 模糊职责边界 + 兜底机制本身脆弱
- retry 必须有硬上限(默认 1 次,可配置),超过即 escalate
- 兜底机制本身必须可靠;不可靠的兜底(如关键词匹配 signal 内容)反而是噪声
- 所有 LLM 输出的异常 / retry / escalation 都记到 event log
```

### A.4 Phase 0A 完成标准(v2.4)

```text
[ ] agent-org repo 创建,所有目录就位(含 meta_prompts/ scripts/ examples/role_templates/)
[ ] examples/role_templates/_template/ 通用模板就位(role.yaml + system_prompt.md + golden_dataset/)
[ ] examples/role_templates/{pm,developer,reviewer,architect}/ 各自的 role.yaml + system_prompt.md 写完
    (这些是参考模板,Owner 启动项目时拷到自己 projects/<x>/roles/ 改)
[ ] projects/example-api/roles/ 至少有 pm 一份(从 templates 拷过来,改成 is_orchestrator: true)
[ ] PM 的 system_prompt 必须包含:业务拆解逻辑 + 角色调度决策(role_sequence 结构)
    + signal severity + immediate_escalate 判定
[ ] constitution.md 落地(v2.4 12 条,第 12 条删 autofix 档)
[ ] vocabulary.md 落地(v2.4 含 business_breakdown / role_invocation_protocol / role_sequence
    / dispatch_plan / dispatch_policy / must_escalate_to_owner / attempt 等词汇)
[ ] docs/role_prompt_structure.md 落地(说明 6 段标准结构)
[ ] docs/golden_dataset_format.md 落地(说明 case 格式)
[ ] docs/module_boundaries.md 落地(v2.3:说明 _internal/ 约定 + 跨模块 import 规则)
[ ] meta_prompts/generate_role_prompt.md 落地
[ ] meta_prompts/generate_golden_dataset.md 落地
[ ] scripts/generate_role_prompt.py 落地(简单 CLI 包装,验证能调通 Claude API)
[ ] 至少 1 个 project.yaml(含 roles 列表,**恰好一个 is_orchestrator: true** + role_groups 配置)
[ ] 至少 1 个 dispatch_policy.yaml(含 mandatory_role_rules / pm_deviation_policy)  # v2.2
[ ] 至少 1 个 task.yaml(放在 tasks/inbox/)
[ ] schema 文件就位(role_invocation / pm_dispatch_plan / dispatch_policy / events / artifact_content/* 等)
[ ] schemas/artifact_content/{code,design,review,dispatch_plan,analysis}.schema.json 各就位
    - review.schema.json 含 must_escalate_to_owner + escalation_reason
    - pm_dispatch_plan 用 role_sequence(step + role_id)结构
[ ] role.schema.json 含 is_orchestrator: boolean(v2.4)
[ ] project.schema.json 含约束:恰好一个 role 标 is_orchestrator: true(v2.4)
[ ] 用 jsonschema 工具校验示例 task.yaml / project.yaml / dispatch_policy.yaml
[ ] importlinter.cfg 落地(v2.3:模块边界规则)
[ ] orchestrator/ 子模块骨架建好(每个模块都有 __init__.py + _internal/)
[ ] pyproject.toml 声明 import-linter 依赖
[ ] CI 跑通 lint-imports(空规则也算通过)
[ ] coding-subagent-prompt.md 包含"模块边界纪律"段 + v2.4 多层设计警惕
[ ] docs/decisions/ 写 v2.4 三条 ADR(no-autofix / all-roles-owner-configured / artifact-attempt-versioning)
[ ] git init + 全部提交
```

**Phase 0A 不能进入 0B 的标志**:
- 任何一项 yaml 通不过 schema 校验
- project.yaml 缺 role_groups 或不止一个 is_orchestrator: true(v2.4)
- dispatch_policy.yaml 缺 mandatory_role_rules
- meta_prompts 生成器跑不通
- **importlinter.cfg 没建,或者目录骨架不符合 _internal/ 约定**(v2.3 新增硬条件)
- schemas/artifact_content/ 子目录不全(v2.4 新增硬条件)

**v2.3 新增的工程实践**:

- `_internal/` + `__init__.py` 显式 public API 是 modular monolith 的基础
- import-linter 强制 enforcement
- coding subagent 写代码时遵守模块边界纪律
- 详见主文档 v2.3 Part IV"模块边界保护"段

---

## Part B:Phase 0B — 最小 runtime(2-3 天)

### B.1 目标

跑通最小状态机,不接任何外部基础设施。

### B.2 关键约束

```text
❌ 不接 Postgres,事件写 events.jsonl 文件
❌ 不接 Git worktree,Developer mock
❌ 不接 Claude Code CLI,直接调 Anthropic API
❌ 不接 Langfuse,用 structlog 写本地 JSON
✅ 只有 PM 调真实 LLM(状态机入口需要真实 dispatch_plan 喂给 DISPATCH 循环)
✅ 其他角色(Developer / Reviewer / Architect)全 mock(返符合 schema 的固定/随机数据)
✅ Phase 1 才把其他角色换成真 LLM
```

**v2.4 修订**:0B 阶段 mock 边界明确为"只 PM 真 LLM"。0B 的目标是验证
状态机 + dispatch validator + signals 路径 + attempt 上限,这些跟 LLM
输出内容无关,只跟结构有关。Reviewer 跑真 LLM 看 mock Developer 的固定
数据没有验证价值。

### B.3 目录新增

```text
agent-org/
└── orchestrator/
    ├── __init__.py
    ├── __main__.py                    # 命令行入口
    ├── runtime.py                     # 主循环
    ├── state_machine.py               # 状态推进
    ├── event_log.py                   # events.jsonl 写入
    ├── dispatcher.py                  # v2.0: DISPATCH 节点逻辑
    ├── roles/                         # 角色执行器
    │   ├── __init__.py
    │   ├── base.py                    # RoleRunner 抽象(实现 role_invocation_protocol)
    │   ├── pm.py                      # PM(任务编排者)
    │   ├── role_runner.py             # 通用角色 runner(架构 / 开发 / 审查都用)
    │   └── mock_developer.py          # mock 实现(0B 阶段)
    ├── llm.py                         # LLM 调用包装(Anthropic SDK)
    ├── budget.py                      # 预算跟踪
    └── escalation.py                  # 生成 escalation.md
```

### B.4 状态机定义(v2.0 — DISPATCH 循环,v2.4 加 attempt 上限)

```text
CREATED
  ↓
PM_PLANNING (一次性,任务入口)
  ↓ (PM 输出 business_breakdown + role_sequence)
  ↓ validator 校验 → PASS / RETRY_PM(上限 1 次) / FATAL
  ↓ (v2.4:删除 autofix 档,只 retry/escalate)
DISPATCH (循环节点)
  ├── 找到下一个 ready role(按 role_sequence.step 排序) → ROLE_EXECUTING
  ├── 没有 ready role → DONE
  ├── HIGH_SIGNALS_OVERFLOW (累计 high ≥ 3) → ESCALATED_TO_OWNER
  └── BUDGET_EXCEEDED → ESCALATED_TO_OWNER
ROLE_EXECUTING
  ↓ (角色返回 role_invocation_output)
  ├── verdict=success → 标记该角色完成 → 回到 DISPATCH
  ├── verdict=needs_changes → (v2.4)
  │     ├── 找到上游角色(role_sequence 里前一个 step)
  │     ├── 该上游角色的 (subtask, role) attempt + 1
  │     ├── if attempt > 2 → ATTEMPT_LIMIT_REACHED → ESCALATED_TO_OWNER
  │     └── else → 标记上游角色 pending(产生新 attempt) → 回到 DISPATCH
  └── verdict=escalate → ESCALATED_TO_OWNER

任何阶段:
  - HIGH_SEVERITY_SIGNAL → 按 signal 处理规则改变流向(见 B.8.5)
  - LLM_FAILED (重试 2 次后) → ESCALATED_TO_OWNER
  - 一致性校验失败(如 Reviewer must_escalate=true 但 verdict 不是 reject)
    → RETRY_LLM 1 次 → 还失败 → ESCALATED_TO_OWNER
```

**关键变化(v2.0)**:状态机不再写死流程。DISPATCH 节点根据 `task_state.pending_roles` 动态决定下一个调用谁。PM 决定调用顺序,状态机只是执行。

**关键点**:状态机除了看角色的 verdict,还要看 signals_to_other_roles。verdict 决定主线流向,signals 提供回炉、escalate 的额外触发点。详见 B.8.5。

### B.5 PM 输出契约(v2.0 / v2.4 role_sequence)

```yaml
pm_planning_output:
  parsed_intent: |
    简洁描述任务要做什么
  
  assumptions:
    - id: A1
      content: 假设用户没有特殊的 timeout 偏好
      risk: low
    - id: A2
      content: 假设当前认证用 JWT
      risk: medium
  
  complexity:
    level: low | medium | high
    reasons:
      - 改动范围小
      - 不涉及数据库
  
  # v2.0 核心:业务拆解 + 角色调度;v2.4 role_sequence 结构
  business_breakdown:
    - subtask_id: subtask-001
      description: "在 login handler 加 timeout 配置"
      task_type: bug_fix
      success_criteria:
        - timeout 配置生效
        - 测试通过
      role_sequence:                # v2.4:替代 required_roles
        - step: 1                   # 顺序由 step 决定,list 位置无语义
          role_id: developer
        - step: 2
          role_id: reviewer
      dependencies: []
    - subtask_id: subtask-002
      description: "加 timeout 测试"
      task_type: simple_feature
      success_criteria:
        - 测试覆盖正常 + 超时场景
      role_sequence:
        - step: 1
          role_id: developer
        - step: 2
          role_id: reviewer
      dependencies: [subtask-001]
  
  # v2.0:角色调度的说明(只在偏离默认模板时填写)
  role_dispatch_notes: []
  # 示例:如果某子任务加了非默认角色
  # role_dispatch_notes:
  #   - subtask: subtask-002
  #     deviation_from_template: "加了 security_reviewer"
  #     reason: "涉及认证敏感"
  
  required_context:
    files_or_dirs:
      - src/auth/login.go
      - src/auth/middleware.go
  
  risks:
    - 改动可能影响现有 session 行为
  
  confidence: 0.85
  
  # 可选:发给其他角色的 signals
  # PM 在第一阶段一般不发 signals
  signals_to_other_roles: []
```

### B.6 角色调用统一协议(role_invocation_protocol,v2.0)

v2.0 删除了独立的 Architect/Developer/Reviewer 契约,改为**所有角色统一协议**。

**调度者调用角色的输入**:

```yaml
role_invocation_input:
  task_id: ...
  subtask_id: ...
  role_id: developer  # 或 architect / reviewer / 任何 Owner 配置的角色
  
  context_pack:
    task_context:
      title: ...
      owner_request: ...
      success_criteria: [...]
    
    business_goal: |
      PM 提供的当前子任务的业务目标
    
    related_artifacts: []  # 前置角色的产物(如 architect 的设计文档)
    
    project_memory: {}  # 相关项目记忆(0B 阶段空,Phase 4 才有)
    
    role_specific_data: {}  # 该角色特定的数据(如 reviewer 的 rubric)
  
  prior_role_signals: []  # 之前角色发给当前角色的 signals
```

**角色返回给调度者的输出**:

```yaml
role_invocation_output:
  role_id: developer
  task_id: ...
  subtask_id: ...
  
  verdict: success | needs_changes | escalate
  
  artifact:
    type: code | design | review | analysis  # 由角色决定
    content: {...}  # 由角色决定具体结构(按 schemas/artifact_content/<type>.schema.json 校验)
    artifact_id: artifact-2026-05-24-abc123  # 不可变 ID
    attempt: 1                                # v2.4:同 (subtask, role) 第几次尝试,从 1
    superseded_by: null                       # v2.4:被哪个新 artifact_id 取代(可选)
  
  # 可选:发给其他角色的 signals
  signals_to_other_roles:
    - target: pm  # 或其他角色 id
      type: question | concern | suggestion | collaboration_request
      severity: low | medium | high
      content: 自然语言描述
      immediate_escalate_required: false  # v2.2 新增,默认 false
      immediate_escalate_reason: ""        # 当 immediate_escalate_required=true 时必填
  
  cost_used:
    llm_tokens: 1234
    duration_ms: 5678
```

### B.7 各角色 artifact 字段的内容约定(角色特定)

虽然 protocol 统一,但每个角色产生的 `artifact.content` 内容不同:

**Architect 角色** (artifact.type = "design"):
```yaml
artifact:
  type: design
  content:
    system_design: |
      系统设计说明
    affected_modules: [...]
    technical_choices: [...]
    suggested_implementation_steps: [...]
```

**Developer 角色** (artifact.type = "code"):
```yaml
artifact:
  type: code
  content:
    summary: 在 src/auth/login.go 加了 timeout 配置
    files_changed:
      - src/auth/login.go
      - src/auth/login_test.go
    commands_run:
      - go test ./auth/...
    known_risks: []
```

**Reviewer 角色** (artifact.type = "review",v2.4 重命名 + 加 reason):
```yaml
artifact:
  type: review
  content:
    must_escalate_to_owner: false           # v2.4:替代 security_or_data_loss_risk
    escalation_reason: ""                   # v2.4:must_escalate=true 时必填
    correctness: 8
    design_quality: 7
    test_coverage: adequate
    blocking_issues: []
    non_blocking_issues:
      - 建议加注释说明 timeout 选择 5s 的理由
```

**Reviewer 的 verdict 规则**:
```
must_escalate_to_owner=true            → verdict=escalate (一票否决)
任一 CI 硬护栏失败                       → verdict=escalate
correctness < 7 或 test_coverage=inadequate → verdict=needs_changes
其他                                     → verdict=success
```

**`must_escalate_to_owner` 触发条件**(写进 Reviewer system_prompt,任一即可):
- 安全风险:代码可能泄露 secret / 绕过认证 / 引入注入漏洞
- 数据损失:不可逆数据丢失(drop / 不可逆 migration / 删备份)
- 合规风险:违反 GDPR / 个人隐私法规
- 生产稳定性:改动核心配置 / 可能引起宕机
- 不可逆架构变更:违反 Architect 核心设计约定
不确定时设为 true,宁可误报。

**一致性校验**(确定性,role runner 出口):
- `must_escalate_to_owner=true` 但 verdict 不是 `escalate` → RETRY_LLM 1 次
- `must_escalate_to_owner=true` 但 `escalation_reason` 空 → RETRY_LLM 1 次
- 还失败 → ESCALATED_TO_OWNER(宪法第 12 条 v2.4:不 autofix)


### B.8 调度者对 signals 的处理规则

调度者读完角色输出后,**先处理 verdict 决定主线流向**,再处理 signals 做副作用:

```python
def process_signals(state, signals):
    for sig in signals:
        # 记录 SIGNAL_RECEIVED 事件(可观察性)
        log_event('SIGNAL_RECEIVED', payload=sig)
        
        # 累计:signal 多了表明系统困惑
        state.signal_count += 1
        if sig.severity == 'high':
            state.high_severity_signals.append(sig)
        
        # 严重信号 → 影响下一步流向
        if sig.severity == 'high':
            if sig.target == 'pm' and sig.type == 'question':
                # 需要 PM 澄清,回炉到 PM_PLANNING
                state.force_next = 'PM_PLANNING'
                state.pm_extra_context = sig.content
            
            elif sig.type == 'concern':
                # 需要 target 角色重新执行
                state.force_re_invoke_role = sig.target
                state.role_extra_context = sig.content
        
        # 中等/低 severity 信号:不阻塞主线,但加进下次 context
        else:
            state.pending_signals_to_inject[sig.target].append(sig)
    
    # 累计太多 signals → 系统困惑,escalate
    if state.signal_count > 5 or len(state.high_severity_signals) >= 3:
        state.force_next = 'ESCALATED_TO_OWNER'
        state.escalation_reason = 'too_many_signals'
```

**关键约束**:

- 调度者**有最终决定权**:角色发 signal 不等于一定被执行
- signal 数量本身是系统健康指标(信号多 = 系统困惑)
- 同一个角色对同一目标连续 3 次 signal 同类型 → 系统循环,强制 escalate

### B.9 events.jsonl 示例(v2.0 DISPATCH 模式)

```json
{"time":"2026-05-24T10:00:00Z","task_id":"task-2026-05-24-001","type":"TASK_CREATED","actor":"owner","payload":{"title":"Fix login timeout bug"}}
{"time":"2026-05-24T10:00:01Z","task_id":"task-2026-05-24-001","type":"STATE_CHANGED","actor":"orchestrator","payload":{"from":"CREATED","to":"PM_PLANNING"}}
{"time":"2026-05-24T10:00:02Z","task_id":"task-2026-05-24-001","type":"ROLE_INVOKED","actor":"pm","payload":{"role":"pm"}}
{"time":"2026-05-24T10:00:08Z","task_id":"task-2026-05-24-001","type":"ROLE_RETURNED","actor":"pm","payload":{"role":"pm","verdict":"success","subtask_count":2,"cost_usd":0.42}}
{"time":"2026-05-24T10:00:08Z","task_id":"task-2026-05-24-001","type":"BUDGET_CONSUMED","actor":"orchestrator","payload":{"used":0.42,"remaining":19.58}}
{"time":"2026-05-24T10:00:09Z","task_id":"task-2026-05-24-001","type":"STATE_CHANGED","actor":"orchestrator","payload":{"from":"PM_PLANNING","to":"DISPATCH"}}
{"time":"2026-05-24T10:00:09Z","task_id":"task-2026-05-24-001","type":"DISPATCH_DECISION","actor":"orchestrator","payload":{"next_role":"developer","subtask_id":"subtask-001","reason":"first ready role"}}
{"time":"2026-05-24T10:00:10Z","task_id":"task-2026-05-24-001","type":"STATE_CHANGED","actor":"orchestrator","payload":{"from":"DISPATCH","to":"ROLE_EXECUTING"}}
{"time":"2026-05-24T10:00:20Z","task_id":"task-2026-05-24-001","type":"ROLE_RETURNED","actor":"developer","payload":{"role":"developer","verdict":"success","subtask_id":"subtask-001","cost_usd":0.85}}
{"time":"2026-05-24T10:00:21Z","task_id":"task-2026-05-24-001","type":"STATE_CHANGED","actor":"orchestrator","payload":{"from":"ROLE_EXECUTING","to":"DISPATCH"}}
{"time":"2026-05-24T10:00:21Z","task_id":"task-2026-05-24-001","type":"DISPATCH_DECISION","actor":"orchestrator","payload":{"next_role":"reviewer","subtask_id":"subtask-001","reason":"developer done"}}
{"time":"2026-05-24T10:00:30Z","task_id":"task-2026-05-24-001","type":"ROLE_RETURNED","actor":"reviewer","payload":{"role":"reviewer","verdict":"success","subtask_id":"subtask-001","cost_usd":0.35}}
{"time":"2026-05-24T10:00:31Z","task_id":"task-2026-05-24-001","type":"DISPATCH_DECISION","actor":"orchestrator","payload":{"next_role":"developer","subtask_id":"subtask-002"}}
... // subtask-002 跑完
{"time":"2026-05-24T10:01:00Z","task_id":"task-2026-05-24-001","type":"STATE_CHANGED","actor":"orchestrator","payload":{"from":"DISPATCH","to":"DONE"}}
{"time":"2026-05-24T10:01:00Z","task_id":"task-2026-05-24-001","type":"TASK_COMPLETED","actor":"orchestrator","payload":{"total_cost_usd":2.15}}
```

**v2.0 新增事件类型**:`DISPATCH_DECISION`(调度者每次派活记录决策依据)

### B.10 命令行使用

```bash
# 跑一个任务
python -m orchestrator run tasks/inbox/task-2026-05-24-001.yaml

# 输出:
# runs/task-2026-05-24-001/
#   events.jsonl
#   pm_planning_output.yaml        # PM 业务拆解 + 角色调度
#   role_outputs/                   # 各角色的输出(按调用顺序)
#     001-subtask-001-developer.yaml
#     002-subtask-001-reviewer.yaml
#     003-subtask-002-developer.yaml
#     004-subtask-002-reviewer.yaml
#   final_report.md (成功时)
#   或
#   escalation.md (失败时)
```

### B.11 escalation.md 模板

```markdown
# Escalation: task-2026-05-24-001

## 任务标题
Fix login timeout bug

## 失败状态
DISPATCH → ESCALATED_TO_OWNER

## 失败原因
Architect (PM 调用的角色之一) verdict=escalate,认为认证机制假设需要先验证

## 上下文
- PM confidence: 0.6 (较低)
- Architect 提出 2 个 concerns
- 已花费: $0.85 / $20

## 详细 trace
- PM 输出见 pm_planning_output.yaml
- Architect 输出见 role_outputs/001-subtask-001-architect.yaml
- Architect 输出见 architect_review.yaml
- 完整事件见 events.jsonl

## 建议 Owner 操作
1. Review Architect 的 concerns
2. 修正 task.yaml 中的描述
3. 重新提交任务
```

### B.12 Phase 0B 完成标准(v2.4)

```text
[ ] python -m orchestrator run <task.yaml> 能跑完
[ ] PM 调真实 LLM(v2.4 明确:0B 只 PM 真 LLM)
[ ] PM 输出符合 pm_planning_output schema(含 business_breakdown + role_sequence v2.4 结构)
[ ] PM 能识别任务类型,从 project.yaml 的 role_groups 模板起步
[ ] PM 能对简单任务和复杂任务选不同角色组(测试:用两个不同 task.yaml 验证)
[ ] Developer / Reviewer / Architect 全 mock(返符合 schema 的固定/随机数据,v2.4)
[ ] DISPATCH 节点按 role_sequence.step 排序派活,不看 list 位置
[ ] validator 失败两级处理(RETRY_PM / FATAL,v2.4 删 autofix)
[ ] retry_pm 上限 1 次,超过 → ESCALATED_TO_OWNER
[ ] 各角色输出含 attempt 字段,同 (subtask, role) attempt 上限 2 次
[ ] needs_changes 路径:产生新 attempt,attempt > 2 → ATTEMPT_LIMIT_REACHED → escalate
[ ] 状态机能从 CREATED → PM_PLANNING → DISPATCH 循环 → DONE 或 ESCALATED
[ ] events.jsonl 包含完整事件流,含 DISPATCH_DECISION / PLAN_RETRY_REQUESTED
    / ATTEMPT_LIMIT_REACHED(不再有 PLAN_AUTOFIXED)
[ ] 失败时生成 escalation.md
[ ] 成功时生成 final_report.md
[ ] 预算超 $20 时强制 ESCALATED_TO_OWNER
[ ] signals_to_other_roles 字段被正确解析
[ ] high severity signal 能正确改变下一步流向
[ ] high signals 累计 ≥ 3 → 强制 escalate
[ ] Reviewer mock 时也要返 must_escalate_to_owner / escalation_reason 字段
[ ] 一致性校验:must_escalate_to_owner=true 但 verdict 不是 escalate → RETRY_LLM
[ ] 总代码量 < 1000 行 Python(v2.0 DISPATCH 比固定状态机略复杂)
```

**Phase 0B 不能进入 0C 的标志**:DISPATCH 循环跑不通,或角色调用 protocol 不一致,或 PM 不能根据任务类型选角色,或 attempt 上限不生效。

---

## Part C:Phase 0C — 基础设施替换(2-3 天)

### C.1 目标

把 0B 的"文件版"runtime 升级到"基础设施版"。**前提:PoC 验证门全部跑通**。

### C.2 PoC 验证清单(开工前必跑)

每个 PoC 给 **1 天硬时间盒**。失败立即走 fallback。

#### C.2.1 LangGraph PoC

```text
任务:用 LangGraph 重写 0B 的状态机
验证:
  [ ] checkpoint 能在 long-running 任务里可靠
  [ ] 中途 kill orchestrator 后从 checkpoint 恢复
  [ ] 节点 timeout 可靠
  [ ] budget exceeded 能硬中断
  [ ] event 可以回放

通过标准:1-4 全部通过。
失败 fallback:保留 0B 的自写状态机,LangGraph 不引入。
结论写入:docs/poc-results.md
```

#### C.2.2 Langfuse PoC

```text
任务:让 0B 的 LLM 调用同时上报 Langfuse
验证:
  [ ] 自部署 Langfuse 能正确接收 trace
  [ ] cost 计算准确(对比 Anthropic 账单)
  [ ] 高频写入稳定(连续跑 10 个任务)

通过标准:1, 2 通过。
失败 fallback:用 structlog 自己实现 trace,UI 用 Postgres + 简单 web。
```

#### C.2.3 Anthropic SDK PoC

```text
任务:跑通 Claude API 调用 + tool use + streaming
验证:
  [ ] tool use 稳定
  [ ] streaming 不卡死
  [ ] error 重试逻辑健康

通过标准:全部通过。
失败 fallback:用 requests 直接调 API。
```

### C.3 工作内容

```text
1. docker-compose.yml 起 Postgres + Langfuse
2. 创建数据库表:
   - tasks
   - task_events (替代 events.jsonl)
3. 0B 的 event_log.py 改写:写 Postgres 而非 jsonl
4. LLM 调用层加 Langfuse instrumentation
5. 备份脚本:每日 pg_dump + Git push 配置
6. docs/poc-results.md 写完
```

### C.4 docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: agent_org
      POSTGRES_USER: agent
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/init.sql:/docker-entrypoint-initdb.d/init.sql:ro
    ports:
      - "127.0.0.1:5432:5432"

  langfuse:
    image: langfuse/langfuse:latest
    depends_on:
      - postgres
    environment:
      DATABASE_URL: postgresql://agent:${POSTGRES_PASSWORD}@postgres:5432/langfuse
      NEXTAUTH_SECRET: ${LANGFUSE_NEXTAUTH_SECRET}
      SALT: ${LANGFUSE_SALT}
    ports:
      - "127.0.0.1:3000:3000"

volumes:
  postgres_data:
```

### C.5 数据库 init.sql(0C 只建任务和事件表,记忆表 Phase 4 才建)

```sql
CREATE DATABASE agent_org;

\c agent_org

CREATE TABLE tasks (
    task_id         TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    title           TEXT,
    status          TEXT NOT NULL,
    state           JSONB,
    budget_usd      REAL,
    cost_used_usd   REAL DEFAULT 0,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE TABLE task_events (
    id              BIGSERIAL PRIMARY KEY,
    task_id         TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    actor           TEXT,
    payload         JSONB,
    occurred_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_task ON task_events(task_id, occurred_at);
CREATE INDEX idx_events_type ON task_events(event_type);
```

### C.6 Phase 0C 完成标准

```text
[ ] docker-compose up 起 Postgres + Langfuse
[ ] 同一个 task.yaml 跑出来,事件全部进 Postgres task_events 表
[ ] Langfuse UI 能看到完整 trace + cost
[ ] docs/poc-results.md 写完,每个 PoC 都有结论
[ ] 任一 PoC 失败,fallback 路径明确(架构不变)
[ ] 备份脚本就位(pg_dump + Git push)
[ ] 失败时,Postgres 状态、Langfuse trace、escalation.md 三者一致
```

**Phase 0C 完成 = Phase 0 整体 ready**,可以进 Phase 1。

---

## Part D:Phase 1 — 单任务 LLM 闭环(1 周)

### D.1 目标(v2.0)

把 Phase 0B 的 mock 角色换成**真实 LLM 调用**(但还不接 Git / Claude Code CLI)。

各角色(developer / reviewer / architect 等)调真实 LLM,基于 role_invocation_protocol 调用。Developer 暂时只输出"伪代码"或"代码改动建议",不真改文件。

### D.2 关键约束

```text
✅ 各角色都是真实 LLM(Claude Sonnet/Opus)
✅ 所有角色遵守统一的 role_invocation_protocol
✅ PM 根据 project.yaml 的 role_groups 决定调用哪些角色
❌ Developer 不真改 Git 仓库
❌ 不创建 worktree
❌ 不跑 CI
❌ 不开 PR
```

### D.3 Developer artifact.content 内容(Phase 1)

```yaml
artifact:
  type: code
  content:
    summary: |
      我会修改 src/auth/login.go 加 timeout 配置
    
    # Phase 1: 用 "proposed_changes" 描述,不真改
    proposed_changes:
      - file: src/auth/login.go
        operation: modify
        description: 在 login handler 第 45 行加 ctx.WithTimeout(5*time.Second)
        diff: |
          @@ -42,7 +42,9 @@
           func Login(w http.ResponseWriter, r *http.Request) {
          +    ctx, cancel := context.WithTimeout(r.Context(), 5*time.Second)
          +    defer cancel()
               ...
      - file: src/auth/login_test.go
        operation: create
        description: 加 timeout 测试用例
    
    proposed_commands:
      - go test ./auth/...
      - go vet ./auth/...
    
    known_risks:
      - context 改动可能影响下游 handler
```

### D.4 Reviewer artifact.content 内容(Phase 1)

Reviewer 看 Developer 的 proposed_changes,基于 LLM 判断"如果按这个改,合理吗"。**不真跑代码**。

```yaml
artifact:
  type: review
  content:
    must_escalate_to_owner: false           # v2.4
    escalation_reason: ""                   # v2.4:must_escalate=true 时必填
    correctness: 8
    design_quality: 7
    test_coverage: adequate
    blocking_issues: []
    non_blocking_issues:
      - 建议加注释说明 5s timeout 的选择理由
```

### D.5 状态机(v2.0:仍然是 DISPATCH 循环)

跟 Phase 0B 一样,只是 ROLE_EXECUTING 节点调真实 LLM。

PM 在 PM_PLANNING 阶段决定 role_sequence(v2.4),调度者按 step 排序派活。

### D.6 Phase 1 重点

1. **LLM 提示词工程**:各角色的 system_prompt.md 真正打磨,特别是 PM(它要会业务拆解 + 角色调度)
2. **错误处理**:LLM 返回不合规 JSON、超时、rate limit 怎么处理
3. **预算追踪**:每个 LLM 调用记录 token + cost,累加到任务总成本
4. **可观察性**:Langfuse 上能完整看一个任务的所有 LLM 调用
5. **任务类型识别**:PM 能识别 task.yaml 属于什么类型,选对应 role_group

### D.7 Phase 1 完成标准(v2.0)

```text
[ ] PM 调真实 LLM,正确输出 business_breakdown + role_sequence(v2.4 结构)
[ ] Developer 调真实 LLM,输出 proposed_changes
[ ] Reviewer 调真实 LLM,输出 rubric(correctness / design_quality / ...)
[ ] Architect(可选)调真实 LLM,输出 system design
[ ] 每个角色的 system_prompt.md 经过至少 3 次迭代
[ ] 每个角色的 system_prompt.md 明确说明何时发 signals_to_other_roles + severity 判定
[ ] 每个角色的输出 100% 符合 role_invocation_output schema(JSON parse 失败率 < 5%)
[ ] LLM 返回不合规时能自动重试(最多 2 次)
[ ] Langfuse 能看到每个角色的 token + cost
[ ] signals 在 5 个示例任务里至少出现 3 次,且调度者处理正确
[ ] 跑 5 个不同复杂度的示例任务(simple_feature / complex_feature / bug_fix / refactor),统计:
    - PM 平均 confidence
    - PM 选角色是否合理(Owner 主观评估)
    - Reviewer approval rate
    - signals 发送频率(每任务平均几个)
    - 平均成本
    - 平均耗时
[ ] 这 5 个任务的 escalation 原因分析归档
[ ] Owner 跑通"提交任务 → PM 拆解 → 看 PR_READY 通知 → 决定下一步"全流程
[ ] 验证范式:简单任务(bug_fix)和复杂任务(complex_feature)走不同角色组
```

---

## Part E:Phase 0-1 整体验收(V1 第一里程碑)

跑完 Phase 0-1,系统应该能做到:

```text
✅ Owner 写一个 task.yaml,提交到 tasks/inbox/
✅ python -m orchestrator run tasks/inbox/xxx.yaml 跑通
✅ PM 真实理解,输出结构化
✅ Architect 真实审查,可以拦截
✅ Developer (LLM) 提出改动建议
✅ Reviewer 真实审查 proposed_changes
✅ 状态机推进,事件入 Postgres
✅ Langfuse 看到完整 trace + cost
✅ 失败时生成 escalation.md
✅ 成功时生成 final_report.md
✅ 全过程在 6 周内完成
```

**还不能做到的**:

```text
❌ 真改代码(Phase 2 的事)
❌ 跑测试(Phase 3 的事)
❌ 开 PR(Phase 3 的事)
❌ 记忆沉淀(Phase 4 的事)
❌ 多项目并行(Phase 5 的事)
```

---

## Part F:常见问题

### F.1 0A 阶段写 system_prompt.md 写不出来怎么办?

写个 50 字的占位就行:

```markdown
# PM System Prompt v0.1

你是一个 Project Manager 角色。

你的工作是:
1. 理解 Owner 提的任务
2. 拆解成可执行的步骤
3. 提出明确的假设和风险

输出必须是 YAML 格式,符合 pm_output 契约。
```

到 Phase 1 才真正打磨 prompt。0A 阶段重点是**结构对**,不是**质量好**。

### F.2 PoC 不通过怎么办?

走 fallback,不影响架构:

```text
LangGraph 不通过 → 保留自写状态机
Langfuse 不通过 → structlog + Postgres
Anthropic SDK 不通过 → requests 直调
```

**不要"调一调说不定行"**。1 天硬时间盒到了就走 fallback。

### F.3 Phase 0B 一定要调真实 LLM 吗?(v2.4 边界明确)

**只有 PM 必须真 LLM,其他角色全 mock**。

理由:0B 阶段要验证的是**状态机 + dispatch validator + signals 路径 + attempt 上限**——
这些跟 LLM 输出**内容**无关,只跟**结构**有关。PM 必须真,因为状态机入口需要真实的
`business_breakdown + role_sequence` 数据来 exercise DISPATCH 各种分支(单/多 subtask、
依赖、强制 escalate 等)。其他角色 mock 返符合 schema 的固定/随机数据就够。

Reviewer 跑真 LLM 看 mock Developer 的固定 proposed_changes,跑 10 次都一样,
**没有验证价值**。Phase 1 才把所有角色换成真 LLM,集中打磨 prompt。

可以让 mock 随机返不同 verdict / signals,exercise 不同分支。

### F.4 schema 校验工具用什么?

Python:`jsonschema`。命令行:`check-jsonschema`。

```bash
pip install jsonschema check-jsonschema
check-jsonschema --schemafile schemas/task.schema.json tasks/inbox/*.yaml
```

### F.5 events.jsonl 在 0B 阶段会不会写丢?

每个 event 一行 JSON,文件每次 append 后 flush + fsync。崩溃最多丢最后一行。

```python
def append_event(event: dict, log_path: Path):
    with log_path.open("a") as f:
        f.write(json.dumps(event) + "\n")
        f.flush()
        os.fsync(f.fileno())
```

### F.6 不想用 LangGraph,直接自写状态机?

可以。0B 阶段本来就是自写。如果 0C 的 LangGraph PoC 通过,**可以选择**升级;不通过就保留自写。

记住:**LangGraph 是实现选择,Orchestrator 是架构决策**。

### F.7 signals 用得多了会不会变 GroupChat?

不会,因为有底线:

```text
1. 角色不在自己的 LLM 调用里 invoke 其他角色(没有 RPC)
2. 调度者读 signals,有最终决定权(没有授权升级)
3. signal 累计 > 5 强制 escalate(没有死循环)
```

signals 是**单向的输出附件**,不是双向对话。Reviewer 发"signal to architect" 不等于 Architect 必定执行——调度者根据规则判断是否触发 Architect 重审。

### F.8 角色的 system_prompt 怎么写 signals 的引导?

每个角色 prompt 加一段:

```markdown
# 关于 signals_to_other_roles

如果你在执行过程中发现需要其他角色注意的事,可以在输出的
signals_to_other_roles 字段里附加 signal。

例如:
- 你是 Developer,发现 PM 的 plan step 2 跟 step 1 冲突
  → 发 signal,target=pm, type=question, severity=high
- 你是 Reviewer,发现 Architect 当时的判断有问题
  → 发 signal,target=architect, type=concern, severity=high
- 你是 Reviewer,有锦上添花的建议
  → 发 signal,target=developer, type=suggestion, severity=low

不要滥用 signals:
- 你能在自己产出里直接解决的问题,不要发 signal
- 不要为了"显得在协作"而硬发 signal
- severity=high 要克制,严重影响主线的才用
```

### F.9 Phase 0 总共多久?

```text
0A: 2-3 天
0B: 2-3 天 (含 signals 实现 0.5 天)
0C: 2-3 天 (PoC 3 天 + 实际改写 0.5 天)

合计: 6-9 天 (大约 1.5 周)
```

加上 Phase 1 的 1 周,Phase 0-1 总共 **2.5-3 周**。

---

## Part G:文档维护

### G.1 这份 Spec 的生命周期

```text
Phase 0-1 期间    本 Spec 是开工施工图,持续更新
Phase 0-1 完成    本 Spec 归档,作为 V1 → V2 的对照
Phase 2 启动      新写 Phase 2 Execution Spec
```

### G.2 跟主设计文档的关系

```text
主文档定义"为什么"和"是什么"
本 Spec 定义"这周写哪几个文件"
冲突时:
  - 如果是设计原则冲突,以主文档为准
  - 如果是实施细节,以本 Spec 为准
  - 任何冲突都要记录到 docs/decisions/ 里
```

### G.3 docs/decisions/ 目录

每次重要决策写一条:

```text
docs/decisions/
  2026-05-24-langgraph-poc-result.md
  2026-05-25-skip-langfuse-for-now.md
  ...
```

格式:决策、理由、影响、回滚方案。

---

## Part H:Phase 0-1 时间预算

```text
Phase 0A (文件骨架)         2-3 天
Phase 0B (最小 runtime)     2-3 天
Phase 0C (基础设施替换)     2-3 天
   ├─ LangGraph PoC          1 天
   ├─ Langfuse PoC           1 天
   └─ 实际集成               0.5-1 天
Phase 1 (单任务 LLM 闭环)   1 周

合计:2.5-3 周
```

**硬时间盒原则**:任何 phase 跑过 1.5 倍预算时间,**强制降级范围**(把没做完的推到下一 phase),不要"再调一调"。

---

## 文档元数据

- 创建日期:2026-05-24(v1.0)
- 最新版本:**v2.4**(2026-05-26,同步主文档 v2.4 — Phase 0A 开工前设计收紧)
- 来源:
  - 主设计文档 v2.4
  - 第二次 codex review(v2.1 → v2.2 修订)
  - 第一次 codex review(v1.0 → v1.1)
  - codex V1 phased design 方案
  - 14 轮修订(v2.4 把 v2.0 没改干净的"固定角色残留"清掉 + 5 个开放问题敲死)
- 状态:**开工就绪(v2.4 5 个设计点收死 + 角色配置方案 Y 落地)**
- 配套主文档:autonomous-agent-system-design.md v2.4
- 配套历史:design-history.md v2.2
- 下一份 Spec:Phase 2 Execution Spec(Phase 1 完成后写)
