# PLAN-20260425 MQTT 网关通讯协议

## 目标
- 为平台与工控机网关之间的 MQTT 应用层通讯建立当前联调契约。
- 明确 MQTT topic、既有遥测 payload、控制命令、控制回执、可靠性、安全和联调验收口径。
- 让后续真实设备或网关联调不再只依赖聊天记录、字段别名或模拟器口径。

## 背景结论
- 当前系统侧以 MQTT 入站消息作为设备接入边界。
- Modbus、串口、RS-485、HTTP 轮询等现场采集配置由工控机网关工程维护，不放入本平台 `config/`。
- 平台已有 MQTT worker、接入流水、失败重放、控制 topic、补偿控制器回执和字段别名兼容能力。
- 当前缺口不是“没有 MQTT”，而是缺少面向网关侧可执行的长期协议文档。

## 范围
- 新增长期规范：
  - `docs/guides/mqtt-gateway-protocol.md`
- 更新规范入口：
  - `docs/guides/README.md`
- 更新当前主题状态：
  - `docs/plans/current-status.md`
  - `docs/plans/handoff.md`
- Daily 归档：
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-status.md`
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-handoff.md`

## 非目标
- 不实现 RS-485 / Modbus / 串口主站。
- 不改 MQTT broker、用户名、现有 topic 环境变量或运行时兼容标识。
- 不修改后端 processor、publisher、worker 代码。
- 不新增前端页面。
- 不宣称真实设备或真实网关协议已经冻结。

## 契约原则
- 协议名称：`campus-mqtt.v1`。
- 控制协议名称：继续沿用现有 `campus-control.v1`。
- 当前状态：先对齐 2026-04-24 已跑通的 `CAP-001` 既有 payload；`campus-mqtt.v1` envelope 仅作为后续增强项。
- 设备身份优先使用 `device_code`，避免网关依赖平台数据库主键 `device_id`。
- 网关侧先按既有成功 payload 输出，平台保留少量历史别名兼容，但新接入不再扩张别名。
- 设备字段必须按公共遥测层、专属遥测层、参数快照层、控制与回执层分层归一。

## 主题 Topic
- 遥测入站：
  - `campus/telemetry`
  - `campus/device/{device_code}/telemetry`
- 控制下发：
  - `campus/control/{device_code}`
- 控制回执：
  - 当前约定回执仍走平台已订阅的遥测入站 topic，并通过 `message_type=control_receipt` 区分。
  - 如后续要新增专用回执 topic，必须单独立项修改 worker 订阅与验收测试。

## Payload 基线
- 所有网关 payload 必须是 UTF-8 JSON object。
- 当前遥测 payload 基线：
  - `device_code`
  - `timestamp`
  - 至少一个有效测点字段
  - 公共遥测、专属遥测和参数快照字段沿用 2026-04-24 已成功入库的 `CAP-001` 字段口径
- 新接入控制回执 payload 必填：
  - `message_type`
  - `device_code`
  - `timestamp`
  - `command_id`
  - `result`
- `protocol_version/message_id/gateway_id` 暂不作为近期必填项；后续用户需要时再补充。

## 验收标准
- `docs/guides/mqtt-gateway-protocol.md` 明确：
  - topic 规则
  - 当前既有 payload 基线
  - 遥测 payload
  - 控制命令 payload
  - 控制回执 payload
  - 字段分层与设备分类口径
  - 可靠性、安全和兼容策略
  - 联调检查清单
- `docs/guides/README.md` 已挂载新规范入口。
- `current-status.md` 与 `handoff.md` 已切换为本主题，不与能源合并主题混写。
- 文档验证通过：
  - `git diff --check -- docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/guides/README.md docs/plans/current-status.md docs/plans/handoff.md`
  - `! rg -n "TB[D]|TO[D]O|待[定]" docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/plans/current-status.md docs/plans/handoff.md`
  - `./venv/bin/python -m pytest tests/test_mqtt_contracts.py -q`

## 当前进展
- [x] 已确认本主题符合园区 EMS 主线：多能源接入、设备与表计接入、告警联动和实时监控。
- [x] 已确认本主题是协议类新主题，应使用正式 PLAN 承载。
- [x] 已明确平台边界：平台消费 MQTT 应用层报文，不维护现场采集网关清单。
- [x] 新增 MQTT 网关协议 guide。
- [x] 更新规范入口。
- [x] 切换 current-status 与 handoff。
- [x] 完成验证与 Daily 归档。
- [x] 回查 2026-04-24 数据库 MQTT 接入流水，确认既有 `CAP-001` 遥测 payload 基线。
- [x] 根据用户决策，将协议口径调整为先对齐既有报文，后续需要时再新增 envelope 字段。

## 剩余风险
- 真实网关尚未完成控制回执 UAT，当前不能宣称控制闭环冻结。
- 现有后端 parser 仍保留历史字段别名兼容，后续若要引入 `protocol_version/message_id/gateway_id`，必须另开后端实现轮。
- 当前控制回执继续复用遥测入站 topic；如现场网关要求独立回执 topic，需要新增订阅契约和代码变更。
- 2026-04-24 数据库中未发现 `control_receipt` payload，控制回执样例仍需通过真实网关或控制联调补齐。
