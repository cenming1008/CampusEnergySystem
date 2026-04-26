# Handoff

## 当前主题
- 当前主主题：`MQTT 网关通讯协议`
- 当前执行依据：
  - /Users/todo/CampusEnergySystem/docs/plans/PLAN-20260425-mqtt-gateway-protocol.md

---

## 阶段结论
- 本轮已把“是否需要 MQTT 与工控机网关通讯协议”收敛为正式协议主题。
- 平台侧边界已锁定：
  - 平台消费 MQTT 应用层 JSON 报文。
  - 工控机网关负责现场 Modbus、串口、RS-485、HTTP 轮询等采集与控制落地。
  - 平台不维护现场网关采集清单。
- 已新增 `docs/guides/mqtt-gateway-protocol.md`，作为当前网关联调契约。
- 已回查 2026-04-24 数据库 MQTT 接入流水：
  - `3792` 条 `campus/telemetry` 记录全部处理成功。
  - 设备为 `CAP-001` 电容补偿控制器。
  - payload 已覆盖公共遥测、专属遥测和参数快照字段。
  - 未发现 `control_receipt` 回执 payload。
- 协议继续保留现有运行时 topic：
  - 遥测入站：`campus/telemetry`、`campus/device/{device_code}/telemetry`
  - 控制下发：`campus/control/{device_code}`
  - 控制回执：当前复用遥测入站 topic，通过 `message_type=control_receipt` 区分
- 协议已按用户决策调整：当前先对齐 2026-04-24 已跑通的 `CAP-001` 既有 payload，`protocol_version/message_id/gateway_id` 后续需要时再添加。

## 下一棒
- 下一棒交给验收角色：
  - 完成文档差异检查、占位符检查和 MQTT 契约单测。
  - 若验证通过，可判定本主题“文档阶段完成”。
- 后续若进入实现，交给后端角色：
  - 优先保证 2026-04-24 既有 `CAP-001` payload 继续可入库。
  - 如用户后续明确需要，再增加 `protocol_version/message_id/gateway_id`。
  - 若现场要求独立回执 topic，修改 MQTT worker 订阅与回执测试。
- 后续真实联调交给设备/网关联调角色：
  - 遥测 topic 与 payload 已可参考 2026-04-24 数据库样例。
  - 重点补齐真实控制回执样例，验证 `command_id` 关联和 `running/success/failed/timeout/rejected` 状态语义。

## 已验证
- `git diff --check -- docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/guides/README.md docs/plans/current-status.md docs/plans/handoff.md` 通过。
- `! rg -n "TB[D]|TO[D]O|待[定]" docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/plans/current-status.md docs/plans/handoff.md` 通过，无占位符命中。
- `./venv/bin/python -m pytest tests/test_mqtt_contracts.py -q` 通过：`2 passed, 2 warnings`。
- Daily 快照已归档：
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-status.md`
  - `docs/plans/daily/2026-04/2026-04-25-mqtt-gateway-protocol-handoff.md`

## 剩余风险
- 当前协议仍未经过完整真实设备 UAT，不得宣称控制闭环冻结。
- 当前文档不改变后端运行时行为，专用回执 topic 仍需后续实现主题。
- 若现场网关已有既定报文格式，需要按本文做字段映射表，不能直接把厂家寄存器名扩散为平台公共字段。
- 既有 `CAP-001` payload 缺少 `protocol_version/message_type/message_id/gateway_id`，当前不要求网关补齐；后续用户需要时再单独添加。
