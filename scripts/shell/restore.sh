#!/bin/bash
# ============================================
# 数据库恢复脚本
# ============================================
# 使用方法：
# chmod +x scripts/shell/restore.sh
# ./scripts/shell/restore.sh backup_20260124_020000.sql.gz
# ============================================

set -e

# 配置
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BACKUP_DIR="$PROJECT_DIR/backups"
DB_CONTAINER="mine_energy_db_prod"
DB_USER="admin"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}❌ 错误: 请指定备份文件${NC}"
    echo "使用方法: $0 <backup_file>"
    echo ""
    echo "可用备份文件:"
    ls -lh "$BACKUP_DIR"/backup_*.sql.gz 2>/dev/null || echo "无备份文件"
    exit 1
fi

BACKUP_FILE="$1"

# 如果只提供了文件名，添加路径
if [[ ! "$BACKUP_FILE" = /* ]]; then
    BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
fi

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ 错误: 备份文件不存在: $BACKUP_FILE${NC}"
    exit 1
fi

# 确认操作
echo -e "${YELLOW}⚠️  警告: 此操作将覆盖当前数据库！${NC}"
echo "备份文件: $BACKUP_FILE"
read -p "确认恢复? (yes/no): " confirm

if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

# 检查容器是否存在
if ! docker ps | grep -q "$DB_CONTAINER"; then
    echo -e "${RED}❌ 错误: 数据库容器未运行${NC}"
    exit 1
fi

# 恢复数据库
echo -e "${GREEN}📥 开始恢复数据库...${NC}"

gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -U "$DB_USER" mine_energy

echo -e "${GREEN}✅ 数据库恢复完成${NC}"
