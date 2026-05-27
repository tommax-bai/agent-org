# Phase 2 报告(2026-05-27)

> Spec Phase 2 完成。Git worktree + Developer 真改文件 + CI + subtask 独立 escalate。

## 配置
- 5 个原 task,Qwen plus,新加:Git worktree + protected_paths + 真文件执行 + CI 跑 `go test/vet/build`

## Phase 2.7 跑测结果

| ID | 终态 | 耗时 | 花费 | PM subtask | 触及 subtask | 真 git diff | CI 跑 | 失败原因 |
|---|---|---|---|---|---|---|---|---|
| 001 | ESCALATED (partial_success) | 142s | $0.008 | 4 | 3 | 2865 字节 | 是,fail | reviewer signal_schema(type='request') |
| 002 | ESCALATED (all_subtasks_failed) | 127s | $0.012 | 2 | 1 | 是 | 是,fail | developer attempt 上限 |
| 003 | ESCALATED (partial_success) | 172s | $0.008 | 4 | 2 | 是 | 是 | reviewer must_escalate/verdict 不一致 |
| 004 | ESCALATED (partial_success) | 277s | $0.015 | 4 | 4 | 是 | 是 | reviewer blocking_issues 缺 required_fix |
| 005 | ESCALATED (partial_success) | 149s | $0.013 | 2 | 2 | 是 | 是,fail | developer attempt 上限 |

**总成本 5 任务:$0.056**(便宜)
**DONE: 0/5,partial_success: 4/5,all_failed: 1/5**

## 跟 Phase 1 对比

| | Phase 1 Round 4 | Phase 2.7 |
|---|---|---|
| DONE | 2/5 | 0/5 |
| 部分成功(有 subtask 跑通)| 不可知(全挂)| **4/5 partial_success** |
| Developer 输出 | proposed_changes 文本 | **真改文件 + git diff(2-3KB)** |
| Reviewer 依据 | 只看文本 | **看 CI 真实 pass/fail** |
| 失败粒度 | 整任务挂 | **subtask 级**(失败不污染其他) |
| 总成本 | $0.07 | $0.056(便宜了!) |

## 关键观察

### ✅ 架构层成功

1. **真改文件工作**:Developer 在 worktree 里写出**有效的 Go 代码**(完整 import / struct / error handling)。
   2.8KB git diff 包含完整 RegisterHandler 函数,Phase 1 那种 JSON parse 崩**不再发生**。
2. **subtask 独立 escalate 工作**:4 个任务都有 partial_success,意味着每个任务都有 subtask 跑通。
   Phase 1 的"失败概率乘积放大"问题真的解决了。
3. **CI 跑通了**:每次 Developer 改完文件,`go test/vet/build` 自动跑,输出进 reviewer context

### ❌ Reviewer schema 错误持续

每个任务的最后 escalate 都是 reviewer 输出 schema 错(signal type 不在 enum / must_escalate
跟 verdict 不一致 / blocking_issues 缺 required_fix)。这跟 Phase 1 同源——Qwen plus
对复杂 schema 的字段填充率不够。

### ❌ Developer 写的 Go 代码 CI 经常 fail

LLM 引用了不存在的 package(`github.com/example/api/src/util` — fixtures 没这个),
真跑 `go build` 必然 fail。Reviewer 看到 fail → request_changes → attempt 上限。

## Phase 2 真正的瓶颈(留 Phase 2.5 后续优化)

1. **Reviewer prompt 还需要打磨**——schema 错误率高(跟 Qwen 模型对 strict 字段约束力差有关)
2. **Developer 上下文不够**——LLM 不知道 fixtures 里实际有哪些 package(应该把
   `go list ./...` 输出注入 context_pack)
3. **CI 真 fail 的修复机制**——LLM 收到 CI fail 后 retry,但同样不知道修什么。
   应该在 retry context 把 `ci_output.results[*].stderr_tail` 整段注入

## 总评

Phase 2 **架构层面**完全 OK——3 个 Phase 1 病根全消失:
- ✅ 长 diff JSON 崩 → 真改文件
- ✅ Reviewer 主观挑刺 → 看 CI 客观判定
- ✅ 单 subtask 挂整任务 → subtask 独立 escalate

剩余问题都是**模型/prompt 层**(Reviewer schema 跟随、Developer 代码 quality),
跟架构无关。

**Phase 2 完成**。Phase 3 该做:
- PR 生成(`gh pr create`)
- approval_required_paths 标红
- worktree 失败保留 + Owner 手动 review

或者先在 Phase 2.5 打磨 Developer prompt + Reviewer schema 容错。
