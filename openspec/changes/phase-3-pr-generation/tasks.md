## 1. 模块骨架

- [ ] 1.1 新建 `orchestrator/pr/` 模块(`__init__.py` + `_internal/__init__.py`)
- [ ] 1.2 加 `orchestrator/pr/_internal/body.py`(PR body 渲染)
- [ ] 1.3 加 `orchestrator/pr/_internal/github.py`(gh CLI 调用 + 降级)
- [ ] 1.4 importlinter.cfg 加 pr 模块的 no_cross_internal contract

## 2. 类型扩展

- [ ] 2.1 `_shared/types.py` `TaskStatus` Literal 加 `PR_READY`
- [ ] 2.2 `TaskState` 加 `pr_url: str | None`(成功开 PR 后填,escalation 用)

## 3. PR body 渲染

- [ ] 3.1 实现 `render_pr_body(state, ci_summary, approval_paths) -> str`
- [ ] 3.2 章节顺序按 spec:summary / subtasks / reviewer / CI / approval / stats
- [ ] 3.3 approval_required_paths 用 `## ⚠️` 强烈标记 + 文字明示 Owner 单独 review
- [ ] 3.4 CI 失败时 stderr_tail 截 1KB

## 4. gh CLI 集成

- [ ] 4.1 `create_pr(worktree, branch, title, body, base) -> PRResult` 调 `gh pr create`
- [ ] 4.2 detect_github_repo(repo_url):`gh repo view` 探测,返 True/False
- [ ] 4.3 push branch:`git push -u origin <branch>` 在 worktree 内跑
- [ ] 4.4 retry 1 次,指数退避(rate limit 友好)
- [ ] 4.5 降级模式:返 PRResult.skipped=True + reason

## 5. state_machine 集成

- [ ] 5.1 `_finalize_task` 检测 status=DONE 且有 git diff → 调 pr.create_pr
- [ ] 5.2 成功 → status=PR_READY,event log `PR_CREATED`
- [ ] 5.3 降级 → status 保持 DONE,event log `PR_CREATION_SKIPPED`
- [ ] 5.4 失败 retry 后仍败 → status=DONE + escalation.md 加 PR_CREATION_FAILED
- [ ] 5.5 `PR_GENERATION_ENABLED=0` env 跳过 PR 步骤(rollback 开关)

## 6. final_report / escalation 渲染

- [ ] 6.1 `escalation/reports.py` final_report.md 加 PR URL(PR_READY 时)
- [ ] 6.2 降级时 final_report 含手动 push 命令模板
- [ ] 6.3 失败时 escalation.md 加 PR_CREATION_FAILED 章节

## 7. event schema 更新

- [ ] 7.1 `schemas/event.schema.json` enum 加 `PR_CREATED` / `PR_CREATION_SKIPPED` / `PR_CREATION_FAILED`

## 8. 测试 + 验证

- [ ] 8.1 unit test:render_pr_body 对几个状态输出符合 spec(approval / CI fail / 全过)
- [ ] 8.2 integration test:fixtures 用本地 git(无 remote)跑一次,验证降级模式
- [ ] 8.3 跑 5 个 Phase 2 任务里能 DONE 的(目前 task-005 partial,等 Phase 2.5 prompt 优化后)
- [ ] 8.4 手动测:agent-org repo 本身跑一次(它是真 GitHub repo),验证 PR 真开了

## 9. 文档

- [ ] 9.1 `docs/decisions/2026-XX-XX-phase-3-pr-generation.md` ADR
- [ ] 9.2 CLAUDE.md 加 PR_GENERATION_ENABLED env 说明
- [ ] 9.3 主文档 Part V Phase 3 段更新(标完成)
