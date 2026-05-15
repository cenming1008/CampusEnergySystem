# 设备监控统一模板契约

本文说明 `GET /devices/{id}/monitor/overview` 中统一模板字段的语义、覆盖矩阵和前端消费方式。模板只负责监控页展示契约，不承接 MQTT 解析、入库、告警判定或控制回执协议。

## 顶层字段

统一模板字段追加在现有 overview 顶层，旧字段继续保留：

- `monitor_template`：模板身份、设备族、专属面板声明。
- `metric_cards`：指标卡列表，前端按 `label/value/unit/precision/state` 展示。
- `trend_fields`：候选趋势字段。前端只渲染当前趋势接口已支持的字段。
- `control_summary`：远程控制能力摘要，不替代专属控制接口。
- `diagnostics_summary`：采集健康摘要，来源为 `runtime_status` 与 `ingestion_health`。
- `template_diagnostics`：接入诊断摘要，用于判断模板命中、指标覆盖、趋势可绘图能力、专属面板声明和采集健康状态。

状态约定：

- `state`：`live`、`mock`、`missing`。
- `source`：`realtime`、`telemetry`、`profile`、`control_log`、`missing`、`configured_fallback`。
- 空值指标仍可输出，前端以 `--` 展示。

前端趋势白名单：

- `flow_rate`
- `value`
- `voltage`
- `current`
- `reactive_power`
- `power_factor`
- `consumption`

模板可声明更多 `trend_fields`，但不在白名单内的字段第一版只作为指标卡或后续能力储备，不显示为趋势按钮。

## 接入诊断

`template_diagnostics` 由后端基于统一模板输出计算，不读取新的数据库表，也不改变 MQTT 入站协议。

字段语义：

- `template_key/display_name/category/subtype`：当前设备命中的模板身份。
- `metric_coverage`：核心指标覆盖情况，包含 `total/live/missing/missing_keys`。
- `trend_coverage`：趋势字段覆盖情况，包含模板声明字段、前端可绘图字段、暂不可绘图字段。
- `panel_coverage`：模板声明的专属面板列表。
- `ingestion_health`：复用 `diagnostics_summary`。
- `overall_status`：接入诊断结论。

状态判定：

- `passed`：设备在线，核心指标没有缺失，模板声明趋势字段都在当前前端白名单内。
- `partial`：设备在线，但存在缺失指标或暂不可绘图趋势字段。
- `missing`：设备在线，但核心指标全部缺失。
- `offline`：采集状态离线，优先级高于指标覆盖状态。

## 告警职责边界

监控页面遵循“页面不制造告警，页面只呈现告警”的边界。

- 设备运行类告警优先来自设备侧或控制器侧上报，包括设备自身故障、保护状态、异常状态、告警码、故障码、状态字、事件记录、投切结果和闭锁原因。
- 后端平台负责接收、解析、标准化、存储设备上报的事件与告警，并维护告警生命周期，包括发生、恢复、确认和处理记录。
- 后端平台可以补充平台级规则，但必须和设备原生告警区分来源；典型场景是通信中断、数据长时间未更新、平台接收异常等设备自身无法可靠上报的告警。
- 前端监控页负责展示当前状态、实时参数、趋势、设备上报告警、平台通讯类告警、事件和历史追溯，最多做轻量 UI 提示，不承担核心告警判定。

因此，设备运行类告警不得只在前端通过阈值或页面状态临时推导；如确需新增平台级补充规则，应先由后端或规则角色明确来源、生命周期和与设备原生告警的区分方式。

告警来源字段统一使用 `Alarm.source` 区分：

- `device_native`：设备或控制器原生上报的故障位、告警位、告警码、故障码或事件。
- `platform_rule`：平台基于已声明规则补充生成的告警，例如非补偿类设备通用电流 / 电压阈值、补偿控制器参数门限或过补偿推导。
- `platform_comm`：平台基于接入健康、心跳或最后成功数据时间生成的通讯类告警。

