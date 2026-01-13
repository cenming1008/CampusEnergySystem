#!/bin/bash
# 在 Docker 容器中运行设备模拟器
# 自动设置正确的环境变量

echo "🏭 启动设备模拟器..."
echo "提示：按 Ctrl+C 停止模拟器"
echo ""

docker exec mine_backend bash -c \
  "MQTT_BROKER=mqtt API_BASE=http://localhost:8088 python -u scripts/python/simulator.py"
