## ADDED Requirements

### Requirement: 任务完成时自动开 PR
当任务最终状态 = DONE 且 worktree 含 git diff 时,系统 SHALL 自动 push 任务分支
到 target repo 并创建 GitHub PR。

#### Scenario: 成功开 PR
- **WHEN** state_machine `_finalize_task` 检测 status=DONE 且 `git diff HEAD` 非空
- **THEN** 系统 SHALL `git push -u origin agent-org/<task_id>` 推送分支
- **AND** 系统 SHALL 调 `gh pr create --title "<task title>" --body "<rendered body>" --base <main_branch>`
- **AND** 状态推进到 `PR_READY`(替代 DONE)
- **AND** event log 记录 `PR_CREATED` 事件,payload 含 PR URL

#### Scenario: 任务无 git diff,不开 PR
- **WHEN** task DONE 但 `git diff HEAD` 为空(纯分析类任务)
- **THEN** 系统 SHALL 保持 status=DONE,**不**开 PR
- **AND** final_report.md 仍然生成

#### Scenario: 任务失败(escalate / partial_success)不开 PR
- **WHEN** 任务终态非 DONE
- **THEN** 系统 SHALL **不**开 PR
- **AND** escalation.md 仍然生成,含 worktree 路径供 Owner 手动 inspect

### Requirement: PR body 模板
PR body MUST 包含以下章节,顺序固定:

1. **Task summary**: owner_request 前 200 字
2. **Subtasks**: 每个 subtask 一行,含 status icon(✅ / ❌ / ⚠️ partial)
3. **Reviewer verdicts**: 每个 reviewer artifact 的 verdict + correctness_score
4. **CI summary**: test/lint/build 通过率 + 失败命令 stderr_tail
5. **⚠️ Approval Required Paths**: `approval_required_paths` 列表,标红提示 Owner 单独 review
6. **Stats**: 总成本 / 总耗时 / LLM 调用数

#### Scenario: PR body 含 approval_required 标记
- **WHEN** Developer 改了 `package.json`(命中 approval_required pattern)
- **THEN** PR body 必有 `## ⚠️ Approval Required Paths` 章节
- **AND** 章节列 `package.json`(以及它命中的 pattern)
- **AND** 章节文字明示"Owner 必须单独审查这些路径"

#### Scenario: PR body 含 CI 失败详情
- **WHEN** CI 跑过且 `go test` 失败
- **THEN** PR body `## CI Summary` 章节 SHALL 含 test 的 exit_code + stderr_tail(截 1KB)

### Requirement: 没 GitHub remote 时降级
当 target repo 不是 GitHub repo(或 `gh repo view` 失败)时,系统 SHALL 降级到本地模式
而不是把任务标失败。

#### Scenario: 降级到本地模式
- **WHEN** `gh repo view <repo_url>` 返非零
- **THEN** 系统 SHALL **不**调 `gh pr create`
- **AND** 状态保持 DONE(不进 PR_READY)
- **AND** final_report.md 含 worktree 路径 + 手动 push 命令模板
- **AND** event log 记录 `PR_CREATION_SKIPPED` 事件,payload 含 reason

### Requirement: PR 创建失败的处理
PR 创建失败(rate limit / network / auth)时,系统 SHALL retry 1 次,
再失败则标 task 状态 DONE(不进 PR_READY)并 escalation.md 详记 error。

#### Scenario: PR 创建 retry 后仍失败
- **WHEN** `gh pr create` 连续 2 次返非零
- **THEN** 系统 SHALL 保持 status=DONE
- **AND** escalation.md 加 PR_CREATION_FAILED 章节含完整 gh stderr
- **AND** event log 记录 `PR_CREATION_FAILED`

### Requirement: PR_READY 是终态
`PR_READY` SHALL 是 terminal state(跟 DONE / ESCALATED_TO_OWNER 同级),
不允许进一步推进。

#### Scenario: PR_READY 后状态机不再 dispatch
- **WHEN** 状态机进 PR_READY
- **THEN** state machine SHALL 不再调用任何 role / dispatch
- **AND** worktree 默认 cleanup(`KEEP_WORKTREE=1` 才保留)
- **AND** TASK_COMPLETED event 写入(同 DONE 行为)