无功补偿设备不再默认执行通用电流 / 电压阈值告警；补偿设备的通用电压、电流、功率因数和无功功率仍可用于监控展示、趋势和运行语义提示，但不直接由前端转成告警实例。

平台通讯告警同时由接入健康读取路径和定时任务同步：读取单设备健康状态时可即时创建 / 恢复 `platform_comm/communication_offline`，默认 scheduler 也会每分钟扫描所有接入健康记录，避免只在打开页面时才发现离线。历史旧告警若仍使用 `source=telemetry`，前端按“历史遥测”展示，不做数据迁移。

## 模板覆盖矩阵

| 模板 key | 适用设备族 | 核心指标 | 趋势字段 | 专属面板 | 控制能力 |
| --- | --- | --- | --- | --- | --- |
| `generic_device` | 未命中特化模板的设备 | `flow_rate`、`consumption`、`voltage`、`current`、`pressure`、`temperature` | 同核心指标 | 无 | 不支持远程控制 |
| `water_meter` | 水表 | `flow_rate`、`consumption`、`pressure`、`temperature` | 同核心指标 | 无 | 不支持远程控制 |
| `gas_meter` | 气表 | `flow_rate`、`consumption`、`pressure` | 同核心指标 | 无 | 不支持远程控制 |
| `heat_meter` | 热量表 | `consumption`、`flow_rate`、`supply_temp`、`return_temp`、`temperature_delta`、`pressure` | `consumption`、`flow_rate` | 无 | 不支持远程控制 |
| `cooling_meter` | 冷量表 | `consumption`、`flow_rate`、`supply_temp`、`return_temp`、`temperature_delta`、`pressure` | `consumption`、`flow_rate` | 无 | 不支持远程控制 |
| `capacitor_bank_controller` | 电容补偿控制器 | `reactive_power`、`power_factor`、`voltage`、`current`、`running_circuit_count`、`capacity_utilization` | `reactive_power`、`power_factor`、`voltage`、`current` | `three_phase`、`circuit_state`、`harmonic_spectrum`、`control_profile`、`control_summary` | 支持远程控制，要求回执 |
| `svg` | SVG 无功补偿装置 | `reactive_power`、`power_factor`、`capacity_utilization`、`cabinet_temperature`、`module_count` | `reactive_power`、`power_factor`、`voltage`、`current` | `three_phase`、`module_status`、`device_profile` | 不支持远程控制 |
| `storage` | 储能设备 | `soc`、`soh`、`active_power`、`run_state`、`cell_temp_max`、`charge_energy_today`、`discharge_energy_today` | `flow_rate`、`voltage`、`current`、`temperature` | `storage_realtime`、`storage_trend`、`storage_status` | 不支持远程控制 |

## 前端消费

- 通用设备路径优先消费 `metric_cards`、`trend_fields`、`diagnostics_summary`。
- 补偿控制器和储能路径继续使用专属组件，统一模板字段作为契约依据和后续迁移基础。
- `DeviceMonitor.vue` 只作为页面入口，负责路由态加载与三类视图分发。
- 普通、补偿、储能三类页面主体分别由 `GenericMonitorView.vue`、`CompensationMonitorView.vue`、`StorageMonitorView.vue` 承载。
- 页面级 overview、trend、alarms、controlLogs、statusHistory、loading、polling 和刷新入口统一收口在 `useDeviceMonitorPage`。
- `DeviceMetricGrid` 支持空指标、缺值、长标签、空单位。
- `DeviceTrendPanel` 只展示白名单内字段；没有可展示字段时显示空态。
- `DeviceDiagnosticsSummary` 在缺少 `runtime_status` 或 `diagnostics_summary` 时显示安全默认值。
- `DeviceTemplateDiagnosticsPanel` 展示 `template_diagnostics`，用于接入验收和现场联调排查。
- 电容补偿控制器使用两个独立谐波视图：`谐波趋势` tab 只展示三相电压 THD 与三相谐波电流历史趋势；`高次谐波` tab 只展示最新采样的 2~31 次谐波柱状谱图。未上报逐次谱线时，`高次谐波` tab 显示空态，不影响既有 THD 趋势。

