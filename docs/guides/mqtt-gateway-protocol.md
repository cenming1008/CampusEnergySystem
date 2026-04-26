# MQTT 网关通讯协议

> 本文定义平台与现场工控机网关之间的 MQTT 应用层通讯契约。当前先对齐 2026-04-24 已跑通的 `CAP-001` 既有报文；`protocol_version`、`message_id`、`gateway_id` 等 envelope 字段作为后续增强项，等需要时再添加。

## 1. 定位与边界

本协议服务于园区综合能源管理系统的多能源接入、设备与表计监控、告警联动和控制回执闭环。

平台侧边界：

- 平台订阅 MQTT 入站消息，并完成设备解析、遥测归一、业务入库、告警检查、接入流水和 WebSocket 广播。
- 平台发布 MQTT 控制命令给工控机网关。
- 平台不在本仓库内维护 Modbus、串口、RS-485、HTTP 轮询等现场采集配置。

网关侧边界：

- 工控机网关负责现场协议主站、采集轮询、设备原始协议解析、控制命令落地和现场回执。
- 工控机网关必须把现场数据转换为本文约定的 MQTT topic 与 JSON payload。

## 2. 协议版本

| 场景 | 版本 |
| --- | --- |
| 遥测、参数快照 | 当前不强制版本字段 |
| 控制下发、控制回执 | `campus-control.v1` |
| 后续增强 envelope | `campus-mqtt.v1` |

版本策略：

- 当前联调优先保持网关已跑通的遥测 payload，不要求网关立即新增 `protocol_version`。
- 若后续新增心跳、网关追踪、跨版本兼容或强幂等，再引入 `campus-mqtt.v1` envelope。
- 新增不兼容字段、topic 或状态集时，必须单独立项说明兼容策略。

## 3. Topic 规则

### 3.1 遥测入站

平台当前订阅：

```text
campus/telemetry
campus/device/+/telemetry
```

推荐网关使用设备级 topic：

```text
campus/device/{device_code}/telemetry
```

兼容 topic：

```text
campus/telemetry
```

使用兼容 topic 时，payload 必须包含 `device_code`。

### 3.2 控制下发

平台发布：

```text
campus/control/{device_code}
```

`{device_code}` 对应平台设备档案中的 `sn` / `device_code`。网关不应依赖平台数据库主键 `device_id` 路由控制命令。

### 3.3 控制回执

当前控制回执约定仍走平台已订阅的入站 topic：

```text
campus/device/{device_code}/telemetry
```

或：

```text
campus/telemetry
```

回执通过 `message_type=control_receipt` 区分。若后续要增加专用回执 topic，例如 `campus/device/{device_code}/control-receipt`，必须同步修改平台 worker 订阅和验收测试。

## 4. Payload 基线

当前遥测入站先对齐既有 `CAP-001` payload。所有 payload 必须是 UTF-8 JSON object。

### 4.1 当前遥测必需字段

| 字段 | 必填 | 类型 | 说明 |
| --- | --- | --- | --- |
| `device_code` | 条件必填 | string | 设备编码；使用 `campus/telemetry` 时必填，设备级 topic 中也建议保留 |
| `timestamp` | 是 | string | ISO 8601 时间，建议带时区，例如 `2026-04-25T10:00:00+08:00` |
| 有效测点 | 是 | number / boolean / string | 至少包含一个公共遥测、专属遥测或参数快照字段 |

### 4.2 后续可选 envelope

以下字段当前不强制，等需要追踪网关、区分消息类型或增强幂等时再添加：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `protocol_version` | string | 建议值 `campus-mqtt.v1` |
| `message_type` | string | `telemetry`、`gateway_heartbeat` 等；控制回执仍建议使用 `control_receipt` |
| `message_id` | string | 网关生成的消息唯一 ID |
| `gateway_id` | string | 工控机网关唯一标识 |

兼容说明：

- 平台当前仍可从 `campus/device/{device_code}/telemetry` topic 提取 `device_code`。
- 平台当前仍兼容 `sn`、`device_sn`、`meter_code` 等历史设备编码别名。
- 当前新联调优先对齐既有 `CAP-001` 字段，不要求立即补 envelope。

## 5. 遥测 Payload

### 5.1 示例

```json
{
  "device_code": "METER-001",
  "timestamp": "2026-04-25T10:00:00+08:00",
  "device_category": "load",
  "device_subtype": "electric_meter",
  "energy_type": "electricity",
  "voltage": 380.2,
  "current": 12.1,
  "power": 7.9,
  "consumption": 12345.6,
  "power_factor": 0.96,
  "quality": "good"
}
```

### 5.2 公共遥测字段

