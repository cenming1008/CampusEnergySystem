#!/bin/bash
# ============================================
# 单站试点就绪检查与证据归档脚本
# ============================================

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
cd "$PROJECT_DIR"

ENV_FILE=""
ARTIFACT_DIR=""
SKIP_TESTS="false"
INSTALL_DEPS="false"

while [[ $# -gt 0 ]]; do
    case "$1" in
        --env-file)
            ENV_FILE="${2:-}"
            shift 2
            ;;
        --artifact-dir)
            ARTIFACT_DIR="${2:-}"
            shift 2
            ;;
        --skip-tests)
            SKIP_TESTS="true"
            shift
            ;;
        --install-deps)
            INSTALL_DEPS="true"
            shift
            ;;
        *)
            echo "❌ 未知参数: $1"
            echo "用法: $0 [--env-file .env.prod] [--artifact-dir artifacts/pilot/xxx] [--skip-tests] [--install-deps]"
            exit 1
            ;;
    esac
done

if [ -z "$ENV_FILE" ]; then
    if [ -f ".env.prod" ]; then
        ENV_FILE=".env.prod"
    else
        ENV_FILE="env.prod.example"
    fi
fi

if [ -z "$ARTIFACT_DIR" ]; then
    TIMESTAMP=$(date +%Y%m%d_%H%M%S)
    ARTIFACT_DIR="artifacts/pilot/${TIMESTAMP}"
fi

mkdir -p "$ARTIFACT_DIR"
LOG_DIR="$ARTIFACT_DIR/logs"
mkdir -p "$LOG_DIR"

if [ "$INSTALL_DEPS" = "true" ]; then
    bash ./scripts/shell/install_dependencies.sh | tee "$LOG_DIR/install_dependencies.log"
fi

if [ -x "./venv/bin/python" ]; then
    PYTHON_BIN="./venv/bin/python"
else
    PYTHON_BIN="python3"
fi

STATUS_FILE="$ARTIFACT_DIR/status.txt"
: > "$STATUS_FILE"

if "$PYTHON_BIN" -m alembic --help >/dev/null 2>&1; then
    ALEMBIC_RUNNER=("$PYTHON_BIN" -m alembic)
elif command -v alembic >/dev/null 2>&1; then
    ALEMBIC_RUNNER=(alembic)
else
    echo "FAIL alembic_missing" | tee -a "$STATUS_FILE"
    echo "未找到 alembic，可先运行: bash ./scripts/shell/install_dependencies.sh" >&2
    exit 1
fi

run_step() {
    local step_name="$1"
    shift
    local log_file="$LOG_DIR/${step_name}.log"
    echo "==> ${step_name}" | tee -a "$STATUS_FILE"
    if "$@" >"$log_file" 2>&1; then
        echo "PASS ${step_name}" | tee -a "$STATUS_FILE"
    else
        echo "FAIL ${step_name}" | tee -a "$STATUS_FILE"
        cat "$log_file"
        return 1
    fi
}

run_python_module_check() {
    "$PYTHON_BIN" - <<'PY'
import importlib
import sys

required_modules = [
    "fastapi",
    "sqlmodel",
    "dotenv",
    "requests",
    "coverage",
]

missing = []
for module_name in required_modules:
    try:
        importlib.import_module(module_name)
    except Exception:
        missing.append(module_name)

if missing:
    print("missing_modules=" + ",".join(missing))
    sys.exit(1)
PY
}

if [ "$ENV_FILE" = ".env.prod" ] && git ls-files --error-unmatch .env.prod >/dev/null 2>&1; then
    echo "FAIL tracked_env_prod" | tee -a "$STATUS_FILE"
    echo ".env.prod 不能被 Git 跟踪，请改为仅保留本地文件" >&2
    exit 1
fi

TEMP_ENV_CREATED="false"
cleanup_temp_env() {
    if [ "$TEMP_ENV_CREATED" = "true" ] && [ -f ".env" ]; then
        rm -f .env
    fi
}
trap cleanup_temp_env EXIT

if [ ! -f ".env" ] && [ -f "env.example" ]; then
    cp env.example .env
    TEMP_ENV_CREATED="true"
fi

run_step dependency_check run_python_module_check
run_step compileall env PYTHONPYCACHEPREFIX=/tmp "$PYTHON_BIN" -m compileall -q app tests scripts/python migrations
run_step config_check "$PYTHON_BIN" scripts/python/check_config.py
run_step production_readiness "$PYTHON_BIN" scripts/python/check_production_readiness.py --env-file "$ENV_FILE"
run_step migration_sql "${ALEMBIC_RUNNER[@]}" upgrade head --sql
run_step compose_config docker compose -f docker-compose.prod.yml --env-file "$ENV_FILE" config

if [ "$SKIP_TESTS" != "true" ]; then
    run_step unit_tests "$PYTHON_BIN" -m unittest discover -s tests -p 'test_*.py'
fi

PASS_COUNT=$(grep -c '^PASS ' "$STATUS_FILE" || true)
FAIL_COUNT=$(grep -c '^FAIL ' "$STATUS_FILE" || true)
SUMMARY_FILE="$ARTIFACT_DIR/summary.md"

cat > "$SUMMARY_FILE" <<EOF
# 试点就绪检查结果

- 生成时间: $(date '+%Y-%m-%d %H:%M:%S %Z')
- 环境文件: \`$ENV_FILE\`
- Python: \`$PYTHON_BIN\`
- 通过项: $PASS_COUNT
- 失败项: $FAIL_COUNT
- 测试状态: $( [ "$SKIP_TESTS" = "true" ] && echo "跳过" || echo "已执行" )

## 执行项

$(sed 's/^/- /' "$STATUS_FILE")

## 证据目录

- 日志目录: \`$LOG_DIR\`
- 汇总文件: \`$SUMMARY_FILE\`
EOF

echo "✅ 试点就绪检查完成"
echo "证据目录: $ARTIFACT_DIR"
