#!/bin/bash
# 生成 dev 用 MQTT TLS 自签证书 + 一设备一密钥 passwd + ACL。
# 幂等：证书/passwd 已存在则跳过，可加 --force 强制重生成。
# 用法: bash scripts/shell/gen_dev_mqtt_certs.sh [--force]

set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/../.." && pwd)
CERT_DIR="$PROJECT_DIR/mosquitto/config/certs"
PASSWD_FILE="$PROJECT_DIR/mosquitto/config/passwd"
ACL_FILE="$PROJECT_DIR/mosquitto/config/acl"
ENV_LOCAL="$PROJECT_DIR/.env.local.mqtt"

FORCE=""
FORCE_PASSWD=""
for arg in "$@"; do
    case "$arg" in
        --force)        FORCE=1 ;;        # 只强制重签 server.crt（默认行为）
        --force-passwd) FORCE_PASSWD=1 ;;  # 同时轮换 passwd / acl / 凭据（破坏性，会让旧 .env 失效）
    esac
done

mkdir -p "$CERT_DIR"

detect_lan_ips() {
    # macOS / Linux 通用：列出所有非环回 IPv4 地址
    if command -v ipconfig >/dev/null 2>&1 && [ "$(uname)" = "Darwin" ]; then
        for ifc in en0 en1 en2 en3; do
            ip=$(ipconfig getifaddr "$ifc" 2>/dev/null || true)
            [ -n "$ip" ] && echo "$ip"
        done
    else
        ifconfig 2>/dev/null | awk '/inet /{print $2}' | grep -v '^127\.'
    fi
}

build_san_block() {
    # 默认 SAN
    {
        echo "DNS.1 = mqtt"
        echo "DNS.2 = localhost"
        echo "IP.1  = 127.0.0.1"
    }
    # 额外 SAN: 来自 env MQTT_CERT_EXTRA_SANS（逗号分隔，DNS:xxx 或 IP:xxx）
    # 以及自动探测的 LAN IP
    local idx_ip=2 idx_dns=3
    local seen=""
    add_san() {
        local kind="$1" val="$2"
        case " $seen " in *" ${kind}:${val} "*) return ;; esac
        seen="$seen ${kind}:${val}"
        if [ "$kind" = "IP" ]; then
            echo "IP.${idx_ip}  = $val"
            idx_ip=$((idx_ip+1))
        else
            echo "DNS.${idx_dns} = $val"
            idx_dns=$((idx_dns+1))
        fi
    }
    if [ -n "${MQTT_CERT_EXTRA_SANS:-}" ]; then
        IFS=',' read -ra entries <<< "$MQTT_CERT_EXTRA_SANS"
        for e in "${entries[@]}"; do
            e=$(echo "$e" | xargs)
            case "$e" in
                IP:*)  add_san IP  "${e#IP:}" ;;
                DNS:*) add_san DNS "${e#DNS:}" ;;
                *)
                    if echo "$e" | grep -Eq '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$'; then
                        add_san IP "$e"
                    else
                        add_san DNS "$e"
                    fi
                    ;;
            esac
        done
    fi
    while read -r ip; do
        [ -n "$ip" ] && add_san IP "$ip"
    done < <(detect_lan_ips)
}

gen_certs() {
    cd "$CERT_DIR"

    # CA 一旦存在就保留（避免已下发的 ca.crt 失效）
    if [ ! -f ca.crt ] || [ ! -f ca.key ]; then
        echo "🔐 生成自签 CA..."
        openssl genrsa -out ca.key 4096
        openssl req -x509 -new -nodes -key ca.key -sha256 -days 3650 \
            -subj "/CN=CampusEnergy-Dev-CA" -out ca.crt
        chmod 600 ca.key
        chmod 644 ca.crt
    else
        echo "✅ CA 已存在，复用 (不会强制覆盖，避免已下发证书失效)"
    fi

    if [ -z "$FORCE" ] && [ -f "$CERT_DIR/server.crt" ] && [ -f "$CERT_DIR/server.key" ]; then
        echo "✅ server 证书已存在，跳过 (传 --force 强制重签)"
        return
    fi

    echo "🔐 生成 server 证书（SAN 包含本机所有 LAN IP）..."
    cat > server.cnf <<EOF
[ req ]
distinguished_name = req_distinguished_name
req_extensions = v3_req
prompt = no
[ req_distinguished_name ]
CN = mqtt
[ v3_req ]
basicConstraints = CA:FALSE
keyUsage = digitalSignature, keyEncipherment
extendedKeyUsage = serverAuth
subjectAltName = @alt_names
[ alt_names ]
$(build_san_block)
EOF
    echo "--- server cert SAN ---"
    grep -E '^(DNS|IP)\.' server.cnf
    echo "-----------------------"

    openssl genrsa -out server.key 4096
    openssl req -new -key server.key -config server.cnf -out server.csr
    openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial \
        -out server.crt -days 825 -sha256 -extensions v3_req -extfile server.cnf
    rm -f server.csr server.cnf ca.srl

    chmod 600 server.key
    chmod 644 server.crt
    echo "✅ server 证书已写入 $CERT_DIR/server.crt"
}

