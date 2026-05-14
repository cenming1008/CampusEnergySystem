# Handoff

## 当前主题
- 当前主主题：`设备监控统一模板 V4 后续结构收敛`
- 当前执行依据：
  - 用户提供的《设备监控模块下一阶段收敛计划》

---

## 阶段结论
- 后端 `GET /devices/{id}/monitor/overview` 已增量返回 `template_diagnostics`。
- 诊断字段包含：
  - 模板身份：`template_key/display_name/category/subtype`
  - 指标覆盖：`total/live/missing/missing_keys`
  - 趋势覆盖：`declared_keys/drawable_keys/unsupported_keys`
  - 专属面板：`specific_panels`
  - 采集健康：复用 `diagnostics_summary`
  - 总体状态：`passed/partial/missing/offline`
- 前端已新增 `DeviceTemplateDiagnosticsPanel`，并在通用、补偿、储能监控路径挂载。
- 契约文档已更新 `template_diagnostics` 字段说明、状态判定和新增设备判断规则。
- 后端已新增 `DeviceMonitorPluginRegistry`，统一按 `device_subtype -> device_category -> device_type/历史别名 -> generic_device` 选择监控插件。
- 补偿、储能、普通表计和通用设备已接入代码内插件注册；`compensation_monitor`、`storage_monitor` 和现有 `/monitor/*` endpoint 保持兼容。
- 前端 `DeviceMonitor.vue` 已拆薄为页面入口，三类页面主体分别下沉到：
  - `frontend/src/features/device-monitor/views/GenericMonitorView.vue`
  - `frontend/src/features/device-monitor/views/CompensationMonitorView.vue`
  - `frontend/src/features/device-monitor/views/StorageMonitorView.vue`
- 页面级状态、副作用、轮询和刷新入口已收口到 `frontend/src/features/device-monitor/composables/useDeviceMonitorPage.ts`。
- 后端插件 payload 构建已改为内部 `DeviceMonitorContext` 入参，context 包含 `session/device/realtime/runtime_status/ingestion_health`。
- `DeviceMonitorService.get_monitor_overview()` 仍是 overview 编排入口，负责构建 context、调用 registry 命中插件，并保持 `compensation_monitor`、`storage_monitor`、`monitor_template`、`metric_cards`、`template_diagnostics` 返回兼容。
- 准真实 payload 校准已覆盖热量表、冷量表、SVG、储能：
  - 热 / 冷量表监控实时 payload 已包含 `supply_temp`、`return_temp`、`heat_flow`、派生 `temperature_delta`。
  - 热 / 冷量表第一屏指标已展示供水温度、回水温度、供回水温差、压力、累计量和瞬时功率。
  - SVG 缺少资产 profile 时，`module_count` 会进入 `template_diagnostics.metric_coverage.missing_keys`。
  - 储能缺少 `soh/cell_temp_max/charge_energy_today/discharge_energy_today` 时，诊断会暴露对应 `missing_keys`。
- 告警边界已按三类来源实现：
  - `device_native`：设备 / 控制器原生故障位、告警位、告警码、故障码或事件。
  - `platform_rule`：平台声明的补充规则，例如普通设备通用电流 / 电压阈值、补偿控制器参数门限或过补偿推导。
  - `platform_comm`：平台基于接入健康生成的通讯类告警。
- 补偿设备不再默认套用通用 `current_overload` / `voltage_out_of_range` 阈值告警。
- 接入健康会创建 / 恢复 `platform_comm/communication_offline` 告警；恢复写入 `recovered_at`，不自动设置 `is_resolved`。
- 告警中心与补偿监控告警表已展示来源标签。
- 默认 scheduler 每分钟执行 `sync_platform_comm_alarms` 全量扫描接入健康记录，避免通讯告警只在页面读取时才同步。
- 旧 `source=telemetry` 告警在前端显示为“历史遥测”，本轮不迁移历史数据。

## 下一棒
- 验收角色：
  - 复核四种状态判定是否符合接入验收预期；当前准真实测试已覆盖 `passed/partial/missing/offline`。
  - 打开普通表计、补偿设备、储能设备监控页，确认诊断面板不影响既有专属页面。
- 后端/设备接入角色：
  - 用真实 payload 继续复核冷热表单位是否已换算到模板口径：累计热 / 冷量 `GJ`，瞬时热 / 冷功率 `kW`，温度 `degC`。
  - 关注诊断面板暴露出的缺失字段，优先判断是 MQTT 映射问题还是模板定义问题。
  - 新增专属设备时优先新增监控插件；普通表计优先补轻量模板，不回到 `DeviceMonitorService` 手写分流。
- 前端角色：
  - 新增设备专属页面时优先新增或复用 `features/device-monitor/views/*MonitorView.vue` 视图容器，不把大段 template 重新堆回 `DeviceMonitor.vue`。
  - 新增页面级请求、轮询或刷新副作用时优先进入 `useDeviceMonitorPage` 或进一步拆出稳定 composable。
  - 后续如需要，可把诊断面板扩展为接入验收 checklist 或独立报告。
  - 告警相关 UI 只展示 `Alarm.source/category/message` 等后端返回语义，不在页面根据实时值制造核心告警。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`34 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_service.py tests/test_alarm_endpoints.py tests/test_device_monitor_service.py tests/test_ingestion_health_service.py -q` 通过：`46 passed, 1 warning`。
- `cd frontend && npm run test:unit -- sourceLabels.test.ts DeviceMonitor.test.ts` 通过：`2 files / 13 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_scheduler_jobs.py tests/test_ingestion_health_service.py -q` 通过：`11 passed, 1 warning`。

## 剩余风险
- 当前诊断结果基于模板输出和当前健康字段，不替代真实设备 UAT。
- 暂不可绘图字段只做展示，不在本轮扩展趋势接口。
- 专属面板声明不在本轮驱动布局。
- `useDeviceMonitorPage` 是本轮低风险收口的页面级 view model；若后续继续膨胀，应按数据加载、通用趋势、告警控制等更细粒度继续拆分。
- 现场真实协议如果上报非 `GJ/kW/degC` 口径，仍需在设备接入层做单位换算后再进入当前监控模板。
- 历史旧告警仍可能保留 `source=telemetry`，当前按“历史遥测”兼容显示，不做历史数据迁移。
