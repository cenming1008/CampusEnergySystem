#!/bin/bash
# 在 Docker 容器中运行统一设备模拟器
# 自动设置正确的环境变量
# 支持多能源类型和远程控制

echo "🏭 启动统一设备模拟器..."
echo "支持：电、水、气、热、冷等多种能源类型"
echo "提示：按 Ctrl+C 停止模拟器"
echo ""

docker exec mine_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 python -u scripts/python/simulator_unified.py"
