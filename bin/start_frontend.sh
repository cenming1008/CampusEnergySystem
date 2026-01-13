#!/bin/bash
# 启动前端开发服务器

echo "🎨 启动前端开发服务器..."
echo ""

# 检查是否已安装依赖
if [ ! -d "frontend/node_modules" ]; then
    echo "📦 首次启动，正在安装依赖..."
    cd frontend && npm install && cd ..
    echo ""
fi

# 启动前端
echo "🚀 启动中..."
cd frontend && npm run dev
