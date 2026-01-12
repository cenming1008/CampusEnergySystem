#!/bin/bash
# 后端容器重新构建并重启脚本（Mac 适配版）

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "🔨 重新构建后端镜像..."
docker compose build backend

echo "🔄 重启后端容器..."
docker compose up -d --build backend

echo "✅ 后端已重新构建并重启"
echo "📊 查看日志: docker compose logs -f backend"

