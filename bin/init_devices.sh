#!/bin/bash
# 初始化测试设备

echo "🔧 正在初始化测试设备..."
echo ""

docker exec mine_backend bash -c \
  "API_BASE=http://localhost:8088 python scripts/python/init_devices.py"

echo ""
echo "✅ 完成！"
