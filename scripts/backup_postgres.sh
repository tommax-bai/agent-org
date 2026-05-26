#!/usr/bin/env bash
# Phase 0C 备份脚本。
#
# 每日跑(cron 或手动),输出到 backups/<date>/agent_org.dump
# 默认只备 agent_org,不备 langfuse(它自己有 schema migration,丢了可以重建)
#
# 用法:
#   ./scripts/backup_postgres.sh                       # 备份到 backups/
#   ./scripts/backup_postgres.sh /path/to/backup/dir  # 自定义目录
#
# cron 示例(每天凌晨 3 点):
#   0 3 * * * cd /path/to/agent-org && ./scripts/backup_postgres.sh
#
# 加密:Owner 自己 PGP / GPG 加密 dump 再传到云存储。
# 这个脚本只做本地 dump,不上传 — 因为各家云存储 API 不一样,自己加。

set -euo pipefail

BACKUP_BASE="${1:-./backups}"
CONTAINER="agent-org-postgres"
USER="${POSTGRES_USER:-agent}"
DB="agent_org"

date_tag=$(date -u +%Y-%m-%d_%H%M%S)
out_dir="$BACKUP_BASE/$date_tag"
mkdir -p "$out_dir"

# 检查 container 在跑
if ! docker ps --filter "name=$CONTAINER" --format '{{.Names}}' | grep -q "$CONTAINER"; then
    echo "ERROR: $CONTAINER 没在跑。先 docker compose up -d" >&2
    exit 1
fi

# 跑 pg_dump
echo "▶  备份 $DB → $out_dir/agent_org.dump"
docker exec "$CONTAINER" pg_dump -U "$USER" -F c -b -v -f "/tmp/agent_org.dump" "$DB" 2>&1 | tail -20
docker cp "$CONTAINER:/tmp/agent_org.dump" "$out_dir/agent_org.dump"
docker exec "$CONTAINER" rm /tmp/agent_org.dump

# 简单校验
size=$(stat -f%z "$out_dir/agent_org.dump" 2>/dev/null || stat -c%s "$out_dir/agent_org.dump")
echo "✓ Backup size: $size bytes"
if [ "$size" -lt 1000 ]; then
    echo "WARNING: dump 文件 < 1KB,可能空表" >&2
fi

# 保留最近 14 天,删除更老的
find "$BACKUP_BASE" -maxdepth 1 -type d -name "20*" -mtime +14 -exec rm -rf {} + 2>/dev/null || true

echo "✓ Backup completed: $out_dir"
