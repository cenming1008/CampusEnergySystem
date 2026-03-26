#!/bin/bash
# ============================================
# 数据库恢复脚本
# ============================================
# 使用方法：
# chmod +x scripts/shell/restore.sh
# ./scripts/shell/restore.sh backup_20260124_020000.dump
# ============================================

set -euo pipefail

# 配置
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BACKUP_DIR="$PROJECT_DIR/backups"
DB_CONTAINER="mine_energy_db_prod"
DB_USER="admin"
DB_NAME="mine_energy"
AUTO_CONFIRM="false"
VERIFY_ONLY="false"
BACKUP_KIND=""
DECRYPTED_TEMP=""

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

while [[ $# -gt 0 ]]; do
    case "$1" in
        --yes)
            AUTO_CONFIRM="true"
            shift
            ;;
        --verify-only)
            VERIFY_ONLY="true"
            shift
            ;;
        *)
            break
            ;;
    esac
done

if [ -n "${DB_CONTAINER_OVERRIDE:-}" ]; then
    DB_CONTAINER="$DB_CONTAINER_OVERRIDE"
elif docker ps --format '{{.Names}}' | grep -q '^mine_energy_db_prod$'; then
    DB_CONTAINER="mine_energy_db_prod"
elif docker ps --format '{{.Names}}' | grep -q '^mine_energy_db_dev$'; then
    DB_CONTAINER="mine_energy_db_dev"
fi

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}❌ 错误: 请指定备份文件${NC}"
    echo "使用方法: $0 <backup_file>"
    echo ""
    echo "可用备份文件:"
    ls -lh "$BACKUP_DIR"/backup_* 2>/dev/null || echo "无备份文件"
    exit 1
fi

BACKUP_FILE="$1"
MANIFEST_FILE=""

# 如果只提供了文件名，添加路径
if [[ ! "$BACKUP_FILE" = /* ]]; then
    if [ -f "$PROJECT_DIR/$BACKUP_FILE" ]; then
        BACKUP_FILE="$PROJECT_DIR/$BACKUP_FILE"
    else
        BACKUP_FILE="$BACKUP_DIR/$BACKUP_FILE"
    fi
fi

# 检查备份文件是否存在
if [ ! -f "$BACKUP_FILE" ]; then
    echo -e "${RED}❌ 错误: 备份文件不存在: $BACKUP_FILE${NC}"
    exit 1
fi

if [ -f "$BACKUP_FILE.manifest.json" ]; then
    MANIFEST_FILE="$BACKUP_FILE.manifest.json"
fi

case "$BACKUP_FILE" in
    *.dump.enc)
        BACKUP_KIND="custom"
        ;;
    *.sql.gz.enc)
        BACKUP_KIND="plain"
        ;;
    *.dump)
        BACKUP_KIND="custom"
        ;;
    *.sql.gz)
        BACKUP_KIND="plain"
        ;;
    *)
        echo -e "${RED}❌ 错误: 不支持的备份格式: $BACKUP_FILE${NC}"
        exit 1
        ;;
esac

echo -e "${YELLOW}🔍 校验备份文件...${NC}"
if [[ "$BACKUP_FILE" == *.enc ]]; then
    if [ -z "${BACKUP_ENCRYPTION_PASSPHRASE:-}" ]; then
        echo -e "${RED}❌ 错误: 加密备份恢复需要设置 BACKUP_ENCRYPTION_PASSPHRASE${NC}"
        exit 1
    fi
    case "$BACKUP_FILE" in
        *.dump.enc)
            DECRYPTED_TEMP=$(mktemp "${TMPDIR:-/tmp}/mine_restore_XXXXXX.dump")
            ;;
        *.sql.gz.enc)
            DECRYPTED_TEMP=$(mktemp "${TMPDIR:-/tmp}/mine_restore_XXXXXX.sql.gz")
            ;;
    esac
    openssl enc -d -aes-256-cbc -pbkdf2 \
        -in "$BACKUP_FILE" \
        -out "$DECRYPTED_TEMP" \
        -pass "pass:$BACKUP_ENCRYPTION_PASSPHRASE"
    BACKUP_FILE="$DECRYPTED_TEMP"
fi

if [ "$BACKUP_KIND" = "custom" ]; then
    if [ ! -s "$BACKUP_FILE" ]; then
        echo -e "${RED}❌ 错误: 自定义备份文件为空${NC}"
        exit 1
    fi
else
    gzip -t "$BACKUP_FILE"
fi
if [ -n "$MANIFEST_FILE" ]; then
    EXPECTED_SHA=$(python3 - <<PY
import json
from pathlib import Path
data = json.loads(Path("$MANIFEST_FILE").read_text())
print(data.get("sha256", ""))
PY
)
    ACTUAL_SHA=$(shasum -a 256 "$BACKUP_FILE" | awk '{print $1}')
    if [ "$EXPECTED_SHA" != "$ACTUAL_SHA" ]; then
        echo -e "${RED}❌ 错误: 备份校验失败，sha256 不匹配${NC}"
        exit 1
    fi
fi

if [ "$VERIFY_ONLY" = "true" ]; then
    echo -e "${GREEN}✅ 备份校验通过（verify-only）${NC}"
    [ -n "$DECRYPTED_TEMP" ] && rm -f "$DECRYPTED_TEMP"
    exit 0
fi

# 确认操作
echo -e "${YELLOW}⚠️  警告: 此操作将覆盖当前数据库！${NC}"
echo "备份文件: $BACKUP_FILE"
if [ "$AUTO_CONFIRM" != "true" ]; then
    read -p "确认恢复? (yes/no): " confirm

    if [ "$confirm" != "yes" ]; then
        echo "已取消"
        exit 0
    fi
fi

# 检查容器是否存在
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo -e "${RED}❌ 错误: 数据库容器未运行${NC}"
    exit 1
fi

echo -e "${YELLOW}📦 恢复前自动创建保护性备份...${NC}"
bash "$PROJECT_DIR/scripts/shell/backup.sh" --label pre_restore

# 恢复数据库
echo -e "${GREEN}📥 开始恢复数据库...${NC}"
docker exec -i "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" -d "$DB_NAME" <<'SQL'
DROP SCHEMA IF EXISTS public CASCADE;
CREATE SCHEMA public;
GRANT ALL ON SCHEMA public TO public;
SQL

if [ "$BACKUP_KIND" = "custom" ]; then
    cat "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" pg_restore -v -U "$DB_USER" -d "$DB_NAME" --clean --if-exists --no-owner --no-privileges
else
    gunzip -c "$BACKUP_FILE" | docker exec -i "$DB_CONTAINER" psql -v ON_ERROR_STOP=1 -U "$DB_USER" "$DB_NAME"
fi

echo -e "${GREEN}✅ 数据库恢复完成${NC}"
[ -n "$DECRYPTED_TEMP" ] && rm -f "$DECRYPTED_TEMP"
