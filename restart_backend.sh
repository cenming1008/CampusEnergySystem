#!/bin/bash
# 后端容器重启脚本

cd /www/wwwroot/MineEnergySystem

echo "🔄 重启后端容器..."
docker-compose restart backend

echo "✅ 后端容器已重启"
echo "📊 查看日志: docker-compose logs -f backend"

