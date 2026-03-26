#!/bin/bash
# ============================================
# 生产环境回滚脚本
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
COMPOSE_FILE="$PROJECT_DIR/docker-compose.prod.yml"
ENV_FILE="$PROJECT_DIR/.env.prod"
BACKUP_FILE="${1:-}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

cd "$PROJECT_DIR"

if [ ! -f "$ENV_FILE" ]; then
    echo -e "${RED}❌ 缺少 .env.prod，无法执行回滚${NC}"
    exit 1
fi

if [ -z "$BACKUP_FILE" ]; then
    if [ -L "$PROJECT_DIR/backups/latest_pre_deploy.dump" ]; then
        BACKUP_FILE="$PROJECT_DIR/backups/latest_pre_deploy.dump"
    elif [ -L "$PROJECT_DIR/backups/latest_pre_deploy.sql.gz" ]; then
        BACKUP_FILE="$PROJECT_DIR/backups/latest_pre_deploy.sql.gz"
    else
        echo -e "${RED}❌ 请提供要恢复的备份文件，或先创建 pre_deploy 备份${NC}"
        exit 1
    fi
fi

echo -e "${YELLOW}⚠️  即将执行生产回滚${NC}"
echo "数据库备份: $BACKUP_FILE"

read -p "确认继续? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "已取消"
    exit 0
fi

echo -e "${YELLOW}1/3 停止应用流量入口...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop nginx backend || true

echo -e "${YELLOW}2/3 恢复数据库...${NC}"
bash "$PROJECT_DIR/scripts/shell/restore.sh" --yes "$BACKUP_FILE"

echo -e "${YELLOW}3/3 重新拉起应用...${NC}"
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d backend nginx

echo -e "${GREEN}✅ 回滚完成，请手动验证 /health 和关键业务接口${NC}"
