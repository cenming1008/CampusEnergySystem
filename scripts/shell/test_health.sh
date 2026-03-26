#!/bin/bash

# 健康检查端点测试脚本
# 用于验证健康检查功能是否正常工作

echo "🔍 健康检查端点测试"
echo "===================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 后端地址
BACKEND_URL="http://localhost:8088"

# 检查后端是否运行
echo "1️⃣  检查后端服务是否运行..."
if curl -s --connect-timeout 2 "$BACKEND_URL/docs" > /dev/null 2>&1; then
    echo -e "${GREEN}✅ 后端服务正在运行${NC}"
else
    echo -e "${RED}❌ 后端服务未运行，请先启动：${NC}"
    echo "   cd <项目根目录>"
    echo "   docker compose up -d"
    exit 1
fi

echo ""
echo "2️⃣  测试 /health 端点..."
HEALTH_RESPONSE=$(curl -s "$BACKEND_URL/health")
HEALTH_STATUS=$(echo "$HEALTH_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

echo "响应内容："
echo "$HEALTH_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$HEALTH_RESPONSE"

if [ "$HEALTH_STATUS" = "healthy" ]; then
    echo -e "${GREEN}✅ 系统状态: healthy${NC}"
elif [ "$HEALTH_STATUS" = "degraded" ]; then
    echo -e "${YELLOW}⚠️  系统状态: degraded (部分服务降级)${NC}"
else
    echo -e "${RED}❌ 系统状态: unhealthy${NC}"
fi

echo ""
echo "3️⃣  测试 /health/live 端点（存活检查）..."
LIVE_RESPONSE=$(curl -s "$BACKEND_URL/health/live")
LIVE_STATUS=$(echo "$LIVE_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

echo "响应内容："
echo "$LIVE_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$LIVE_RESPONSE"

if [ "$LIVE_STATUS" = "alive" ]; then
    echo -e "${GREEN}✅ 存活检查: alive${NC}"
else
    echo -e "${RED}❌ 存活检查失败${NC}"
fi

echo ""
echo "4️⃣  测试 /health/ready 端点（就绪检查）..."
READY_RESPONSE=$(curl -s "$BACKEND_URL/health/ready")
READY_STATUS=$(echo "$READY_RESPONSE" | grep -o '"status":"[^"]*"' | cut -d'"' -f4)

echo "响应内容："
echo "$READY_RESPONSE" | python3 -m json.tool 2>/dev/null || echo "$READY_RESPONSE"

if [ "$READY_STATUS" = "ready" ]; then
    echo -e "${GREEN}✅ 就绪检查: ready${NC}"
else
    echo -e "${RED}❌ 就绪检查: not_ready${NC}"
fi

echo ""
echo "5️⃣  测试 Docker 健康检查..."
CONTAINER_HEALTH=$(docker inspect mine_backend --format='{{.State.Health.Status}}' 2>/dev/null)

if [ "$CONTAINER_HEALTH" = "healthy" ]; then
    echo -e "${GREEN}✅ Docker 容器健康检查: healthy${NC}"
elif [ "$CONTAINER_HEALTH" = "starting" ]; then
    echo -e "${YELLOW}⚠️  Docker 容器健康检查: starting (启动中)${NC}"
elif [ "$CONTAINER_HEALTH" = "" ]; then
    echo -e "${YELLOW}⚠️  Docker 容器未运行或未配置健康检查${NC}"
else
    echo -e "${RED}❌ Docker 容器健康检查: $CONTAINER_HEALTH${NC}"
fi

echo ""
echo "===================="
echo "✨ 测试完成！"
echo ""
echo "📖 健康检查端点说明："
echo "   - /health       : 完整的系统健康检查（推荐用于监控）"
echo "   - /health/live  : 存活检查（Kubernetes liveness probe）"
echo "   - /health/ready : 就绪检查（Kubernetes readiness probe）"
echo ""
echo "🔗 查看 API 文档："
echo "   http://localhost:8088/docs#/系统健康"