| 字段 | 单位 | 说明 |
| --- | --- | --- |
| `consumption` | 按能源类型确定，电为 kWh | 累计用量或表读数 |
| `flow_rate` | 按能源类型确定 | 瞬时流量或等价负荷 |
| `power` | kW | 有功功率 |
| `voltage` | V | 电压 |
| `current` | A | 电流 |
| `power_factor` | 无量纲 | 功率因数 |
| `reactive_power` | kvar | 无功功率，允许负值 |
| `temperature` | degC | 温度 |
| `pressure` | MPa 或现场约定单位 | 压力 |
| `heat_flow` | GJ 或 kWh 热量等价 | 热量 |
| `heat_power` | kW | 热功率 |
| `cooling_power` | kW | 冷量功率 |
| `supply_temp` | degC | 供水或供能温度 |
| `return_temp` | degC | 回水或回能温度 |

遥测 payload 至少必须包含一个有效测点字段。字段值必须是可解析的有限数值，不得使用 `NaN`、`Infinity` 或带单位的字符串。

### 5.3 设备身份与分类

新设备接入时必须先说明：

- `device_category`
- `device_subtype`
- 公共层字段
- 专属遥测字段
- 参数快照字段
- 控制与回执字段

分类口径以 `docs/guides/device-data-classification.md` 为准。厂家型号、协议名、寄存器名不得直接作为 `device_category`。

## 6. 专属遥测与参数快照

公共遥测字段只能承接跨设备可复用语义。某类设备独有字段必须进入专属遥测或参数快照层。

### 6.1 补偿设备示例

```json
{
  "device_code": "CAP-001",
  "timestamp": "2026-04-25T10:01:00+08:00",
  "device_category": "compensation",
  "device_subtype": "capacitor_bank_controller",
  "energy_type": "electricity",
  "voltage_a": 220.1,
  "voltage_b": 219.8,
  "voltage_c": 221.0,
  "current_a": 18.2,
  "current_b": 17.9,
  "current_c": 18.4,
  "power_factor_a": 0.95,
  "power_factor_b": 0.96,
  "power_factor_c": 0.94,
  "reactive_power_a": 3.2,
  "reactive_power_b": 3.0,
  "reactive_power_c": 3.4,
  "circuit_state_reg_1": 255,
  "switch_on_power_factor": 95,
  "switch_off_power_factor": 102
}
```

平台会把可复用三相值归一到公共层，同时保留子型专属遥测和参数快照。网关侧不得把原始寄存器名直接扩散为公共业务字段。

## 7. 控制命令

### 7.1 平台下发示例

topic：

```text
campus/control/CAP-001
```

payload：

```json
{
  "message_type": "control_command",
  "protocol_version": "campus-control.v1",
  "timestamp": "2026-04-25T10:02:00+08:00",
  "device_id": 12,
  "device_code": "CAP-001",
  "command": "manual_switch",
  "command_id": "10086",
  "reason": "控制台手动投切",
  "manual_mode": "manual",
  "phase": "COMMON",
  "switch_action": "on",
  "protocol_function_code": "0x44",
  "manual_mode_code": 1,
  "phase_code": 3,
  "switch_action_code": 17
}
```

网关侧处理要求：

- 必须用 `command_id` 关联后续回执。
- 收到命令但尚未完成现场执行时，应先回 `running`。
- 现场执行完成后，必须回 `success`、`failed` 或 `rejected`。
- 网关不得把 MQTT publish 成功当成设备执行成功。

### 7.2 参数写入示例

```json
{
  "message_type": "control_command",
  "protocol_version": "campus-control.v1",
  "timestamp": "2026-04-25T10:03:00+08:00",
  "device_id": 12,
  "device_code": "CAP-001",
  "command": "write_parameter",
  "command_id": "10087",
  "parameter_key": "switch_on_power_factor",
  "target_value": 95,
  "register": "0xD2",
  "reason": "协议联调"
}
```

## 8. 控制回执

### 8.1 示例

```json
{
  "protocol_version": "campus-control.v1",
  "message_type": "control_receipt",
  "message_id": "gw-01-receipt-10087",
  "gateway_id": "gw-01",
  "device_code": "CAP-001",
  "timestamp": "2026-04-25T10:03:05+08:00",
  "command_id": "10087",
  "result": "success",
  "detail": "参数写入成功"
}
```

### 8.2 状态集

| result | 说明 |
| --- | --- |
| `running` | 网关已收到命令，现场设备正在执行 |
| `success` | 设备已确认执行成功 |
| `failed` | 设备执行失败或网关执行异常 |
| `timeout` | 网关或设备侧确认执行超时 |
| `rejected` | 网关拒绝执行，例如动作不支持、参数非法、设备离线 |

兼容别名：

- `refused`
- `unsupported`
- `not_supported`
- `not-supported`
- `invalid`
- `reject`

上述别名在平台侧按 `rejected` 处理。新网关应直接使用标准状态。

## 9. 心跳与接入健康

推荐网关每 30 秒上报一次心跳。

topic：

```text
campus/telemetry
```

payload：

```json
{
  "message_type": "gateway_heartbeat",
  "gateway_id": "gw-01",
  "timestamp": "2026-04-25T10:04:00+08:00",
  "status": "online",
  "device_count": 48,
  "software_version": "1.0.0"
}
```

当前平台以 MQTT worker 健康、设备接入记录和最近成功入库时间作为主要接入健康依据。若要正式落库网关心跳，需单独新增后端模型或 service。

