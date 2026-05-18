# Handoff

## 当前主题
- 当前主主题：`设备监控统一模板 V4 后续结构收敛`
- 当前执行依据：
  - 用户提供的《设备监控模块下一阶段收敛计划》
  - `docs/plans/PLAN-20260518-unified-alarm-rule-framework.md`

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
- 统一告警规则框架第一阶段已落地：
  - 新增 `app/domain/alarm_rule_profiles.py`，负责解析设备告警规则 profile。
  - 非补偿类通用电压 / 电流阈值规则支持 `default -> device_categories -> device_subtypes -> devices` 覆盖。
  - `enabled=false` 可关闭某一层通用阈值规则。
  - 旧 `config/settings.json` 的 `default/device_thresholds` 结构仍兼容；新增配置优先使用 `alarm_rules.platform_rules.generic_thresholds`。
  - 补偿设备仍不套用通用电压 / 电流阈值告警。
  - 电容补偿控制器平台推导规则已接入 `alarm_rules.platform_rules.capacitor_bank`，支持同样的覆盖顺序；`enabled=false` 只关闭平台推导，不屏蔽设备原生状态位告警。
  - 水表、气表、冷热量表等介质表计公共字段规则已接入 `alarm_rules.platform_rules.media_thresholds`，支持 `flow_rate/pressure/temperature` 上下限；默认关闭，需显式启用。
  - 储能设备基础平台规则已接入 `alarm_rules.platform_rules.storage`，支持 `soc/soh/cell_temp_max/active_power` 阈值；默认关闭，需显式启用。
- MQTT 设备扩展链路已支持储能专属遥测落库到 `StorageTelemetry`，并在写入后调用 `AlarmService.check_storage_faults()`。
- 电容补偿控制器已新增 2~31 次逐次谐波谱线接入：
  - 后端 `CapacitorBankTelemetry` 支持 `voltage_harmonics_a/b/c` 与 `current_harmonics_a/b/c` JSON 字段。
  - MQTT payload 接受 `{ "order": 2..31, "value": finite number }` 数组，非法阶次或非数值项会被丢弃，不影响整条遥测。
  - 补偿监控已拆为 `谐波趋势` 与 `高次谐波` 两个 tab：`谐波趋势` 保留原三相电压 THD / 谐波电流历史趋势，`高次谐波` 展示最新采样的逐次谐波柱状谱图。
  - 电容补偿控制器模板专属面板已新增 `harmonic_spectrum`。
  - 准真实验收脚本 `scripts/python/send_capacitor_bank_harmonic_uat_payloads.py` 已固化 4 类 payload：A 相 5 次电压谐波超限、B 相电流谱线缺失、旧 CAP-001 无谱线、非法谱线项过滤。
- 2026-05-16 现场真实设备数据已进入平台：
  - 当前系统局域网地址：`192.168.1.46`。
  - MQTT 明文入口：`192.168.1.46:1883`。
  - MQTT TLS 入口：`192.168.1.46:8883`。
  - 后端 API / 健康检查：`http://192.168.1.46:8088`。
  - 最新接入流水可见 `CAP-001` 发布到 `campus/device/CAP-001/telemetry`，状态 `success`。
  - `.env` 中 `MQTT_BROKER=localhost` 保持为平台 worker 连接本机 broker 的内部配置；现场网关使用局域网地址连接。

## 下一棒
- 验收角色：
  - 复核四种状态判定是否符合接入验收预期；当前准真实测试已覆盖 `passed/partial/missing/offline`。
  - 打开普通表计、补偿设备、储能设备监控页，确认诊断面板不影响既有专属页面。
- 后端/设备接入角色：
  - 现场网关继续使用 `192.168.1.46:1883` 发布 dev 明文 MQTT；如切换 TLS，则改用 `192.168.1.46:8883` 并下发 CA。
  - 用真实 payload 继续复核冷热表单位是否已换算到模板口径：累计热 / 冷量 `GJ`，瞬时热 / 冷功率 `kW`，温度 `degC`。
  - 联调逐次谐波时，网关需要先把 JKWF-LCD 2~31 次寄存器换算为工程值后再上报 `voltage_harmonics_a/b/c`、`current_harmonics_a/b/c`；平台不解析原始 RS-485 / Modbus 帧。
  - 现场网关未就绪时，可先运行 `./venv/bin/python scripts/python/send_capacitor_bank_harmonic_uat_payloads.py --print-only` 对齐 payload，再连接 broker 发送到 `campus/device/CAP-001/telemetry` 做平台闭环。
  - 关注诊断面板暴露出的缺失字段，优先判断是 MQTT 映射问题还是模板定义问题。
  - 新增专属设备时优先新增监控插件；普通表计优先补轻量模板，不回到 `DeviceMonitorService` 手写分流。
