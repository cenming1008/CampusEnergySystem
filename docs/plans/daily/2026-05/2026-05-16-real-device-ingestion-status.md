# 2026-05-16 Real Device Ingestion Status

## 当前目标
- 更新现场真实设备接入时使用的系统 IP 地址和端口。
- 确认真实设备数据是否已经进入平台侧 MQTT 接入流水。

## 状态快照
- 当前系统局域网地址：`192.168.1.46`。
- MQTT dev 明文入口：`192.168.1.46:1883`。
- MQTT TLS 入口：`192.168.1.46:8883`。
- 后端 API / 健康检查入口：`http://192.168.1.46:8088`。
- 当前 `.env` 中 `MQTT_BROKER=localhost` 是平台 worker 连接本机 broker 的内部配置，现场设备 / 网关不应使用该值，应使用局域网地址连接 broker。

## 验证结果
- `ifconfig en0` 显示 `inet 192.168.1.46`。
- `lsof -nP -iTCP -sTCP:LISTEN` 显示 MQTT `*:1883`、`*:8883` 与后端 `*:8088` 正在监听。
- `docker ps --format '{{.Names}} {{.Ports}}'` 显示 `campusenergysystem-mqtt-1` 已映射 `0.0.0.0:1883->1883/tcp` 和 `0.0.0.0:8883->8883/tcp`。
- `GET /health` 返回 `database`、`redis`、`mqtt_bridge`、`mqtt_worker`、`api_realtime`、`scheduler` 均为 `healthy`。
- MQTT 接入流水最近记录显示 `CAP-001` 发布到 `campus/device/CAP-001/telemetry`，处理状态 `success`，最近 `received_at=2026-05-15T21:17:55.785974`。

## 剩余风险
- `192.168.1.46` 是当前 DHCP / 局域网地址；现场网络变化后需要更新网关侧 broker 地址。
- 当前核验只确认真实数据进入平台，不替代字段语义、单位换算、专属遥测覆盖和控制回执验收。
