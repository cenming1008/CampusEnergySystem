# 2026-05-16 Real Device Ingestion Handoff

## 交接对象
- 后端 / 设备接入角色
- 验收角色

## 现场入口
- MQTT dev 明文：`192.168.1.46:1883`
- MQTT TLS：`192.168.1.46:8883`
- 后端 API / 健康检查：`http://192.168.1.46:8088`

## 已确认事实
- MQTT broker 已对局域网监听 `1883` 和 `8883`。
- 后端 API 已监听 `8088`。
- `mqtt_worker` 当前为 `healthy`。
- 真实设备数据已进入平台接入流水，最新可见记录为 `CAP-001` / `campus/device/CAP-001/telemetry` / `success`。

## 下一步建议
- 现场网关继续按 `campus/device/{device_code}/telemetry` 发布遥测。
- 若改 TLS 接入，需要给现场网关配置 CA，并切换到 `192.168.1.46:8883`。
- 用诊断面板和接入流水继续核对字段缺失、单位换算和专属遥测覆盖。
- 若现场网络重新分配 IP，应同步更新网关配置和 `docs/guides/mqtt-gateway-protocol.md` 的现场入口。
