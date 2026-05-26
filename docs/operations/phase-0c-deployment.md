# Phase 0C 部署(本地)

> 起 Postgres + Langfuse 给 agent-org 用。

## 前置

- Docker Desktop(macOS / Linux)+ docker compose v2
- `.env`(从 `.env.example` 拷贝改密码)

## 启动

```bash
cd /path/to/agent-org

cp .env.example .env
# 编辑 .env,改 POSTGRES_PASSWORD / LANGFUSE_NEXTAUTH_SECRET / LANGFUSE_SALT
# 生成随机字符串:openssl rand -base64 32

docker compose up -d

# 等 30 秒让 Langfuse 跑完它自己的 schema migration
docker compose ps    # 看是不是 healthy
```

## 验证

```bash
# Postgres
docker exec agent-org-postgres psql -U agent -d agent_org -c "\\dt"
# 应该看到:tasks / task_events / artifacts / memory_items

# Langfuse Web UI
open http://localhost:3000
# 第一次进会让你建账号(本地用),建完之后在 Settings → API Keys 拿
# LANGFUSE_PUBLIC_KEY / LANGFUSE_SECRET_KEY,填回 .env
```

## 切到 Postgres backend 跑任务

```bash
# .env 里改:
STORAGE_BACKEND=postgres
# 然后跑
.venv/bin/python -m orchestrator run tasks/inbox/task-2026-05-26-001.yaml
```

事件 / 产物会进 Postgres,LLM 调用上报 Langfuse(如 LANGFUSE_PUBLIC_KEY 配了)。

## 停止 + 数据保留

```bash
docker compose down                # 停容器,数据 volume 保留
docker compose down -v             # 停 + 删 volume(数据丢失,谨慎)
```

## 备份

```bash
./scripts/backup_postgres.sh       # 每日跑(cron 或手动),输出到 backups/
```

## 切回 file backend(0B 行为)

```bash
# .env 里改回:
STORAGE_BACKEND=file
```
runtime 不需要 Postgres / Langfuse 也能跑,跟 0B 一样写 jsonl。
