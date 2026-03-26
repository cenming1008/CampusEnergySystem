#!/bin/bash
# ============================================
# 单站试点演练总入口
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

ENV_FILE="${ENV_FILE:-.env.prod}"
BASE_URL="${BASE_URL:-http://127.0.0.1:8088}"
ARTIFACT_ROOT="${ARTIFACT_ROOT:-artifacts/pilot/$(date +%Y%m%d_%H%M%S)}"
SKIP_TESTS="${SKIP_TESTS:-false}"
SKIP_BASELINE="${SKIP_BASELINE:-false}"
SKIP_SMOKE="${SKIP_SMOKE:-false}"
INSTALL_DEPS="${INSTALL_DEPS:-false}"

mkdir -p "$ARTIFACT_ROOT"

if [ ! -f "$ENV_FILE" ]; then
    echo "❌ 未找到环境文件: $ENV_FILE"
    exit 1
fi

echo "==> 1. 试点 readiness 检查"
READINESS_ARGS=(--env-file "$ENV_FILE" --artifact-dir "$ARTIFACT_ROOT/readiness")
if [ "$SKIP_TESTS" = "true" ]; then
    READINESS_ARGS+=(--skip-tests)
fi
if [ "$INSTALL_DEPS" = "true" ]; then
    READINESS_ARGS+=(--install-deps)
fi
bash ./scripts/shell/pilot_readiness.sh "${READINESS_ARGS[@]}"

if [ "$SKIP_BASELINE" != "true" ]; then
    echo "==> 2. 容量基线"
    LOAD_OUTPUT_DIR="$ARTIFACT_ROOT/load" \
    BASE_URL="$BASE_URL" \
    LOAD_USERNAME="${LOAD_USERNAME:-}" \
    LOAD_PASSWORD="${LOAD_PASSWORD:-}" \
    bash ./scripts/shell/load_baseline.sh
else
    echo "==> 2. 跳过容量基线"
fi

if [ "$SKIP_SMOKE" != "true" ]; then
    echo "==> 3. 部署后冒烟"
    BACKEND_URL="$BASE_URL" \
    SMOKE_USERNAME="${SMOKE_USERNAME:-${LOAD_USERNAME:-}}" \
    SMOKE_PASSWORD="${SMOKE_PASSWORD:-${LOAD_PASSWORD:-}}" \
    bash ./scripts/shell/pilot_smoke_test.sh | tee "$ARTIFACT_ROOT/pilot_smoke.log"
else
    echo "==> 3. 跳过部署后冒烟"
fi

SUMMARY_FILE="$ARTIFACT_ROOT/summary.md"
cat > "$SUMMARY_FILE" <<EOF
# 单站试点演练汇总

- 时间: $(date '+%Y-%m-%d %H:%M:%S %Z')
- 环境文件: \`$ENV_FILE\`
- BASE_URL: \`$BASE_URL\`
- readiness: \`$ARTIFACT_ROOT/readiness\`
- baseline: $( [ "$SKIP_BASELINE" = "true" ] && echo "skipped" || echo "\`$ARTIFACT_ROOT/load\`" )
- smoke: $( [ "$SKIP_SMOKE" = "true" ] && echo "skipped" || echo "\`$ARTIFACT_ROOT/pilot_smoke.log\`" )
EOF

echo "✅ 单站试点演练完成"
echo "汇总文件: $SUMMARY_FILE"
