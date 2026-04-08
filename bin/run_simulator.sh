#!/bin/bash
# 在 Docker 容器中运行统一设备模拟器

set -e

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
cd "$PROJECT_DIR"

if ! docker ps --format '{{.Names}}' | grep -q '^campus_backend$'; then
    echo "❌ 未检测到 campus_backend 容器"
    echo "请先启动系统，例如执行: ./bin/fast_start.sh"
    exit 1
fi

echo "🏭 启动统一设备模拟器..."
echo "支持：电、水、气、热、冷等多种能源类型"
echo "说明：脚本进入 campus_backend 容器执行，但容器内 MQTT 仍通过 service 名 mqtt 访问"
echo "提示：按 Ctrl+C 停止模拟器"
echo ""

docker exec campus_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 \
   MQTT_USERNAME=\${MQTT_USERNAME:-campus_mqtt} \
   MQTT_PASSWORD=\${MQTT_PASSWORD:-campus_mqtt_secret_2026} \
   ADMIN_PASSWORD=\${ADMIN_PASSWORD:-} \
   python -u scripts/python/simulator_unified.py"
