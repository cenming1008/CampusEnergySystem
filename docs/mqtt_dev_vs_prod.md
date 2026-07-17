# MQTT 接入模式：dev（明文）↔ prod（TLS）

broker 同时监听两个端口：
- `1883` 明文 —— dev 默认
- `8883` TLS  —— prod 默认

ACL（`mosquitto/config/acl`）+ 一设备一密钥（`mosquitto/config/passwd`）对**两个端口都生效**，所以即便走 1883，仍然有：
- cap-001 只能写 `campus/device/CAP-001/telemetry`，伪造其他设备会被丢弃
- sto-001 只能写 `campus/device/STO-001/telemetry`，并读取本设备控制与仿真控制 topic
- control-publisher 才能下发 `campus/control/+`
- ingest-worker 只读不可写

## 切换方法

只动 `.env`，broker 配置和应用代码不动。

### dev（明文）
```env
MQTT_PORT=1883
MQTT_TLS_ENABLED=False
```
模拟器侧只用账号密码连 1883。

### prod（TLS）
```env
MQTT_PORT=8883
MQTT_TLS_ENABLED=True
MQTT_TLS_CA_PATH=/etc/ssl/mqtt/ca.crt
MQTT_TLS_INSECURE=False
```
- 把 `mosquitto/config/certs/ca.crt` 部署到 prod 主机
- 所有设备客户端都要拿到 ca.crt
- 上线前重签 server.crt，SAN 加入 prod 的域名/IP（参见 `scripts/shell/gen_dev_mqtt_certs.sh`，支持 `MQTT_CERT_EXTRA_SANS` 环境变量）

## 端口暴露

`docker-compose.dev.yml` 同时映射 `1883:1883` 与 `8883:8883`。prod 部署文件 (`docker-compose.prod.yml`) 上线时**只**保留 `8883:8883`。

## 凭据轮换

```bash
bash scripts/shell/gen_dev_mqtt_certs.sh --force-passwd
```
会重新生成四个账号的随机密码，写入 `.env.local.mqtt`，包括 `MQTT_STORAGE_USERNAME=sto-001` 与独立密码；需手动合并进 `.env`。`--force` 只重签 server.crt（CA 与 passwd 都保留）。

## 验证

CAP-001 可使用 `scripts/python/dev_simulate_cap001.py` 验证。储能使用 `storage_simulator.py`，它优先读取 `MQTT_STORAGE_USERNAME` / `MQTT_STORAGE_PASSWORD`，根据 `MQTT_TLS_ENABLED` 走明文或 TLS；入站采集需单独运行 `scripts/python/run_mqtt_ingest_worker.py`。
