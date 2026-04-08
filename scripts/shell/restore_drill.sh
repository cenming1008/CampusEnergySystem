#!/bin/bash
# ============================================
# 备份恢复演练脚本
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

DB_CONTAINER="${DB_CONTAINER_OVERRIDE:-campus_energy_db_prod}"
LABEL="${DRILL_LABEL:-restore_drill_$(date +%Y%m%d_%H%M%S)}"
BACKUP_FORMAT="${BACKUP_FORMAT:-custom}"
REPORT_DIR="$PROJECT_DIR/backups/restore_drills"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

mkdir -p "$REPORT_DIR"

if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo -e "${RED}❌ 数据库容器未运行: ${DB_CONTAINER}${NC}"
    exit 1
fi

echo -e "${YELLOW}1/4 创建演练备份...${NC}"
DB_CONTAINER_OVERRIDE="$DB_CONTAINER" bash ./scripts/shell/backup.sh --label "$LABEL" --format "$BACKUP_FORMAT"

if [ "$BACKUP_FORMAT" = "custom" ]; then
    BACKUP_FILE="backups/latest_${LABEL}.dump"
else
    BACKUP_FILE="backups/latest_${LABEL}.sql.gz"
fi

echo -e "${YELLOW}2/4 校验备份可恢复性...${NC}"
DB_CONTAINER_OVERRIDE="$DB_CONTAINER" bash ./scripts/shell/restore.sh --verify-only "$BACKUP_FILE"

echo -e "${YELLOW}3/4 执行恢复演练...${NC}"
DB_CONTAINER_OVERRIDE="$DB_CONTAINER" bash ./scripts/shell/restore.sh --yes "$BACKUP_FILE"

echo -e "${YELLOW}4/4 执行恢复后烟雾校验...${NC}"
TABLE_COUNT=$(docker exec "$DB_CONTAINER" psql -U admin -d campus_energy -tAc "select count(*) from information_schema.tables where table_schema='public';" | tr -d '[:space:]')
TIMESCALE_EXISTS=$(docker exec "$DB_CONTAINER" psql -U admin -d campus_energy -tAc "select count(*) from pg_extension where extname='timescaledb';" | tr -d '[:space:]')
ENERGY_ROWS=$(docker exec "$DB_CONTAINER" psql -U admin -d campus_energy -tAc "select count(*) from public.energydata;" | tr -d '[:space:]')

REPORT_FILE="$REPORT_DIR/${LABEL}.md"
cat > "$REPORT_FILE" <<EOF
# 恢复演练记录

- 时间：$(date '+%Y-%m-%d %H:%M:%S %z')
- 数据库容器：\`$DB_CONTAINER\`
- 备份标签：\`$LABEL\`
- 备份文件：\`$BACKUP_FILE\`

## 结果

- public schema 表数量：\`$TABLE_COUNT\`
- TimescaleDB 扩展存在：\`$TIMESCALE_EXISTS\`
- energydata 行数：\`$ENERGY_ROWS\`

## 执行命令

\`\`\`bash
DB_CONTAINER_OVERRIDE=$DB_CONTAINER bash ./scripts/shell/backup.sh --label $LABEL --format $BACKUP_FORMAT
DB_CONTAINER_OVERRIDE=$DB_CONTAINER bash ./scripts/shell/restore.sh --verify-only $BACKUP_FILE
DB_CONTAINER_OVERRIDE=$DB_CONTAINER bash ./scripts/shell/restore.sh --yes $BACKUP_FILE
\`\`\`
EOF

echo -e "${GREEN}✅ 恢复演练完成${NC}"
echo "演练记录: $REPORT_FILE"