- 前端角色：
  - 新增设备专属页面时优先新增或复用 `features/device-monitor/views/*MonitorView.vue` 视图容器，不把大段 template 重新堆回 `DeviceMonitor.vue`。
  - 新增页面级请求、轮询或刷新副作用时优先进入 `useDeviceMonitorPage` 或进一步拆出稳定 composable。
  - 后续如需要，可把诊断面板扩展为接入验收 checklist 或独立报告。
  - 告警相关 UI 只展示 `Alarm.source/category/message` 等后端返回语义，不在页面根据实时值制造核心告警。
  - 逐次谐波第一版只展示最新采样谱线；历史回放仍在 `谐波趋势` tab 看 THD / 谐波电流聚合趋势。
  - 告警规则配置第一阶段没有前端改动；后续如做规则管理页，应只编辑后端规则配置，不在页面侧复刻判定逻辑。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`34 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_alarm_service.py tests/test_alarm_endpoints.py tests/test_device_monitor_service.py tests/test_ingestion_health_service.py -q` 通过：`46 passed, 1 warning`。
- `cd frontend && npm run test:unit -- sourceLabels.test.ts DeviceMonitor.test.ts` 通过：`2 files / 13 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_scheduler_jobs.py tests/test_ingestion_health_service.py -q` 通过：`11 passed, 1 warning`。
- `./venv/bin/python -m pytest tests/test_alarm_rule_profiles.py tests/test_alarm_service.py tests/test_alarm_endpoints.py tests/test_ingestion_health_service.py tests/test_capacitor_bank_ingestion.py tests/test_compensation_device_nested_api.py tests/test_storage_device_nested_api.py tests/test_storage_ingestion.py tests/test_mqtt_contracts.py -q` 通过：`72 passed, 2 warnings`。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_ingestion.py tests/test_device_monitor_service.py tests/test_compensation_device_nested_api.py -q` 通过：`54 passed, 1 warning`。
- `cd frontend && npm run test:unit -- viewMapping.test.ts DeviceTemplateDiagnosticsPanel.test.ts DeviceMonitor.test.ts` 通过：`4 files / 47 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_harmonic_uat_payloads.py tests/test_capacitor_bank_ingestion.py tests/test_device_monitor_service.py tests/test_compensation_device_nested_api.py -q` 通过：`57 passed, 1 warning`。
- `./venv/bin/python scripts/python/send_capacitor_bank_harmonic_uat_payloads.py --print-only --timestamp 2026-05-15T14:44:21+08:00` 通过，已打印 4 条 `campus/device/CAP-001/telemetry` 准真实联调消息。
- `cd frontend && npm run test:unit -- viewMapping.test.ts DeviceMonitor.test.ts` 通过：`2 files / 45 tests passed`。
- `ifconfig en0` 确认当前系统局域网地址为 `192.168.1.46`。
- `lsof -nP -iTCP -sTCP:LISTEN` 确认 `*:1883`、`*:8883`、`*:8088` 正在监听。
- `/health` 返回关键服务均为 `healthy`，其中 `mqtt_worker` 为 `healthy` 且已连接。
- 数据库 MQTT 接入流水最新记录确认 `CAP-001` / `campus/device/CAP-001/telemetry` / `success`，最近 `received_at=2026-05-15T21:17:55.785974`。

## 剩余风险
- 当前诊断结果基于模板输出和当前健康字段，不替代真实设备 UAT。
- 暂不可绘图字段只做展示，不在本轮扩展趋势接口。
- 专属面板声明不在本轮驱动布局。
- `useDeviceMonitorPage` 是本轮低风险收口的页面级 view model；若后续继续膨胀，应按数据加载、通用趋势、告警控制等更细粒度继续拆分。
- 现场真实协议如果上报非 `GJ/kW/degC` 口径，仍需在设备接入层做单位换算后再进入当前监控模板。
- 历史旧告警仍可能保留 `source=telemetry`，当前按“历史遥测”兼容显示，不做历史数据迁移。
- 告警规则配置已迁入非补偿类通用阈值、电容补偿控制器平台推导规则、介质表计公共字段规则和储能基础平台规则；更多设备族规则可后续继续按设备族逐步迁入。
- 储能专属遥测扩展只按已有 `StorageTelemetry` 字段落库；真实网关若使用其它厂商字段名，仍需在接入层补 alias 或协议映射。
- 逐次谐波频谱依赖网关上报最新谱线；历史接口当前不做 2~31 次长周期谱线回放。
- `192.168.1.46` 来自当前本机 `en0` 地址；现场网络切换、DHCP 重新分配或改用固定 IP 后，需要同步更新网关侧配置与协议文档现场入口。
