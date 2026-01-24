#!/bin/bash
# ============================================
# 数据库自动备份脚本
# ============================================
# 使用方法：
# 1. chmod +x scripts/shell/backup.sh
# 2. 手动执行: ./scripts/shell/backup.sh
# 3. 或添加到crontab: 0 2 * * * /path/to/backup.sh
# ============================================

set -e

# 配置
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BACKUP_DIR="$PROJECT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
DB_CONTAINER="mine_energy_db_prod"
DB_USER="admin"

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}📦 开始备份数据库...${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 检查容器是否存在
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${YELLOW}⚠️  数据库容器未运行，跳过备份${NC}"
    exit 0
fi

# 备份数据库
BACKUP_FILE="$BACKUP_DIR/backup_$DATE.sql.gz"
echo "备份文件: $BACKUP_FILE"

docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" mine_energy | gzip > "$BACKUP_FILE"

# 检查备份是否成功
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ 备份成功: $BACKUP_FILE (大小: $BACKUP_SIZE)${NC}"
else
    echo "❌ 备份失败"
    exit 1
fi

# 删除旧备份（保留30天）
echo -e "${YELLOW}🗑️  清理旧备份（保留${RETENTION_DAYS}天）...${NC}"
find "$BACKUP_DIR" -name "backup_*.sql.gz" -mtime +$RETENTION_DAYS -delete

# 显示备份列表
echo ""
echo "当前备份文件:"
ls -lh "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null | tail -5 || echo "无备份文件"

echo -e "${GREEN}✅ 备份完成${NC}"
