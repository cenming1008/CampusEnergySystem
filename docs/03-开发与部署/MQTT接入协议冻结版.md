# MQTT 接入协议冻结版

> 用于试点和正式交付阶段的统一接入约定。真实设备、网关程序、模拟器都应遵守本协议，避免现场出现“能发消息但系统不认”的问题。

---

## 1. Topic 规范

### 推荐正式主题

- 单设备遥测：`mine/device/{device_code}/telemetry`
- 平台订阅通配符：`mine/device/+/telemetry`
- 控制指令下发：`mine/device/{device_code}/control`

### 要求

- `device_code` 必须是现场唯一编码，建议与资产台账一致。
- 不允许一个物理设备在多个 topic 中轮换编码。
- 同一类采集消息不要混用多个 topic 结构。

---

## 2. Payload 字段清单

### 必填字段

- `device_id` 或 `device_code`
- `timestamp`
- 至少一个有效测点字段

### 推荐测点字段

- 电压：`voltage`
- 电流：`current`
- 功率：`power`
- 能耗：`energy_consumption`
- 功率因数：`power_factor`
- 频率：`frequency`
- 温度：`temperature`
- 压力：`pressure`
- 流量：`flow_rate`

### 示例

```json
{
  "device_code": "MINE-A-EM-001",
  "timestamp": "2026-03-26T10:30:00+08:00",
  "voltage": 380.5,
  "current": 41.2,
  "power": 23.8,
  "energy_consumption": 1289.4
}
```

---

## 3. 时间戳规则

- 推荐使用 ISO 8601 格式，例如 `2026-03-26T10:30:00+08:00`
- 必须带时区，禁止只传本地字符串如 `2026/03/26 10:30:00`
- 未来时间不得超过系统允许的漂移窗口
- 历史补传不得超过系统允许的陈旧数据窗口

当前默认窗口由以下配置控制：

- `MQTT_MAX_FUTURE_SECONDS`
- `MQTT_STALE_DATA_DAYS`

---

## 4. 设备唯一标识规则

- 正式现场以 `device_code` 作为跨系统唯一标识
- `device_id` 仅作为平台内部数据库主键使用
- 新设备接入前，应先在设备台账中登记 `device_code / 名称 / 类型 / 所属位置 / 负责人`
- 非正式环境允许自动创建设备；正式环境建议关闭自动创建并走台账审批

---

## 5. 重试与幂等

- 同一条采集消息重复投递时，平台应识别并防重
- 网关重试时不得随意改写原始业务时间戳
- 重试消息应保持相同业务含义，避免“同一时刻多份不同值”
- 失败补偿、重放、死信处理以平台运维记录为准

建议现场确认以下配置：

- `MQTT_RETRY_MAX_ATTEMPTS`
- `MQTT_RETRY_BACKOFF_SECONDS`

---

## 6. 上线前联调检查

- 设备编码与平台台账一致
- topic 与正式规范一致
- payload 至少包含一个有效测点
- 时间戳格式和时区正确
- 重复发送不会产生重复入库
- 断网重连后补发策略明确
- 异常值和空值处理策略明确

---

## 7. 变更规则

- 试点阶段冻结 topic 结构和关键字段命名
- 正式投产后如需改动，必须同步修改：
  - 平台解析逻辑
  - 设备/网关程序
  - 联调文档
  - 现场台账与运维手册
