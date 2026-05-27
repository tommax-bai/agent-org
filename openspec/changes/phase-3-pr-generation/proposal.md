## Why

Phase 2 完成后,Developer 真改文件 + CI 跑过,但**改动停留在本地 worktree 里**——
Owner 看不到任何 GitHub PR,merge 要手动 `cd .runs/worktrees/<task>/ && git push`。
Phase 3 把"任务跑完 → 自动开 PR"接起来,Owner 才能在 GitHub UI 上 review + merge,
完成真正的"agent-org 自治闭环"。

同时配合宪法第 7 条(硬护栏)和 v2.4 决策(reviewer must_escalate / approval_required),
PR body 要把这些标记**显式列出来**让 Owner 一眼看到风险。

## What Changes

- **新增 PR 生成**:任务成功(DONE / partial_success)时,自动 push 任务分支 + `gh pr create`
- **新增 PR body 模板**:
  - 任务 owner_request 摘要
  - 各 subtask 完成情况(✅ / ❌ 部分失败)
  - Developer 的 summary + Reviewer 的 verdict
  - **approval_required_paths**(标红,Owner 必须单独 review 这些路径)
  - CI 输出汇总(test/lint/build 通过率)
  - cost / 耗时
- **新增 PR 状态推进**:task 状态加 `PR_READY`(最终 terminal state,任务挂着等 Owner merge)
- **GitHub CLI 集成**:用 `gh` 命令(已经装了),不引入新 SDK
- **任务失败**(escalate / partial_success)依然走 escalation.md 不开 PR
- **BREAKING**:`PR_READY` 是新 terminal state,跟 DONE 区分(DONE = 无文件改动的任务,如纯分析;
  PR_READY = 有 git diff 的任务)

## Capabilities

### New Capabilities

- `pr-generation`: 任务完成后生成 GitHub PR,包含 PR body 模板渲染、approval_required 标记、
  状态推进到 PR_READY

### Modified Capabilities

(无现有 capability 需要改动需求层 — Phase 0/1/2 都没建 spec,从 Phase 3 起新功能用 OpenSpec 规范)

## Impact

- **代码**:
  - 新增 `orchestrator/pr/` 模块(`generate_pr_body` / `create_pr`)
  - `state_machine/_internal/graph.py` 加 PR_READY 状态 + 调用 pr 模块
  - `_shared/types.py` `TaskStatus` enum 加 `PR_READY`
- **配置**:
  - `project.yaml` 加 `repo_url`(已有占位)+ `pr_target_branch`(默认 main)
  - 需要 `gh auth login` + repo write 权限
- **schemas**:`task.schema.json` 不变;新 PR-related 字段在 task_state 内部
- **CI**:agent-org 自己的 GitHub Actions 不受影响(我们用 gh CLI 操作的是 target repo)
- **文档**:`docs/decisions/` 加 v2.5 ADR(PR 生成时机 / PR body 字段约定)
- **依赖**:无新 Python 依赖(用 subprocess 调 gh)
