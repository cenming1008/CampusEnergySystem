#!/bin/bash
# WebSocket 连接诊断脚本

echo "🔍 WebSocket 连接诊断工具"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查后端服务
echo -e "${BLUE}1. 检查后端服务状态...${NC}"
if curl -s -f http://localhost:8088/docs > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务正在运行 (http://localhost:8088)${NC}"
else
    echo -e "${RED}❌ 后端服务未运行或无法访问${NC}"
    echo -e "${YELLOW}💡 请运行: ./start.sh 或 docker compose up -d${NC}"
    exit 1
fi
echo ""

# 检查 Docker 容器
echo -e "${BLUE}2. 检查 Docker 容器状态...${NC}"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    BACKEND_STATUS=$(docker compose ps backend 2>/dev/null | grep -c "Up" || echo "0")
    if [ "$BACKEND_STATUS" -gt 0 ]; then
        echo -e "${GREEN}✅ 后端容器正在运行${NC}"
        docker compose ps backend
    else
        echo -e "${YELLOW}⚠️  后端容器未运行${NC}"
        echo -e "${YELLOW}💡 请运行: docker compose up -d${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Docker 未运行或未安装${NC}"
fi
echo ""

# 检查端口占用
echo -e "${BLUE}3. 检查端口占用...${NC}"
if lsof -i :8088 &> /dev/null; then
    PROCESS=$(lsof -i :8088 | tail -n 1 | awk '{print $1}')
    echo -e "${GREEN}✅ 端口 8088 被占用 (进程: $PROCESS)${NC}"
else
    echo -e "${RED}❌ 端口 8088 未被占用${NC}"
fi

if lsof -i :3000 &> /dev/null; then
    PROCESS=$(lsof -i :3000 | tail -n 1 | awk '{print $1}')
    echo -e "${GREEN}✅ 端口 3000 被占用 (进程: $PROCESS)${NC}"
else
    echo -e "${YELLOW}⚠️  端口 3000 未被占用 (前端可能未运行)${NC}"
fi
echo ""

# 测试 WebSocket 连接（使用 wscat 或 curl）
echo -e "${BLUE}4. 测试 WebSocket 端点...${NC}"
if command -v wscat &> /dev/null; then
    echo "使用 wscat 测试 WebSocket 连接..."
    timeout 3 wscat -c ws://localhost:8088/ws 2>&1 | head -n 5 || echo -e "${YELLOW}⚠️  WebSocket 连接测试超时或失败${NC}"
elif command -v curl &> /dev/null; then
    echo "使用 curl 测试 WebSocket 升级..."
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Connection: Upgrade" \
        -H "Upgrade: websocket" \
        -H "Sec-WebSocket-Version: 13" \
        -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
        http://localhost:8088/ws 2>&1)
    if [ "$HTTP_CODE" = "101" ]; then
        echo -e "${GREEN}✅ WebSocket 端点响应正常 (HTTP 101 Switching Protocols)${NC}"
    else
        echo -e "${YELLOW}⚠️  WebSocket 端点响应: HTTP $HTTP_CODE${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  未找到 wscat 或 curl，跳过 WebSocket 测试${NC}"
fi
echo ""

# 检查后端日志
echo -e "${BLUE}5. 检查后端日志（最近 10 行）...${NC}"
if command -v docker &> /dev/null && docker info &> /dev/null; then
    echo -e "${YELLOW}最近的后端日志:${NC}"
    docker compose logs --tail=10 backend 2>/dev/null | grep -i "websocket\|ws\|error\|error" || echo "无相关日志"
else
    echo -e "${YELLOW}⚠️  无法访问 Docker 日志${NC}"
fi
echo ""

# 总结
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}📋 诊断完成${NC}"
echo ""
echo -e "${BLUE}💡 如果问题仍然存在，请检查:${NC}"
echo "   1. 后端服务是否正常运行: docker compose ps"
echo "   2. 后端日志: docker compose logs -f backend"
echo "   3. 前端控制台错误信息"
echo "   4. 网络连接和防火墙设置"
echo ""
echo -e "${BLUE}🔧 常用命令:${NC}"
echo "   启动服务: ./start.sh"
echo "   查看日志: docker compose logs -f backend"
echo "   重启服务: docker compose restart backend"
echo "   停止服务: docker compose down"
echo ""