random_secret() {
    # 32 字符随机 (避免 pipefail 下 tr 因 SIGPIPE 中断脚本)
    openssl rand -base64 48 | LC_ALL=C tr -dc 'A-Za-z0-9' | cut -c1-32
}

gen_passwd_and_acl() {
    if [ -z "$FORCE_PASSWD" ] && [ -f "$PASSWD_FILE" ] && grep -q '^ingest-worker:' "$PASSWD_FILE"; then
        echo "✅ passwd 已是新结构，跳过 (传 --force-passwd 才会轮换凭据)"
        return
    fi

    INGEST_PWD=$(random_secret)
    CONTROL_PWD=$(random_secret)
    CAP001_PWD=$(random_secret)

    rm -f "$PASSWD_FILE"

    # 用 docker 里的 mosquitto_passwd 工具生成（与现有 setup_mqtt_auth.sh 一致）
    echo "🔐 生成 passwd（一设备一密钥）..."
    docker run --rm -v "$PROJECT_DIR/mosquitto/config:/mosquitto/config" \
        eclipse-mosquitto:2.0 \
        mosquitto_passwd -b -c /mosquitto/config/passwd ingest-worker "$INGEST_PWD"
    docker run --rm -v "$PROJECT_DIR/mosquitto/config:/mosquitto/config" \
        eclipse-mosquitto:2.0 \
        mosquitto_passwd -b /mosquitto/config/passwd control-publisher "$CONTROL_PWD"
    docker run --rm -v "$PROJECT_DIR/mosquitto/config:/mosquitto/config" \
        eclipse-mosquitto:2.0 \
        mosquitto_passwd -b /mosquitto/config/passwd cap-001 "$CAP001_PWD"
    chmod 600 "$PASSWD_FILE"

    cat > "$ACL_FILE" <<'ACL'
# 后端 ingest worker：仅订阅遥测，不能写
user ingest-worker
topic read campus/telemetry
topic read campus/device/+/telemetry

# 后端控制下发：仅可发布控制 topic
user control-publisher
topic write campus/control/+
topic write campus/control/+/+

# 设备 CAP-001：只能发自己 SN 的 telemetry；只能订阅自己的控制
user cap-001
topic write campus/device/CAP-001/telemetry
topic read  campus/control/CAP-001
topic read  campus/control/CAP-001/+
ACL
    chmod 644 "$ACL_FILE"

    cat > "$ENV_LOCAL" <<EOF
# Auto-generated by gen_dev_mqtt_certs.sh — DO NOT commit
# 把以下条目合并到 .env 中（或 source 进环境变量）
MQTT_BROKER=localhost
MQTT_PORT=8883
MQTT_TLS_ENABLED=True
MQTT_TLS_CA_PATH=$CERT_DIR/ca.crt
MQTT_TLS_INSECURE=False
# 兼容旧字段（ingest worker 用）
MQTT_USERNAME=ingest-worker
MQTT_PASSWORD=$INGEST_PWD
# 分角色凭据
MQTT_INGEST_USERNAME=ingest-worker
MQTT_INGEST_PASSWORD=$INGEST_PWD
MQTT_CONTROL_USERNAME=control-publisher
MQTT_CONTROL_PASSWORD=$CONTROL_PWD
# 设备模拟器 (dev_simulate_cap001.py 使用)
MQTT_DEVICE_CAP001_USERNAME=cap-001
MQTT_DEVICE_CAP001_PASSWORD=$CAP001_PWD
EOF
    chmod 600 "$ENV_LOCAL"
    echo "✅ passwd/acl/凭据已生成"
    echo "   凭据片段写入: $ENV_LOCAL"
    echo "   请手动合并到项目根目录 .env"
}

gen_certs
gen_passwd_and_acl

echo ""
echo "完成。下一步："
echo "  1) 把 $ENV_LOCAL 中的变量合并进 .env"
echo "  2) docker compose -f docker-compose.dev.yml up -d mqtt"
echo "  3) python scripts/python/dev_simulate_cap001.py  # 验证 TLS+ACL 链路"
