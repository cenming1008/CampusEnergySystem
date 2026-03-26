#!/bin/sh
set -eu

TEMPLATE_PATH="${ALERTMANAGER_TEMPLATE_PATH:-/etc/alertmanager/alertmanager.yml.template}"
TARGET_PATH="${ALERTMANAGER_TARGET_PATH:-/etc/alertmanager/alertmanager.yml}"

CHANNEL="${ALERTMANAGER_CHANNEL:-webhook}"
WEBHOOK_URL="${ALERTMANAGER_WEBHOOK_URL:-}"

looks_like_placeholder() {
    case "$1" in
        *replace-with-real*|*example.com*|*hooks.example.com*|*hooks.invalid*|"")
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

if [ "$CHANNEL" = "email" ]; then
    if [ -z "${ALERTMANAGER_EMAIL_TO:-}" ] || [ -z "${ALERTMANAGER_EMAIL_FROM:-}" ] || [ -z "${ALERTMANAGER_SMARTHOST:-}" ]; then
        echo "Alertmanager email channel is selected but email settings are incomplete" >&2
        exit 1
    fi
else
    if [ -z "$WEBHOOK_URL" ]; then
        echo "Alertmanager webhook channel is selected but ALERTMANAGER_WEBHOOK_URL is empty" >&2
        exit 1
    fi
    if looks_like_placeholder "$WEBHOOK_URL"; then
        echo "Alertmanager webhook channel is selected but ALERTMANAGER_WEBHOOK_URL is still a placeholder" >&2
        exit 1
    fi
fi

cat >"$TARGET_PATH" <<EOF
global:
  resolve_timeout: 5m

route:
  receiver: active-channel
  group_by: ["alertname"]
  group_wait: 15s
  group_interval: 2m
  repeat_interval: 4h

receivers:
  - name: active-channel
EOF

if [ "$CHANNEL" = "email" ]; then
    cat >>"$TARGET_PATH" <<EOF
    email_configs:
      - to: "${ALERTMANAGER_EMAIL_TO}"
        from: "${ALERTMANAGER_EMAIL_FROM}"
        smarthost: "${ALERTMANAGER_SMARTHOST}"
        auth_username: "${ALERTMANAGER_AUTH_USERNAME:-}"
        auth_password: "${ALERTMANAGER_AUTH_PASSWORD:-}"
        require_tls: true
EOF
else
    cat >>"$TARGET_PATH" <<EOF
    webhook_configs:
      - url: "${WEBHOOK_URL}"
        send_resolved: true
EOF
fi

# 保留模板挂载以便排查当前版本来源
if [ -f "$TEMPLATE_PATH" ]; then
    echo "# template-source: $TEMPLATE_PATH" >>"$TARGET_PATH"
fi
