-- Phase 0C 基础设施:Postgres schema
--
-- 两个库:
--   agent_org   : 系统主库(tasks / task_events / artifacts / memory_items)
--   langfuse    : Langfuse 自用(它 boot 时自己迁移 schema,这里只建库)
--
-- 在 docker-entrypoint-initdb.d 里跑(Postgres 容器首次启动时)。

-- ----------------------------------------------------------------------------
-- Langfuse 自己的库
-- ----------------------------------------------------------------------------
CREATE DATABASE langfuse;

-- ----------------------------------------------------------------------------
-- agent_org 主库的 schema
-- ----------------------------------------------------------------------------
\c agent_org

-- 任务总表
CREATE TABLE IF NOT EXISTS tasks (
    task_id         TEXT PRIMARY KEY,
    project_id      TEXT NOT NULL,
    title           TEXT,
    status          TEXT NOT NULL,             -- CREATED / PM_PLANNING / DISPATCH / DONE / ESCALATED_TO_OWNER / BUDGET_EXCEEDED
    state_json      JSONB,                     -- 完整 TaskState 序列化(checkpoint 用)
    budget_usd      REAL,
    cost_used_usd   REAL DEFAULT 0,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);

-- 事件日志(append-only,审计真相源)
CREATE TABLE IF NOT EXISTS task_events (
    id              BIGSERIAL PRIMARY KEY,
    task_id         TEXT NOT NULL,
    event_type      TEXT NOT NULL,             -- TASK_CREATED / STATE_CHANGED / ROLE_INVOKED / ... 见 schemas/event.schema.json
    actor           TEXT NOT NULL,
    payload         JSONB NOT NULL DEFAULT '{}'::jsonb,
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_events_task ON task_events(task_id, occurred_at);
CREATE INDEX IF NOT EXISTS idx_events_type ON task_events(event_type);
CREATE INDEX IF NOT EXISTS idx_events_time ON task_events(occurred_at);

-- 产物存储(v2.4:attempt 字段 + superseded_by 追溯链)
CREATE TABLE IF NOT EXISTS artifacts (
    artifact_id     TEXT PRIMARY KEY,
    task_id         TEXT NOT NULL,
    subtask_id      TEXT,
    role_id         TEXT NOT NULL,
    attempt         INT NOT NULL DEFAULT 1,
    type            TEXT NOT NULL,             -- code / design / review / dispatch_plan / analysis / ...
    content         JSONB NOT NULL,
    superseded_by   TEXT,                      -- 新 artifact_id(可空)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (task_id, subtask_id, role_id, attempt)
);

CREATE INDEX IF NOT EXISTS idx_artifacts_task ON artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_current ON artifacts(task_id, subtask_id, role_id, attempt DESC);

-- Phase 4 才用,这里先建表
CREATE TABLE IF NOT EXISTS memory_items (
    id              BIGSERIAL PRIMARY KEY,
    project_id      TEXT NOT NULL,
    kind            TEXT NOT NULL,             -- fact / convention / history / experience / preference
    content         JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_project ON memory_items(project_id);
CREATE INDEX IF NOT EXISTS idx_memory_kind ON memory_items(kind);