## 新增设备判断

新增设备时按下面顺序判断：

1. 如果只是字段名字不同，本质仍是流量、累计读数、电压、电流、压力、温度等公共指标，应在接入解析层映射到公共字段，并复用现有模板或新增一个设备族模板。
2. 如果是一类设备共享新的第一屏指标，但没有特殊结构，新增一个 `MonitorTemplateSpec`，不新增前端专属页面。
3. 如果设备存在专属结构，例如补偿回路、三相状态、储能 SOC/充放电状态、组串状态，应保留统一模板，同时新增专属 monitor payload 和专属组件。
4. 不为单台设备写页面或插件；只为稳定设备族新增模板或专属面板。

## 后端插件注册

设备监控后端采用代码内插件注册，不支持运行时上传或热插拔插件。

- 统一 overview 入口仍是 `/devices/{id}/monitor/overview`。
- `DeviceMonitorPluginRegistry` 负责按 `device_subtype -> device_category -> device_type/历史别名 -> generic_device` 选择插件。
- `DeviceMonitorService.get_monitor_overview()` 负责构建内部 `DeviceMonitorContext`，包含 `session/device/realtime/runtime_status/ingestion_health`。
- `DeviceMonitorPlugin.build_monitor_payload()` 接收 `DeviceMonitorContext`，插件不再从多个位置接收分散入参。
- 插件负责生成本设备族的专属 monitor payload、模板 spec、指标卡和控制摘要。
- `compensation_monitor`、`storage_monitor` 继续作为对前端兼容的顶层字段保留。
- 普通表计优先使用轻量模板插件；只有存在专属遥测表、参数快照或控制链时才新增专属 service。

## overview 样例

以下样例展示 overview 中统一模板字段。`archive`、`runtime_status`、`realtime`、`recent_alarms` 等既有字段仍按现有接口返回。

### water_meter

```json
{
  "monitor_template": {
    "template_key": "water_meter",
    "category": "water_meter",
    "subtype": null,
    "display_name": "水表",
    "specific_panels": []
  },
  "metric_cards": [
    { "key": "flow_rate", "label": "瞬时流量", "value": 2.2, "unit": "m³/h", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "consumption", "label": "累计读数", "value": 12.5, "unit": "m³", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "pressure", "label": "压力", "value": 0.33, "unit": "MPa", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "temperature", "label": "温度", "value": 21.5, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" }
  ],
  "trend_fields": [
    { "key": "flow_rate", "label": "瞬时流量", "unit": "m³/h", "precision": 2 },
    { "key": "consumption", "label": "累计读数", "unit": "m³", "precision": 2 },
    { "key": "pressure", "label": "压力", "unit": "MPa", "precision": 2 },
    { "key": "temperature", "label": "温度", "unit": "degC", "precision": 1 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": {
    "ingestion_status": "online",
    "is_online": true,
    "last_message_at": "2026-04-25T10:00:00+08:00",
    "last_success_at": "2026-04-25T10:00:00+08:00"
  }
}
```

### gas_meter

