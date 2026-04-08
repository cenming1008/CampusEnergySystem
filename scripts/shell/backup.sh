#!/bin/bash
# ============================================
# 数据库自动备份脚本
# ============================================
# 使用方法：
# 1. chmod +x scripts/shell/backup.sh
# 2. 手动执行: ./scripts/shell/backup.sh
# 3. 或添加到crontab: 0 2 * * * /path/to/backup.sh
# ============================================

set -euo pipefail

# 配置
PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BACKUP_DIR="$PROJECT_DIR/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30
DB_CONTAINER="campus_energy_db_prod"
DB_USER="admin"
DB_NAME="campus_energy"
LABEL="${BACKUP_LABEL:-manual}"
BACKUP_FORMAT="${BACKUP_FORMAT:-custom}"
KEEP_PLAINTEXT_BACKUP="${KEEP_PLAINTEXT_BACKUP:-false}"
BACKUP_ENCRYPTION_PASSPHRASE="${BACKUP_ENCRYPTION_PASSPHRASE:-}"
OFFSITE_BACKUP_DIR="${OFFSITE_BACKUP_DIR:-}"
OFFSITE_RCLONE_REMOTE="${OFFSITE_RCLONE_REMOTE:-}"
FINAL_BACKUP_FILE=""

# 颜色输出
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

while [[ $# -gt 0 ]]; do
    case "$1" in
        --label)
            LABEL="${2:-manual}"
            shift 2
            ;;
        --retention-days)
            RETENTION_DAYS="${2:-30}"
            shift 2
            ;;
        --format)
            BACKUP_FORMAT="${2:-custom}"
            shift 2
            ;;
        *)
            echo -e "${RED}❌ 未知参数: $1${NC}"
            exit 1
            ;;
    esac
done

if [ -n "${DB_CONTAINER_OVERRIDE:-}" ]; then
    DB_CONTAINER="$DB_CONTAINER_OVERRIDE"
elif docker ps --format '{{.Names}}' | grep -q '^campus_energy_db_prod$'; then
    DB_CONTAINER="campus_energy_db_prod"
elif docker ps --format '{{.Names}}' | grep -q '^campus_energy_db_dev$'; then
    DB_CONTAINER="campus_energy_db_dev"
fi

echo -e "${GREEN}📦 开始备份数据库...${NC}"

# 创建备份目录
mkdir -p "$BACKUP_DIR"

# 检查容器是否存在
if ! docker ps --format '{{.Names}}' | grep -q "^${DB_CONTAINER}$"; then
    echo -e "${YELLOW}⚠️  数据库容器未运行，跳过备份${NC}"
    exit 0
fi

# 备份数据库
case "$BACKUP_FORMAT" in
    custom)
        BACKUP_FILE="$BACKUP_DIR/backup_${DATE}_${LABEL}.dump"
        ;;
    plain)
        BACKUP_FILE="$BACKUP_DIR/backup_${DATE}_${LABEL}.sql.gz"
        ;;
    *)
        echo -e "${RED}❌ 不支持的备份格式: $BACKUP_FORMAT${NC}"
        exit 1
        ;;
esac
CONFIG_ARCHIVE="$BACKUP_DIR/config_${DATE}_${LABEL}.tar.gz"
echo "备份文件: $BACKUP_FILE"

if [ "$BACKUP_FORMAT" = "custom" ]; then
    docker exec "$DB_CONTAINER" pg_dump -Fc -U "$DB_USER" "$DB_NAME" > "$BACKUP_FILE"
else
    docker exec "$DB_CONTAINER" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"
    gzip -t "$BACKUP_FILE"
fi

# 检查备份是否成功
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
    BACKUP_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo -e "${GREEN}✅ 备份成功: $BACKUP_FILE (大小: $BACKUP_SIZE)${NC}"
else
    echo "❌ 备份失败"
    exit 1
fi

tar -czf "$CONFIG_ARCHIVE" \
    docker-compose.prod.yml \
    env.prod.example \
    monitoring \
    nginx \
    >/dev/null 2>&1 || true

SHA256=$(shasum -a 256 "$BACKUP_FILE" | awk '{print $1}')
GIT_REVISION=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")

