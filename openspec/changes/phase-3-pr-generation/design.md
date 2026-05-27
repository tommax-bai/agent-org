## Context

Phase 2 完成后,agent-org 能让 LLM 在 Git worktree 真改文件、跑 CI、生成真实 diff。
但所有改动**停在本地**:
- worktree 在 `.runs/worktrees/<task>/` 里(`KEEP_WORKTREE=1` 不清)
- 分支 `agent-org/<task_id>` 只在本地(没 push)
- Owner 要看代码改动得 cd 进 worktree 自己 `git diff` 看

实际工程闭环需要:**任务跑完 → 自动 push + 开 PR → Owner 在 GitHub 上 review → merge**。
Phase 3 接通这一环。

约束:
- `gh` CLI 已经装(Phase 0A 部署时用过)
- Owner 已经 `gh auth login`(创建 agent-org repo 时用过)
- target repo 可能没 GitHub remote(fixtures 跑的 example-api 只是本地)— 要兼容本地-only 模式

## Goals / Non-Goals

**Goals**:
- 任务成功(有 git diff 的)自动 push + 开 PR
- PR body 含完整任务上下文:owner_request / subtask 摘要 / CI 输出 / approval_required 路径标红
- 新增 terminal state `PR_READY`
- 没 GitHub remote 时降级:不开 PR,但 escalation.md 给出 worktree path + 手动 push 命令

**Non-Goals**:
- **不做 auto-merge**(宪法第 11 条:Owner 不在 review loop ≠ 系统自动合并;V1 永远手动 merge)
- **不做 PR 评论交互**(Owner 在 PR 留 review comment,系统不消费)
- 不集成 GitLab / Bitbucket(只 GitHub,gh CLI 限制)
- 不做 Draft PR 自动转 Ready(全部直接 ready)

## Decisions

### 1. 用 `gh` CLI 而不是 PyGithub / Anthropic API

**选**:subprocess 调用 `gh pr create` / `gh pr edit`

**理由**:
- gh CLI 已经装 + 已经 auth,零额外集成
- PyGithub 引入新依赖 + 自己管 token
- 跟其他 gh 操作(repo create / clone)一致

**替代**:PyGithub(否决:依赖 + token 管理重)

### 2. 任务终态加 `PR_READY`,不是用 DONE

**选**:加新 enum 值 `PR_READY`

**理由**:
- DONE = 任务跑完无 git diff(纯分析类任务,如 task-005 模糊需求)
- PR_READY = 任务跑完有 git diff + PR 已开 + 等 Owner merge
- 语义清晰,Owner dashboard 区分容易

**替代**:复用 DONE + 看 git_diff 字段空不空(否决:状态机要靠副作用判断,反模式)

### 3. PR 在 `_finalize_task` 时机开,不是某个 role 触发

**选**:state_machine 的 `_finalize_task` 检测 status == DONE 且有 git diff 时,
调 `orchestrator.pr.create_pr`,成功 → status = PR_READY

**理由**:
- 集中在一处,逻辑可控
- role 不需要知道 PR 概念(保持 role 纯产物输出)
- partial_success 不开 PR(只有 fully DONE 才开)— 部分成功的代码还在 worktree,Owner 手动看

**替代**:某个新 role(PRBot)负责开 PR(否决:杀鸡用牛刀,role 是 LLM 调用,这步纯确定性)

### 4. 没 GitHub remote 时的降级

**选**:`gh repo view` 失败 → 写 escalation.md 给手动命令,**不 fail 任务**

**理由**:
- 本地 fixtures(example-api)没 remote,但系统还是要让 worktree 可被 inspect
- 给出"cd /path && git push -u origin agent-org/<task>" 命令让 Owner 自己 push
- 不视为任务失败(代码改动是真的)

### 5. PR body 模板放代码里(不是 yaml / 外部模板文件)

**选**:Python f-string + 简单段落拼接,放在 `orchestrator/pr/_internal/body.py`

**理由**:
- 内容字段固定,模板引擎过度
- 修改要走代码 review,不能 Owner 在 yaml 里乱改

## Risks / Trade-offs

| 风险 | 缓解 |
|---|---|
| gh CLI 未登录 / token 过期 → PR 创建失败 | 降级:写 escalation 给手动命令,任务标 DONE(代码改动有效)而非 PR_READY |
| target repo 没设 default branch / 分支冲突 | gh pr create 报错 → escalation 含 error,Owner 看 |
| 单 worktree 多次 push(重复跑同 task)→ branch 已存在 | `-B` force(已经在 worktree manager 用了)+ PR 自动复用同名 branch |
| PR body 含敏感信息(error / stderr 含 token)| stderr/stdout 已经在 ci.py 截断 4KB,但 secret 扫描留 Phase 3.5+(gitleaks 集成)|
| approval_required_paths 漏标 | check_path 已在 Developer 写盘前做,失败拒写;这里只是汇总展示 |

## Migration Plan

1. 加 `orchestrator/pr/` 模块(新模块,不影响现有代码)
2. `TaskState.status` 加 `PR_READY` enum 值(向后兼容,旧 task 仍走 DONE)
3. `_finalize_task` 加 PR 创建逻辑(检测 DONE + has_diff)
4. 不需要数据 migration(Phase 3 之前没 task 状态是 PR_READY)
5. rollback:`PR_GENERATION_ENABLED=0` env 跳过 PR 步骤,行为退回 Phase 2

## Open Questions

- PR title 长度限制?Owner 短 title 偏好(< 70 字符)— **决定**:截到 70 字符 + ellipsis
- PR 失败(rate limit / network)是否 retry?— **决定**:retry 1 次,再失败 escalation
- PR 用 squash merge 还是 normal?— **不在系统范围**(Owner 在 GitHub UI 决定)