```json
{
  "monitor_template": { "template_key": "gas_meter", "category": "gas_meter", "subtype": null, "display_name": "燃气表", "specific_panels": [] },
  "metric_cards": [
    { "key": "flow_rate", "label": "瞬时流量", "value": 6.8, "unit": "m³/h", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "consumption", "label": "累计读数", "value": 401.2, "unit": "m³", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "pressure", "label": "压力", "value": 2.4, "unit": "kPa", "precision": 2, "source": "realtime", "state": "live" }
  ],
  "trend_fields": [
    { "key": "flow_rate", "label": "瞬时流量", "unit": "m³/h", "precision": 2 },
    { "key": "consumption", "label": "累计读数", "unit": "m³", "precision": 2 },
    { "key": "pressure", "label": "压力", "unit": "kPa", "precision": 2 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

### heat_meter

```json
{
  "monitor_template": { "template_key": "heat_meter", "category": "heat_meter", "subtype": null, "display_name": "热量表", "specific_panels": [] },
  "metric_cards": [
    { "key": "consumption", "label": "累计热量", "value": 128.4, "unit": "GJ", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "flow_rate", "label": "瞬时热功率", "value": 52.6, "unit": "kW", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "supply_temp", "label": "供水温度", "value": 60.2, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "return_temp", "label": "回水温度", "value": 47.7, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "temperature_delta", "label": "供回水温差", "value": 12.5, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "pressure", "label": "压力", "value": 0.41, "unit": "MPa", "precision": 2, "source": "realtime", "state": "live" }
  ],
  "trend_fields": [
    { "key": "consumption", "label": "累计热量", "unit": "GJ", "precision": 2 },
    { "key": "flow_rate", "label": "瞬时热功率", "unit": "kW", "precision": 2 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

### cooling_meter

```json
{
  "monitor_template": { "template_key": "cooling_meter", "category": "cooling_meter", "subtype": null, "display_name": "冷量表", "specific_panels": [] },
  "metric_cards": [
    { "key": "consumption", "label": "累计冷量", "value": 96.7, "unit": "GJ", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "flow_rate", "label": "瞬时冷功率", "value": 44.3, "unit": "kW", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "supply_temp", "label": "供水温度", "value": 7.1, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "return_temp", "label": "回水温度", "value": 12.6, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "temperature_delta", "label": "供回水温差", "value": 5.5, "unit": "degC", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "pressure", "label": "压力", "value": 0.37, "unit": "MPa", "precision": 2, "source": "realtime", "state": "live" }
  ],
  "trend_fields": [
    { "key": "consumption", "label": "累计冷量", "unit": "GJ", "precision": 2 },
    { "key": "flow_rate", "label": "瞬时冷功率", "unit": "kW", "precision": 2 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

### storage

```json
{
  "monitor_template": { "template_key": "storage", "category": "storage", "subtype": null, "display_name": "储能设备", "specific_panels": ["storage_realtime", "storage_trend", "storage_status"] },
  "metric_cards": [
    { "key": "soc", "label": "SOC", "value": 76.5, "unit": "%", "precision": 1, "source": "telemetry", "state": "live" },
    { "key": "soh", "label": "SOH", "value": 98.1, "unit": "%", "precision": 1, "source": "telemetry", "state": "live" },
    { "key": "active_power", "label": "有功功率", "value": -18.2, "unit": "kW", "precision": 2, "source": "telemetry", "state": "live" },
    { "key": "run_state", "label": "运行状态", "value": "放电中", "unit": null, "precision": 0, "source": "telemetry", "state": "live" },
    { "key": "cell_temp_max", "label": "最高温度", "value": 36.7, "unit": "degC", "precision": 1, "source": "telemetry", "state": "live" },
    { "key": "charge_energy_today", "label": "今日充电量", "value": 42.0, "unit": "kWh", "precision": 2, "source": "telemetry", "state": "live" },
    { "key": "discharge_energy_today", "label": "今日放电量", "value": 38.5, "unit": "kWh", "precision": 2, "source": "telemetry", "state": "live" }
  ],
  "trend_fields": [
    { "key": "flow_rate", "label": "功率", "unit": "kW", "precision": 2 },
    { "key": "voltage", "label": "电压", "unit": "V", "precision": 1 },
    { "key": "current", "label": "电流", "unit": "A", "precision": 1 },
    { "key": "temperature", "label": "温度", "unit": "degC", "precision": 1 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

### svg

```json
{
  "monitor_template": { "template_key": "svg", "category": "compensation", "subtype": "svg", "display_name": "SVG 无功补偿装置", "specific_panels": ["three_phase", "module_status", "device_profile"] },
  "metric_cards": [
    { "key": "reactive_power", "label": "无功功率", "value": 42.0, "unit": "kvar", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "power_factor", "label": "功率因数", "value": 0.99, "unit": null, "precision": 3, "source": "realtime", "state": "live" },
    { "key": "capacity_utilization", "label": "容量利用率", "value": 64.5, "unit": "%", "precision": 1, "source": "telemetry", "state": "live" },
    { "key": "cabinet_temperature", "label": "柜内温度", "value": 35.6, "unit": "degC", "precision": 1, "source": "telemetry", "state": "live" },
    { "key": "module_count", "label": "模块数", "value": 8, "unit": "个", "precision": 0, "source": "profile", "state": "live" }
  ],
  "trend_fields": [
    { "key": "reactive_power", "label": "无功功率", "unit": "kvar", "precision": 2 },
    { "key": "power_factor", "label": "功率因数", "unit": null, "precision": 3 },
    { "key": "voltage", "label": "电压", "unit": "V", "precision": 1 },
    { "key": "current", "label": "电流", "unit": "A", "precision": 1 }
  ],
  "control_summary": { "supports_remote_control": false, "receipt_required": false, "supported_commands": [] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

### capacitor_bank_controller

```json
{
  "monitor_template": { "template_key": "capacitor_bank_controller", "category": "compensation", "subtype": "capacitor_bank_controller", "display_name": "电容补偿控制器", "specific_panels": ["three_phase", "circuit_state", "harmonic_spectrum", "control_profile", "control_summary"] },
  "metric_cards": [
    { "key": "reactive_power", "label": "无功功率", "value": -32.0, "unit": "kvar", "precision": 2, "source": "realtime", "state": "live" },
    { "key": "power_factor", "label": "功率因数", "value": 0.95, "unit": null, "precision": 3, "source": "realtime", "state": "live" },
    { "key": "voltage", "label": "电压", "value": 389.0, "unit": "V", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "current", "label": "电流", "value": 43.0, "unit": "A", "precision": 1, "source": "realtime", "state": "live" },
    { "key": "running_circuit_count", "label": "投入回路", "value": 6, "unit": "路", "precision": 0, "source": "telemetry", "state": "live" },
    { "key": "capacity_utilization", "label": "容量利用率", "value": 25.0, "unit": "%", "precision": 1, "source": "telemetry", "state": "live" }
  ],
  "trend_fields": [
    { "key": "reactive_power", "label": "无功功率", "unit": "kvar", "precision": 2 },
    { "key": "power_factor", "label": "功率因数", "unit": null, "precision": 3 },
    { "key": "voltage", "label": "电压", "unit": "V", "precision": 1 },
    { "key": "current", "label": "电流", "unit": "A", "precision": 1 }
  ],
  "control_summary": { "supports_remote_control": true, "receipt_required": true, "supported_commands": ["manual_switch", "switch_control_mode", "reset_alarm", "write_parameter"] },
  "diagnostics_summary": { "ingestion_status": "online", "is_online": true, "last_message_at": "2026-04-25T10:00:00+08:00", "last_success_at": "2026-04-25T10:00:00+08:00" }
}
```

## 真实联调校准项

- 冷热量表第一屏使用公共层 `supply_temp`、`return_temp` 和派生 `temperature_delta` 展示供回水温与温差；`temperature_delta = abs(supply_temp - return_temp)`。
- 热 / 冷累计量单位当前采用 `GJ`，瞬时热 / 冷功率单位采用 `kW`；现场协议若上报 `kWh`、`MWh` 或厂商自定义单位，需要在设备接入层统一换算。
- 储能的 `active_power` 正负方向已由专属组件解释，统一指标卡仅展示数值和单位。
- SVG 的 `module_count` 来源使用资产 profile；没有 profile 时通过 `template_diagnostics.metric_coverage.missing_keys` 暴露为缺失。
- 电容补偿控制器逐次谐波联调用 `scripts/python/send_capacitor_bank_harmonic_uat_payloads.py` 生成准真实 payload；验收时重点确认 `谐波趋势` tab 仍只显示 THD / 谐波电流历史趋势，`高次谐波` tab 可切换电压 / 电流与 A/B/C 相，A 相 5 次超限标红，B 相电流缺谱线只显示空态。
