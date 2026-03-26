#!/bin/bash

# Docker 容器清理脚本
# 用途：清理所有 MineEnergySystem 相关的 Docker 资源

set -e

echo "🧹 MineEnergySystem Docker 清理脚本"
echo "======================================"
echo ""

# 检查是否在项目根目录
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ 错误：请在项目根目录运行此脚本"
    exit 1
fi

# 显示当前运行的容器
echo "📋 当前运行的容器："
docker ps --filter "name=mine" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""

# 询问确认
read -p "⚠️  是否要停止并删除所有容器？(y/N) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ 已取消"
    exit 0
fi

# 停止并删除容器（保留数据卷）
echo "1️⃣ 停止并删除容器..."
docker compose down

echo "✅ 容器已删除"
echo ""

# 询问是否删除数据卷
read -p "⚠️  是否要删除数据卷（会删除所有数据）？(y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "2️⃣ 删除数据卷..."
    docker volume rm mineenergysystem_redis_data 2>/dev/null || true
    docker volume rm mineenergysystem_pg_data 2>/dev/null || true
    echo "✅ 数据卷已删除"
else
    echo "⏭️  跳过删除数据卷"
fi
echo ""

# 询问是否删除镜像
read -p "是否要删除 Docker 镜像（节省磁盘空间）？(y/N) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "3️⃣ 删除镜像..."
    docker rmi mineenergysystem-backend 2>/dev/null || true
    docker rmi timescale/timescaledb:latest-pg14 2>/dev/null || true
    docker rmi redis:7.0-alpine 2>/dev/null || true
    docker rmi eclipse-mosquitto:2.0 2>/dev/null || true
    echo "✅ 镜像已删除"
else
    echo "⏭️  保留镜像"
fi
echo ""

# 清理未使用的资源
echo "4️⃣ 清理未使用的 Docker 资源..."
docker system prune -f
echo ""

echo "✅ 清理完成！"
echo ""
echo "💡 下一步："
echo "   - 如需本地运行，请参考 Docker清理与本地运行指南.md"
echo "   - 如需重新启动 Docker，运行：docker compose up -d"
echo ""
