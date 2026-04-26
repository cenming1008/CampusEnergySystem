# Current Status

## 当前总目标
- 当前主主题：`MQTT 网关通讯协议`
- 当前总目标：为平台与现场工控机网关之间的 MQTT 应用层通讯建立当前联调契约，先对齐已跑通的 `CAP-001` 既有报文，支撑设备接入、控制下发与回执闭环。
- 当前执行依据：
  - /Users/todo/CampusEnergySystem/docs/plans/PLAN-20260425-mqtt-gateway-protocol.md

---

## 当前阶段
- [x] 规则角色已确认本主题符合园区 EMS 主线：多能源接入、设备与表计监控、告警联动和实时监控。
- [x] 预判角色已确认平台边界：本系统消费 MQTT 应用层报文，不维护现场 Modbus、串口、RS-485 或 HTTP 轮询采集配置。
- [x] 已建立正式计划：`PLAN-20260425-mqtt-gateway-protocol.md`。
- [x] 已新增长期规范：`docs/guides/mqtt-gateway-protocol.md`。
- [x] 已在 `docs/guides/README.md` 挂载规范入口。
- [x] 执行文档差异检查、占位符检查和 MQTT 契约单测。
- [x] 将本轮状态与交接归档到 `docs/plans/daily/2026-04/`。
- [x] 已回查 2026-04-24 数据库 MQTT 接入流水：`3792` 条 `campus/telemetry` 成功记录，均为 `CAP-001` 电容补偿控制器遥测。
- [x] 已按用户决策调整协议口径：当前先对齐既有报文，`protocol_version/message_id/gateway_id` 后续需要时再添加。

## 当前阻塞
- 当前无代码阻塞。

## 当前待办
- [ ] 等待真实工控机网关控制回执样例，或发起一次控制联调生成 `control_receipt` payload。
- [ ] 决定是否进入控制回执联调、专用回执 topic 或新设备子型接入实现轮。

## 当前验证结论
- `git diff --check -- docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/guides/README.md docs/plans/current-status.md docs/plans/handoff.md` 通过。
- `! rg -n "TB[D]|TO[D]O|待[定]" docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/plans/current-status.md docs/plans/handoff.md` 通过，无占位符命中。
- `./venv/bin/python -m pytest tests/test_mqtt_contracts.py -q` 通过：`2 passed, 2 warnings`。
- Daily 快照已归档：
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-status.md`
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-handoff.md`
- 数据库回查结果：
  - 2026-04-24 `mqtt_ingestion_record` 共 `3792` 条记录。
  - 全部记录 topic 为 `campus/telemetry`，status 为 `success`。
  - 设备为 `device_id=12 / CAP-001 / capacitor_bank_controller / compensation / electricity`。
  - 代表性 payload 已写入 `docs/guides/mqtt-gateway-protocol.md` 的“既有联调报文基线”。
  - 未发现 `control_receipt` payload。

## 当前验收判断
- 当前可判定：本主题文档阶段完成。
- `mqtt-gateway-protocol.md` 可作为真实网关联调基线，近期不强制 envelope。
- 本主题暂不进入代码实现；后续控制回执联调、专用回执 topic 或新设备子型接入需另开实现轮。

## 当前剩余风险
- 当前协议为联调口径，还不能替代真实设备/真实网关 UAT。
- 现有后端 parser 仍保留历史字段别名兼容；若后续需要引入 `protocol_version/message_id/gateway_id`，必须另开后端实现轮。
- 当前控制回执继续复用遥测入站 topic；若现场网关要求独立回执 topic，需要新增 worker 订阅和测试。
- 2026-04-24 既有遥测 payload 未包含 `protocol_version/message_type/message_id/gateway_id`，当前阶段按既有 payload 对齐，不要求网关立即补齐 envelope。
