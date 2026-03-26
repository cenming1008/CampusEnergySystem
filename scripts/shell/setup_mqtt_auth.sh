#!/bin/bash
# ============================================
# 生成 Mosquitto 密码文件
# ============================================
# 使用 Docker 中的 mosquitto_passwd 工具生成密码文件
# 用法: ./scripts/shell/setup_mqtt_auth.sh [username] [password]
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
PASSWD_FILE="$PROJECT_DIR/mosquitto/config/passwd"
USERNAME="${1:-mine_mqtt}"
PASSWORD="${2:-mine_mqtt_secret_2026}"
FORCE_OVERWRITE="${3:-}"

if [ -f "$PASSWD_FILE" ] && [ "$FORCE_OVERWRITE" != "--force" ]; then
    echo "⚠️  密码文件已存在: $PASSWD_FILE"
    read -p "是否覆盖? (yes/no): " confirm
    if [ "$confirm" != "yes" ]; then
        echo "已取消"
        exit 0
    fi
fi

echo "🔐 生成 Mosquitto 密码文件..."
echo "   用户名: $USERNAME"

docker run --rm -v "$PROJECT_DIR/mosquitto/config:/mosquitto/config" \
    eclipse-mosquitto:2.0 \
    mosquitto_passwd -b -c /mosquitto/config/passwd "$USERNAME" "$PASSWORD"

chmod 600 "$PASSWD_FILE"
echo "✅ 密码文件已生成: $PASSWD_FILE"
echo ""
echo "请在 .env 中设置以下环境变量:"
echo "  MQTT_USERNAME=$USERNAME"
echo "  MQTT_PASSWORD=$PASSWORD"
