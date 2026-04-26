# 2026-04-25 MQTT 网关通讯协议状态快照

## 当天目标
- 为平台与现场工控机网关之间的 MQTT 应用层通讯建立当前联调契约。
- 将当前主区从已完成的能源合并主题切换到 MQTT 网关通讯协议主题。

## 当天进展
- 已建立正式计划：`docs/plans/PLAN-20260425-mqtt-gateway-protocol.md`。
- 已新增长期规范：`docs/guides/mqtt-gateway-protocol.md`。
- 已在 `docs/guides/README.md` 挂载新规范入口。
- 已更新 `docs/plans/current-status.md` 与 `docs/plans/handoff.md`，主区只服务当前 MQTT 协议主题。
- 已明确平台边界：
  - 平台消费 MQTT 应用层 JSON 报文。
  - 工控机网关负责现场 Modbus、串口、RS-485、HTTP 轮询等采集与控制落地。
  - 当前协议为联调口径，真实设备 UAT 前不得宣称冻结。
- 已回查 2026-04-24 数据库 MQTT 接入流水：
  - `3792` 条 `campus/telemetry` 记录全部处理成功。
  - 设备为 `CAP-001` 电容补偿控制器。
  - 代表性 payload 已写入 `docs/guides/mqtt-gateway-protocol.md`。
  - 未发现 `control_receipt` 回执 payload。
- 已按用户决策调整协议口径：
  - 当前先对齐既有 `CAP-001` 报文。
  - `protocol_version`、`message_id`、`gateway_id` 等 envelope 字段后续需要时再添加。

## 当天验证
- `git diff --check -- docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/guides/README.md docs/plans/current-status.md docs/plans/handoff.md` 通过。
- `! rg -n "TB[D]|TO[D]O|待[定]" docs/plans/PLAN-20260425-mqtt-gateway-protocol.md docs/guides/mqtt-gateway-protocol.md docs/plans/current-status.md docs/plans/handoff.md` 通过，无占位符命中。
- `./venv/bin/python -m pytest tests/test_mqtt_contracts.py -q` 通过：`2 passed, 2 warnings`。

## 当天风险
- 当前只完成协议文档阶段，未修改后端 parser、worker 或 publisher 行为。
- 若后续要求强制校验 `protocol_version/message_id/gateway_id`，需要后端实现轮。
- 若现场网关要求独立回执 topic，需要更新 MQTT worker 订阅、测试和联调契约。
- 既有 `CAP-001` payload 缺少 envelope 字段；当前阶段不要求网关补齐，后续用户需要时再单独添加。