if [ -n "$BACKUP_ENCRYPTION_PASSPHRASE" ]; then
    ENCRYPTED_FILE="$BACKUP_FILE.enc"
    echo -e "${YELLOW}🔐 对备份执行 AES-256 加密...${NC}"
    openssl enc -aes-256-cbc -pbkdf2 -salt \
        -in "$BACKUP_FILE" \
        -out "$ENCRYPTED_FILE" \
        -pass "pass:$BACKUP_ENCRYPTION_PASSPHRASE"
    if [ "$KEEP_PLAINTEXT_BACKUP" != "true" ]; then
        rm -f "$BACKUP_FILE"
    fi
    BACKUP_FILE="$ENCRYPTED_FILE"
fi

if [ -n "$OFFSITE_BACKUP_DIR" ]; then
    mkdir -p "$OFFSITE_BACKUP_DIR"
    cp "$BACKUP_FILE" "$OFFSITE_BACKUP_DIR/"
    cp "$CONFIG_ARCHIVE" "$OFFSITE_BACKUP_DIR/" 2>/dev/null || true
fi

if [ -n "$OFFSITE_RCLONE_REMOTE" ] && command -v rclone >/dev/null 2>&1; then
    echo -e "${YELLOW}☁️  使用 rclone 推送异地备份...${NC}"
    rclone copyto "$BACKUP_FILE" "$OFFSITE_RCLONE_REMOTE/$(basename "$BACKUP_FILE")"
    rclone copyto "$CONFIG_ARCHIVE" "$OFFSITE_RCLONE_REMOTE/$(basename "$CONFIG_ARCHIVE")" || true
fi

SHA256=$(shasum -a 256 "$BACKUP_FILE" | awk '{print $1}')
FINAL_BACKUP_FILE="$BACKUP_FILE"
MANIFEST_FILE="$FINAL_BACKUP_FILE.manifest.json"

cat > "$MANIFEST_FILE" <<EOF
{
  "backup_file": "$(basename "$FINAL_BACKUP_FILE")",
  "label": "$LABEL",
  "created_at": "$DATE",
  "database": "$DB_NAME",
  "db_container": "$DB_CONTAINER",
  "db_user": "$DB_USER",
  "sha256": "$SHA256",
  "encrypted": $( [ -n "$BACKUP_ENCRYPTION_PASSPHRASE" ] && echo "true" || echo "false" ),
  "config_archive": "$(basename "$CONFIG_ARCHIVE")",
  "offsite_backup_dir": "${OFFSITE_BACKUP_DIR}",
  "offsite_rclone_remote": "${OFFSITE_RCLONE_REMOTE}",
  "git_revision": "$GIT_REVISION"
}
EOF

BACKUP_SUFFIX=$(basename "$FINAL_BACKUP_FILE" | sed "s/^backup_${DATE}_${LABEL}//")
ln -sfn "$(basename "$FINAL_BACKUP_FILE")" "$BACKUP_DIR/latest_${LABEL}${BACKUP_SUFFIX}"
ln -sfn "$(basename "$MANIFEST_FILE")" "$BACKUP_DIR/latest_${LABEL}.manifest.json"

# 删除旧备份（保留30天）
echo -e "${YELLOW}🗑️  清理旧备份（保留${RETENTION_DAYS}天）...${NC}"
find "$BACKUP_DIR" \( -name "backup_*.sql.gz" -o -name "backup_*.dump" -o -name "backup_*.sql.gz.enc" -o -name "backup_*.dump.enc" \) -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" \( -name "backup_*.sql.gz.manifest.json" -o -name "backup_*.dump.manifest.json" -o -name "backup_*.sql.gz.enc.manifest.json" -o -name "backup_*.dump.enc.manifest.json" \) -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "config_*.tar.gz" -mtime +$RETENTION_DAYS -delete

# 显示备份列表
echo ""
echo "当前备份文件:"
ls -lh "$BACKUP_DIR"/backup_* 2>/dev/null | tail -5 || echo "无备份文件"
echo "备份清单: $MANIFEST_FILE"

echo -e "${GREEN}✅ 备份完成${NC}"
