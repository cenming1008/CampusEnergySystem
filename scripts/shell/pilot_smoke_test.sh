#!/bin/bash
# ============================================
# 试点联调冒烟脚本
# ============================================
# 目标：
# 1. 校验对外公开的交付面是否可访问
# 2. 可选校验认证链路与受保护接口
# 3. 用于部署后 5 分钟内的快速验收
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
BACKEND_URL="${BACKEND_URL:-http://localhost:8088}"
USERNAME="${SMOKE_USERNAME:-}"
PASSWORD="${SMOKE_PASSWORD:-}"
if [[ -x "$PROJECT_DIR/venv/bin/python" ]]; then
    PYTHON_BIN="$PROJECT_DIR/venv/bin/python"
else
    PYTHON_BIN="python3"
fi

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

fail() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

check_json_endpoint() {
    local name="$1"
    local path="$2"

    echo "检查 ${name}: ${BACKEND_URL}${path}"
    local body
    local code
    body=$(curl -sS -o /tmp/mine_smoke_body.json -w "%{http_code}" "${BACKEND_URL}${path}") || fail "${name} 请求失败"
    code="$body"
    if [[ "$code" != "200" ]]; then
        cat /tmp/mine_smoke_body.json
        fail "${name} 返回状态码 ${code}"
    fi
    cat /tmp/mine_smoke_body.json | python3 -m json.tool >/dev/null 2>&1 || fail "${name} 返回内容不是有效 JSON"
    pass "${name} 可用"
}

echo "==> MineEnergySystem 试点联调冒烟检查"
echo "后端地址: ${BACKEND_URL}"

check_json_endpoint "健康检查" "/health"
check_json_endpoint "存活检查" "/health/live"
check_json_endpoint "就绪检查" "/health/ready"

echo "检查 metrics: ${BACKEND_URL}/metrics"
METRICS_CODE=$(curl -sS -o /tmp/mine_smoke_metrics.out -w "%{http_code}" "${BACKEND_URL}/metrics") || fail "metrics 请求失败"
[[ "$METRICS_CODE" == "200" ]] || fail "metrics 返回状态码 ${METRICS_CODE}"
grep -q "process_" /tmp/mine_smoke_metrics.out || warn "metrics 已返回，但未找到 process_* 指标"
pass "metrics 可用"

if [[ -n "$USERNAME" && -n "$PASSWORD" ]]; then
    echo "检查认证链路: ${USERNAME}"
    TOKEN_JSON=$(curl -sS -X POST "${BACKEND_URL}/auth/login" \
        -H "Content-Type: application/x-www-form-urlencoded" \
        --data-urlencode "username=${USERNAME}" \
        --data-urlencode "password=${PASSWORD}")

    ACCESS_TOKEN=$(TOKEN_JSON="$TOKEN_JSON" "$PYTHON_BIN" - <<'PY'
import json
import os

payload = json.loads(os.environ["TOKEN_JSON"])
print(payload.get("access_token", ""))
PY
)

    if [[ -z "$ACCESS_TOKEN" ]]; then
        echo "$TOKEN_JSON"
        fail "认证链路失败，未获取 access token"
    fi
    pass "登录成功"

    AUTH_CODE=$(curl -sS -o /tmp/mine_smoke_audit.json -w "%{http_code}" \
        -H "Authorization: Bearer ${ACCESS_TOKEN}" \
        "${BACKEND_URL}/audit/events?limit=1")

    if [[ "$AUTH_CODE" == "200" || "$AUTH_CODE" == "403" ]]; then
        pass "受保护接口可访问（权限结果符合预期）"
    else
        cat /tmp/mine_smoke_audit.json
        fail "受保护接口返回状态码 ${AUTH_CODE}"
    fi
else
    warn "未提供 SMOKE_USERNAME / SMOKE_PASSWORD，跳过认证链路验证"
fi

echo "==> 冒烟检查完成"