## 10. 可靠性要求

- 遥测消息建议使用 QoS 1。
- 控制命令平台侧使用 QoS 1。
- 当前不要求网关生成 `message_id`；若后续需要精确排查重复和丢包，再追加该字段。
- 网关断线后应从现场缓存中补发关键遥测，但不得无限补发过旧数据。
- 时间戳必须使用设备采集时间；无法取得设备时间时使用网关接收时间，并在 `quality` 或扩展字段中标记。
- 平台会对重复、失败、死信和人工重放保留接入流水。

## 11. 安全要求

- 生产环境必须配置 MQTT 用户名和强密码。
- 生产部署不应把 MQTT broker 暴露到宿主机所有网卡。
- 现场部署如跨网络传输，应优先使用专线/VPN；如 broker 暴露到非可信网络，必须启用 TLS。
- 网关账号应限制到必要 topic 权限：
  - 发布遥测入站 topic。
  - 订阅自身控制 topic。
  - 不允许发布其他设备控制 topic。

## 12. 兼容与迁移

当前平台仍兼容部分历史字段：

| 历史字段 | 标准字段 |
| --- | --- |
| `sn` | `device_code` |
| `device_sn` | `device_code` |
| `meter_code` | `device_code` |
| `ts` | `timestamp` |
| `time` | `timestamp` |
| `collect_time` | `timestamp` |
| `kw` | `power` |
| `active_power` | `power` |
| `total_energy` | `energy` |
| `meter_reading` | `consumption` |
| `pf` | `power_factor` |
| `temp` | `temperature` |

对齐原则：

- 当前先按 2026-04-24 已跑通的 `CAP-001` payload 对齐。
- `protocol_version`、`message_id`、`gateway_id` 不作为近期必填项。
- 不再为单个厂家随意扩张全局别名；新增字段先按设备数据分类规范判断公共层或专属层。

### 12.1 既有联调报文基线

2026-04-24 数据库 `mqtt_ingestion_record` 中存在一批已成功处理的 `CAP-001` 联调遥测：

- 时间范围：`2026-04-24 18:27:43` 至 `2026-04-24 21:33:07`
- 记录数量：`3792`
- topic：`campus/telemetry`
- 状态：全部 `success`
- 设备：`device_id=12`，`device_code=CAP-001`
- 设备分类：`device_category=compensation`，`device_subtype=capacitor_bank_controller`，`energy_type=electricity`
- 控制回执：未发现 `message_type=control_receipt` 记录

该批 payload 已覆盖公共遥测、补偿控制器专属遥测和参数快照字段，但尚未包含 `protocol_version`、`message_type`、`message_id`、`gateway_id`。当前阶段以这类已跑通 payload 作为联调基线，暂不要求网关补齐 envelope。

代表性字段如下：

```json
{
  "device_code": "CAP-001",
  "timestamp": "2026-04-24T13:33:04+00:00",
  "voltage": 220.37,
  "current": 84.17,
  "power": 57.0,
  "power_factor": 0.9383,
  "reactive_power": 21.0,
  "voltage_a": 222.1,
  "voltage_b": 219.5,
  "voltage_c": 219.5,
  "current_a": 92.3,
  "current_b": 75.7,
  "current_c": 84.5,
  "power_factor_a": 0.932,
  "power_factor_b": 0.96,
  "power_factor_c": 0.922,
  "reactive_power_a": 9,
  "reactive_power_b": 5,
  "reactive_power_c": 7,
  "circuit_state_1": 3855,
  "circuit_state_2": 2047,
  "circuit_state_3": 3840,
  "common_output_circuit_count": 18,
  "split_output_circuit_count": 12,
  "switch_on_power_factor": 92,
  "switch_off_power_factor": 100
}
```

## 13. 联调检查清单

每接入一个真实网关或新设备子型，至少确认：

1. MQTT broker 地址、端口、账号、密码已配置。
2. 网关可以发布 `campus/device/{device_code}/telemetry`。
3. 平台可以在接入流水看到原始 payload。
4. `device_code` 能匹配或自动创建平台设备档案。
5. 遥测 payload 至少包含一个有效测点。
6. 时间戳未超前过多，也未超过平台允许的过旧范围。
7. 公共字段能进入通用遥测和监控页。
8. 专属字段能进入对应设备族的专属遥测或参数快照。
9. 控制命令能被网关订阅。
10. 控制回执能按 `command_id` 匹配平台控制日志。
11. `running/success/failed/timeout/rejected` 状态语义已现场确认。
12. 断线、重复消息、失败重放和迟到回执已验证。

## 14. 后续演进

- 若新增专用控制回执 topic，先更新本协议，再改 worker 订阅和测试。
- 若后续要求 `protocol_version/message_id/gateway_id`，需单独新增后端校验实现与失败原因。
- 若接入新设备类型，必须先完成 `device_category/device_subtype/字段分层/控制回执` 分类。
- 若目标升级为某厂商原始协议完整支持，需另开主题实现原始帧级协议栈，不混入 MQTT 应用层协议。
