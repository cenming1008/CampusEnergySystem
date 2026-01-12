#!/bin/bash
# 数据库容器故障修复脚本

set -e

# 获取脚本所在目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}  🔧 数据库容器故障修复工具${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker 未安装${NC}"
    exit 1
fi

if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Docker 未运行，请先启动 Docker Desktop${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Docker 环境检查通过${NC}"
echo ""

# 显示当前状态
echo "📊 当前容器状态："
docker compose ps
echo ""

# 查看错误日志
echo "📋 数据库容器日志（最近 20 行）："
docker compose logs --tail=20 db 2>&1 || echo "无法获取日志"
echo ""

# 询问修复方式
echo -e "${YELLOW}请选择修复方式：${NC}"
echo "1. 修复权限（保留数据）"
echo "2. 重置数据库（删除所有数据，重新创建）"
echo "3. 仅查看日志"
echo "4. 退出"
echo ""
read -p "请输入选项 (1-4): " choice

case $choice in
    1)
        echo ""
        echo -e "${BLUE}🔧 修复权限...${NC}"
        
        # 停止容器
        echo "停止容器..."
        docker compose down
        
        # 修复权限
        echo "修复 pg_data 目录权限..."
        sudo chown -R $(id -u):$(id -g) pg_data/ 2>/dev/null || chown -R $(id -u):$(id -g) pg_data/
        chmod -R 755 pg_data/
        
        echo "修复其他目录权限..."
        chmod -R 755 mosquitto/ logs/ 2>/dev/null || true
        
        # 重新启动
        echo "重新启动容器..."
        docker compose up -d
        
        echo ""
        echo -e "${GREEN}✅ 权限修复完成${NC}"
        echo "等待容器启动..."
        sleep 5
        docker compose ps
        ;;
        
    2)
        echo ""
        echo -e "${RED}⚠️  警告：此操作将删除所有数据库数据！${NC}"
        read -p "确认继续？(yes/no): " confirm
        
        if [ "$confirm" != "yes" ]; then
            echo "已取消"
            exit 0
        fi
        
        echo ""
        echo -e "${BLUE}🗑️  重置数据库...${NC}"
        
        # 停止容器
        echo "停止容器..."
        docker compose down -v
        
        # 备份（可选）
        if [ -d "pg_data" ] && [ "$(ls -A pg_data)" ]; then
            echo "创建备份..."
            tar -czf pg_data_backup_$(date +%Y%m%d_%H%M%S).tar.gz pg_data/ 2>/dev/null || true
        fi
        
        # 删除数据
        echo "删除旧数据..."
        rm -rf pg_data/*
        
        # 重新启动
        echo "重新创建数据库..."
        docker compose up -d --build
        
        echo ""
        echo -e "${GREEN}✅ 数据库已重置${NC}"
        echo "等待容器启动..."
        sleep 5
        docker compose ps
        ;;
        
    3)
        echo ""
        echo -e "${BLUE}📋 完整日志：${NC}"
        docker compose logs db
        ;;
        
    4)
        echo "退出"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选项${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}💡 提示：${NC}"
echo "   查看日志: docker compose logs -f db"
echo "   查看状态: docker compose ps"
echo "   测试连接: docker exec -it mine_energy_db psql -U admin -d mine_energy -c 'SELECT 1;'"
