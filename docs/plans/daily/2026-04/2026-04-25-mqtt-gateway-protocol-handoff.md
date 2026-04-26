# 2026-04-25 MQTT 网关通讯协议交接快照

## 当天仍需交接的动作
- 交给设备/网关联调角色：
  - 遥测入站可先参考 2026-04-24 数据库中的 `CAP-001` 样例：topic 为 `campus/telemetry`，payload 已覆盖公共遥测、专属遥测和参数快照字段。
  - 验证 `campus/control/{device_code}` 控制下发是否能被网关订阅。
  - 验证 `message_type=control_receipt` 回执能按 `command_id` 匹配平台控制日志。
  - 核对 `running/success/failed/timeout/rejected` 状态语义是否与现场执行一致。
- 如进入后端实现轮，交给后端角色：
  - 增加可选或强制的 `protocol_version/message_id/gateway_id` 校验。
  - 若需要独立回执 topic，修改 MQTT worker 订阅与回执测试。
  - 按新协议补充标准 payload 示例测试。

## 当天限制条件
- 当前协议为联调口径，不能替代真实设备 UAT。
- 平台侧仍不维护现场 Modbus、串口、RS-485 或 HTTP 轮询采集配置。
- 旧字段别名只保留兼容，不作为新网关模板继续扩张。
- 既有 `CAP-001` payload 缺少 `protocol_version/message_type/message_id/gateway_id`，当前不要求网关补齐，后端实现时不得直接强切既有报文。

## 当天未解决风险
- 真实网关是否接受“控制回执复用遥测入站 topic”仍需现场确认。
- 数据库中尚未发现 `control_receipt` payload，控制回执样例仍需通过真实控制联调补齐。
- 现场网关若已有既定 payload，需要补充字段映射表，并按设备数据分类规范判断公共层和专属层。
- 当前文档不会改变平台运行时对既有 payload 的兼容行为。
