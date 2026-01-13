#!/bin/bash
# 检查系统配置和状态

echo "🔍 系统检查..."
echo ""

echo "1️⃣ 检查 Docker 容器状态："
docker compose ps
echo ""

echo "2️⃣ 检查系统配置："
docker exec mine_backend python scripts/python/check_config.py
echo ""

echo "3️⃣ 测试 API 健康检查："
curl -s http://localhost:8088/health | python -m json.tool
echo ""

echo "✅ 系统检查完成！"
