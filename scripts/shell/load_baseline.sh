#!/bin/bash
# ============================================
# 后端容量基线脚本
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

PYTHON_BIN="./venv/bin/python"
if [ ! -x "$PYTHON_BIN" ]; then
    PYTHON_BIN="python3"
fi

BASE_URL="${BASE_URL:-http://127.0.0.1:8088}"
WORKERS="${LOAD_WORKERS:-20}"
DURATION_SECONDS="${LOAD_DURATION_SECONDS:-60}"
OUTPUT_DIR="${LOAD_OUTPUT_DIR:-artifacts/load/$(date +%Y%m%d_%H%M%S)}"
HEALTH_LIVE_MIN_RPS="${HEALTH_LIVE_MIN_RPS:-20}"
HEALTH_LIVE_MAX_P95_MS="${HEALTH_LIVE_MAX_P95_MS:-200}"
HEALTH_LIVE_MIN_SUCCESS_RATE="${HEALTH_LIVE_MIN_SUCCESS_RATE:-99.9}"
AUTH_LOGIN_MIN_RPS="${AUTH_LOGIN_MIN_RPS:-5}"
AUTH_LOGIN_MAX_P95_MS="${AUTH_LOGIN_MAX_P95_MS:-500}"
AUTH_LOGIN_MIN_SUCCESS_RATE="${AUTH_LOGIN_MIN_SUCCESS_RATE:-99}"
AUTH_LOGIN_WORKERS="${AUTH_LOGIN_WORKERS:-2}"
AUTH_LOGIN_DURATION_SECONDS="${AUTH_LOGIN_DURATION_SECONDS:-5}"
AUTH_LOGIN_REQUESTS_PER_WORKER="${AUTH_LOGIN_REQUESTS_PER_WORKER:-1}"
AUTH_HEALTH_MIN_RPS="${AUTH_HEALTH_MIN_RPS:-5}"
AUTH_HEALTH_MAX_P95_MS="${AUTH_HEALTH_MAX_P95_MS:-300}"
AUTH_HEALTH_MIN_SUCCESS_RATE="${AUTH_HEALTH_MIN_SUCCESS_RATE:-99}"
AUTH_HEALTH_WORKERS="${AUTH_HEALTH_WORKERS:-5}"
AUTH_HEALTH_DURATION_SECONDS="${AUTH_HEALTH_DURATION_SECONDS:-10}"

mkdir -p "$OUTPUT_DIR"

evaluate_report() {
  local report_file="$1"
  local output_md="$2"
  local min_rps="$3"
  local max_p95_ms="$4"
  local min_success_rate="$5"

  "$PYTHON_BIN" scripts/python/evaluate_capacity_baseline.py \
    --report "$report_file" \
    --min-rps "$min_rps" \
    --max-p95-ms "$max_p95_ms" \
    --min-success-rate "$min_success_rate" \
    --max-failed-requests 0 \
    --expect-status-code 200 \
    --output-md "$output_md"
}

echo "==> 1. health/live baseline"
"$PYTHON_BIN" scripts/python/stress_test.py \
  --base-url "$BASE_URL" \
  --endpoint /health/live \
  --workers "$WORKERS" \
  --duration-seconds "$DURATION_SECONDS" \
  --output "$OUTPUT_DIR/health_live.json"
evaluate_report \
  "$OUTPUT_DIR/health_live.json" \
  "$OUTPUT_DIR/health_live.md" \
  "$HEALTH_LIVE_MIN_RPS" \
  "$HEALTH_LIVE_MAX_P95_MS" \
  "$HEALTH_LIVE_MIN_SUCCESS_RATE"

if [ -n "${LOAD_USERNAME:-}" ] && [ -n "${LOAD_PASSWORD:-}" ]; then
  echo "==> 2. auth/login baseline"
  "$PYTHON_BIN" scripts/python/stress_test.py \
    --base-url "$BASE_URL" \
    --endpoint /auth/login \
    --method POST \
    --workers "$AUTH_LOGIN_WORKERS" \
    --duration-seconds "$AUTH_LOGIN_DURATION_SECONDS" \
    --requests-per-worker "$AUTH_LOGIN_REQUESTS_PER_WORKER" \
    --headers-json '{"Content-Type":"application/x-www-form-urlencoded"}' \
    --body-form-json "{\"username\":\"${LOAD_USERNAME}\",\"password\":\"${LOAD_PASSWORD}\"}" \
    --output "$OUTPUT_DIR/auth_login.json"
  evaluate_report \
    "$OUTPUT_DIR/auth_login.json" \
    "$OUTPUT_DIR/auth_login.md" \
    "$AUTH_LOGIN_MIN_RPS" \
    "$AUTH_LOGIN_MAX_P95_MS" \
    "$AUTH_LOGIN_MIN_SUCCESS_RATE"

  echo "==> 3. authenticated health baseline"
  "$PYTHON_BIN" scripts/python/stress_test.py \
    --base-url "$BASE_URL" \
    --endpoint /health \
    --workers "$AUTH_HEALTH_WORKERS" \
    --duration-seconds "$AUTH_HEALTH_DURATION_SECONDS" \
    --username "$LOAD_USERNAME" \
    --password "$LOAD_PASSWORD" \
    --output "$OUTPUT_DIR/health_authenticated.json"
  evaluate_report \
    "$OUTPUT_DIR/health_authenticated.json" \
    "$OUTPUT_DIR/health_authenticated.md" \
    "$AUTH_HEALTH_MIN_RPS" \
    "$AUTH_HEALTH_MAX_P95_MS" \
    "$AUTH_HEALTH_MIN_SUCCESS_RATE"
else
  echo "==> 跳过登录类基线（未提供 LOAD_USERNAME / LOAD_PASSWORD）"
fi

SUMMARY_FILE="$OUTPUT_DIR/summary.md"
{
  echo "# 后端容量基线汇总"
  echo
  echo "- BASE_URL: \`$BASE_URL\`"
  echo "- workers: $WORKERS"
  echo "- duration_seconds: $DURATION_SECONDS"
  echo
  echo "## 报告"
  echo
  echo "- health_live.json"
  echo "- health_live.md"
  if [ -f "$OUTPUT_DIR/auth_login.json" ]; then
    echo "- auth_login.json"
    echo "- auth_login.md"
  fi
  if [ -f "$OUTPUT_DIR/health_authenticated.json" ]; then
    echo "- health_authenticated.json"
    echo "- health_authenticated.md"
  fi
} > "$SUMMARY_FILE"

echo "基线报告目录: $OUTPUT_DIR"
echo "基线汇总: $SUMMARY_FILE"
