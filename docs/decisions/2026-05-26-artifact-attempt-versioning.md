# ADR: Artifact 追加 attempt,不覆盖

- **日期**:2026-05-26
- **状态**:已接受
- **关联修订**:v2.4(主文档 D 域 artifact schema + state layers 段)
- **触发问题**:Spec 5 个开放问题之 Q4(verdict=needs_changes 时 artifact 怎么处理)

---

## 决策

verdict=needs_changes 触发重试时:

1. **追加,不覆盖**。新 attempt 产生新 artifact_id,老的留着,加 `superseded_by` 字段
2. **dispatcher 取"当前 artifact"** = 同 (task_id, subtask_id, role_id) 下 `max(attempt)`
3. **硬上限**:同 (subtask, role) `attempt > 2` → `ATTEMPT_LIMIT_REACHED` → ESCALATED_TO_OWNER

---

## 上下文

Reviewer 看 Developer 的代码,verdict=needs_changes,Developer 改后再交。第一次的 artifact 怎么处理?

两个候选:
- (a) 覆盖:第二份替换第一份,系统里只剩最新的
- (b) 追加:第一份留着,第二份是新 attempt(每个 artifact 有 attempt_n)

---

## 论据

### 为什么追加

1. **宪法第 9 条**:所有决策可解释、可追溯。覆盖了就追溯不了"Developer 第一次怎么写错的、Reviewer 第一次怎么指出来的"
2. **Phase 4 记忆系统的数据基础**:统计"Developer 平均几次过 review"、"哪类任务 reviewer 反弹率高"这类指标,需要历史 attempt
3. **debug 时方便**:任务失败时,看 attempt 链能看到完整的"为什么走到这一步"
4. **存储成本可忽略**:一个 artifact 几 KB,一个 task 撑死几 MB,无所谓

### 为什么 attempt 上限 2

- 第 1 次:LLM 第一次产物,Reviewer 说改
- 第 2 次:LLM 改完再交,Reviewer 再审
- 第 3 次:再改就是死循环嫌疑了,自动 escalate 给 Owner

数字 2 是直觉值,Phase 1 跑几个真实任务后看数据校准。配置在 `dispatch_policy.yaml` 里,不 hardcode。

### 为什么上限只算"被审查方"

reviewer / pm 这种角色发出 needs_changes,不会被自己反向 needs_changes。只有 developer / architect 等"被审查方"会被打回来。上限只对它们计数。

---

## 实施

### Artifact schema 改动

`role_invocation_output.artifact` 加两个字段:

```yaml
artifact:
  type: code | design | review | analysis
  content: {...}
  artifact_id: artifact-2026-05-26-abc123    # 不可变 UUID
  attempt: 1                                  # v2.4 新增,从 1 起
  superseded_by: null                         # v2.4 新增,可选(被哪个新 artifact_id 取代)
```

### 状态机改动(B.4)

ROLE_EXECUTING 节点处理 verdict=needs_changes:

```
verdict=needs_changes
  ↓
找到上游角色(role_sequence 里前一个 step)
  ↓
该上游角色的 (subtask, role) attempt + 1
  ↓
if attempt > 2:
    log_event('ATTEMPT_LIMIT_REACHED', ...)
    → ESCALATED_TO_OWNER
else:
    标记上游角色 pending(产生新 attempt)
    → 回到 DISPATCH
```

### Event log

新增事件类型:`ATTEMPT_LIMIT_REACHED`

### Storage layout

```
runs/<task_id>/artifacts/
  artifact-2026-05-26-abc123.yaml    # subtask-001 developer attempt 1
  artifact-2026-05-26-def456.yaml    # subtask-001 reviewer attempt 1 (verdict=needs_changes)
  artifact-2026-05-26-ghi789.yaml    # subtask-001 developer attempt 2 (新)
  artifact-2026-05-26-jkl012.yaml    # subtask-001 reviewer attempt 2
```

老的 artifact 文件中加 `superseded_by: artifact-2026-05-26-ghi789` 标记。

0C+ 接 Postgres 后,artifact 表:

```sql
CREATE TABLE artifacts (
  artifact_id     TEXT PRIMARY KEY,
  task_id         TEXT NOT NULL,
  subtask_id      TEXT NOT NULL,
  role_id         TEXT NOT NULL,
  attempt         INT NOT NULL,
  type            TEXT NOT NULL,
  content         JSONB NOT NULL,
  superseded_by   TEXT,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  UNIQUE (task_id, subtask_id, role_id, attempt)
);
```

---

## 不做什么

- 不做 attempt 自动 cleanup(V1 阶段不需要,存储不是瓶颈)
- 不做"smart retry"(根据 Reviewer 反馈自动改下次 prompt)— 那是 V2+ self-evolution,已否决
- 不做"跨任务 attempt 统计"作为 dispatcher 决策依据 — 那是 Phase 4 记忆系统的事

---

## 修订风险

- attempt 上限 2 可能太严格(真实任务中 3-4 次才过的情况存在)→ Phase 1 跑数据后校准,先按 2 试
- 上限通过 `dispatch_policy.yaml` 配置,改不需要发版

---

## 关联文档

- `constitution.md` 第 9 条
- `docs/autonomous-agent-system-design.md` D 域 artifact schema + 状态机
- `docs/phase-0-1-execution-spec.md` B.4 状态机 + B.7 artifact + B.12 完成标准
- `docs/design-history.md` v2.4 修订日志 + Part IV 已否决清单(`artifact 覆盖式重试`)
