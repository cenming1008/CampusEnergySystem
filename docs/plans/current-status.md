# Current Status

## 当前总目标
- 当前主主题：`设备监控统一模板 V4 后续结构收敛`
- 当前总目标：在不扩展新设备类型、不改现有接口路径、不改变前端展示结果的前提下，拆薄设备监控页和后端插件接口，让后续新增设备更容易接入。
- 当前执行依据：
  - 用户提供的《设备监控模块下一阶段收敛计划》
  - `docs/plans/PLAN-20260518-unified-alarm-rule-framework.md`

---

## 当前阶段
- [x] 后端 overview 已新增增量字段 `template_diagnostics`。
- [x] `template_diagnostics` 已覆盖模板身份、指标覆盖、趋势覆盖、专属面板、采集健康和 `overall_status`。
- [x] 状态判定已支持 `passed/partial/missing/offline`。
- [x] 后端诊断逻辑只基于现有模板输出与现有健康字段计算，不新增数据库表、不改变 MQTT 协议。
- [x] 前端已新增 `DeviceTemplateDiagnosticsPanel`。
- [x] `DeviceMonitor.vue` 已在通用、补偿、储能路径挂载接入诊断面板。
- [x] `docs/guides/device-monitor-template.md` 已补充 `template_diagnostics` 字段说明、状态判定和新增设备判断规则。
- [x] 后端已完成设备监控代码内插件注册第一阶段，`DeviceMonitorPluginRegistry` 负责按 `device_subtype -> device_category -> device_type/历史别名 -> generic_device` 选择监控插件。
- [x] 补偿、储能、普通表计和通用设备已通过 registry 接入统一 overview 模板构建，现有 endpoint 与返回字段保持兼容。
- [x] `DeviceMonitor.vue` 已拆薄为页面入口，只负责加载态提示与普通 / 补偿 / 储能三类视图分发。
- [x] 已新增 `GenericMonitorView.vue`、`CompensationMonitorView.vue`、`StorageMonitorView.vue` 三个视图容器，复用既有公共、补偿、储能组件。
- [x] 已新增 `useDeviceMonitorPage`，收口 overview、trend、alarms、controlLogs、statusHistory、loading、polling、刷新入口、告警处理和设备启停逻辑。
- [x] 后端已新增内部 `DeviceMonitorContext`，`DeviceMonitorPlugin.build_monitor_payload()` 改为接收 context。
- [x] `DeviceMonitorService.get_monitor_overview()` 负责构建 context，再交给 registry 命中的插件生成专属 payload。
- [x] `docs/guides/device-monitor-template.md` 已补充前端视图容器分层与后端插件 context 说明。
- [x] 已用准真实 payload 覆盖热量表、冷量表、SVG、储能诊断闭环。
- [x] 热 / 冷量表 overview 已输出 `supply_temp`、`return_temp`、`heat_flow`、派生 `temperature_delta`。
- [x] 热 / 冷量表模板第一屏已改为展示供水温度、回水温度、供回水温差、压力、累计量和瞬时功率。
- [x] SVG 缺少资产 profile 时，`module_count` 不再用静态默认值掩盖，诊断会通过 `missing_keys` 暴露缺失。
- [x] 储能缺少 `soh/cell_temp_max/charge_energy_today/discharge_energy_today` 时，诊断会通过 `missing_keys` 暴露缺失。
- [x] `docs/guides/device-monitor-template.md` 已补充冷热量表单位、温差计算和 SVG 模块数来源说明。
- [x] 告警边界已按设备原生、平台规则、平台通讯三类来源收敛；`Alarm.source` 统一使用 `device_native/platform_rule/platform_comm`。
- [x] 补偿设备原生状态位 / 故障码 / 告警码进入 `device_native`，参数门限和过补偿推导进入 `platform_rule`，补偿设备不再默认套用通用电流 / 电压阈值告警。
- [x] 接入健康已补充 `platform_comm/communication_offline` 通讯告警创建与恢复闭环；系统恢复和人工处理继续分离。
- [x] 告警中心和补偿监控告警表已展示告警来源标签；监控页面不新增核心告警判定逻辑。
- [x] 默认 scheduler 已新增每分钟全量同步平台通讯告警任务 `sync_platform_comm_alarms`。
- [x] 旧 `source=telemetry` 告警前端统一显示为“历史遥测”，不做历史数据迁移。
- [x] 统一告警规则框架第一阶段已落地：非补偿类通用电压 / 电流阈值规则支持 `default -> device_categories -> device_subtypes -> devices` 覆盖。
- [x] `config/settings.json` 已新增 `alarm_rules.platform_rules.generic_thresholds` 示例结构，旧 `default/device_thresholds` 继续兼容。
- [x] 补偿设备仍默认不套用通用电压 / 电流阈值规则，专属状态位、参数门限、谐波与过补偿逻辑保持补偿专属检测。
- [x] 电容补偿控制器平台推导规则已接入统一 profile：`alarm_rules.platform_rules.capacitor_bank` 支持同样的覆盖顺序，且 `enabled=false` 只关闭 `platform_rule` 推导，不屏蔽 `device_native` 状态位告警。
- [x] 水表、气表、冷热量表等介质表计公共字段规则已接入统一 profile：`alarm_rules.platform_rules.media_thresholds` 支持 `flow_rate/pressure/temperature` 上下限，默认关闭，需显式启用。
- [x] 储能设备基础平台规则已接入统一 profile：`alarm_rules.platform_rules.storage` 支持 `soc/soh/cell_temp_max/active_power` 阈值，默认关闭，需显式启用。
- [x] MQTT 设备扩展链路已支持储能专属遥测落库到 `StorageTelemetry`，并在写入后调用 `AlarmService.check_storage_faults()`。
- [x] 电容补偿控制器已新增 2~31 次逐次谐波谱线接入字段，支持 `voltage_harmonics_a/b/c` 与 `current_harmonics_a/b/c` JSON 谱线入库。
- [x] 补偿监控已将谐波视图拆为 `谐波趋势` 与 `高次谐波` 两个独立 tab：前者保留 THD / 谐波电流历史趋势，后者展示最新采样高次谐波频谱柱状图，支持电压 / 电流与 A/B/C 相切换、门限标线和超限着色。
- [x] MQTT 网关协议与设备监控模板文档已补充逐次谐波 payload、单位、网关换算责任和前端展示规则。
- [x] 已新增逐次谐波准真实联调 payload 工具 `scripts/python/send_capacitor_bank_harmonic_uat_payloads.py`，覆盖 A 相 5 次电压谐波超限、B 相电流谱线缺失、旧 CAP-001 无谱线和非法谱线项过滤四类验收场景。
- [x] 2026-05-16 已确认当前系统现场联调入口：MQTT 明文 `192.168.1.46:1883`、MQTT TLS `192.168.1.46:8883`、后端 API `http://192.168.1.46:8088`。
- [x] 真实设备数据已进入 MQTT 接入流水，最近记录为 `CAP-001` 发布到 `campus/device/CAP-001/telemetry`，处理状态为 `success`。

## 当前阻塞
- 当前无代码阻塞。

## 当前待办
- [ ] 真实设备联调时，继续用诊断面板复核现场冷热表单位是否已在接入层统一换算为当前模板口径。
- [ ] 后续可把接入诊断结果扩展为独立验收报告或设备接入 checklist。
- [ ] 后续再评估是否让专属面板声明动态驱动页面布局。

## 当前验证结论
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
- 2026-05-16 现场入口核验：
  - `ifconfig en0` 显示当前局域网地址为 `192.168.1.46`。
  - `lsof -nP -iTCP -sTCP:LISTEN` 显示 MQTT `*:1883`、`*:8883` 和后端 `*:8088` 正在监听。
  - `/health` 返回 `database/redis/mqtt_bridge/mqtt_worker/api_realtime/scheduler` 均为 `healthy`。
  - 数据库最新 MQTT 接入记录显示 `CAP-001` 在 `campus/device/CAP-001/telemetry` 上报成功，最近 `received_at=2026-05-15T21:17:55.785974`。

## 当前验收判断
- 当前可判定：设备监控统一模板 V4 已完成后端、前端和文档接入。
- 现有 `/devices/{id}/monitor/overview` 路径保持不变，`template_diagnostics` 为增量字段。
- 通用、补偿、储能三条页面路径均可展示接入诊断结果。
- 当前可判定：后端设备监控已进入代码内插件注册形态；新增专属设备优先新增插件，不继续扩大中心 service 手动分流。
- 当前可判定：本轮结构收敛未新增设备类型、未改变 `/devices/{id}/monitor/*` endpoint、未改变补偿 / 储能 / 普通设备 overview 返回兼容字段。
- 当前可判定：`DeviceMonitor.vue`、`DeviceMonitorService.get_monitor_overview()` 已从继续堆积复杂度转为入口编排层。
- 当前可判定：准真实 payload 校准已覆盖冷热表、SVG 和储能缺字段归因；冷热表供回水温 / 温差已经进入监控模板第一屏。
- 当前可判定：逐次谐波准真实验收 payload 已固化为脚本、测试和协议文档，可用于现场网关联调前的平台闭环验收。

## 当前剩余风险
- 接入诊断仅判断当前模板字段覆盖，不替代真实 payload 语义校准。
- 前端趋势可绘图字段仍受白名单限制。
- 专属面板声明本轮只展示，不驱动页面显隐。
- 冷热量表现场若上报 `kWh/MWh` 或厂商自定义单位，仍需在设备接入层按当前模板口径统一换算。
- 历史告警数据不做迁移；前端以“历史遥测”标签兼容展示旧 `source=telemetry`。
- 统一告警规则配置已覆盖非补偿类通用阈值、电容补偿控制器平台推导规则、介质表计公共字段规则和储能基础平台规则；更多设备族规则可后续继续分阶段迁入配置层。
- 储能专属遥测扩展只按已有 `StorageTelemetry` 字段落库；真实网关若使用其它厂商字段名，仍需在接入层补 alias 或协议映射。
- 逐次谐波第一版只展示最新采样谱线；历史回放仍在 `谐波趋势` tab 使用 THD / 谐波电流聚合趋势。现场网关必须先完成 2~31 次寄存器到工程值的换算后再上报 MQTT。
- 当前 `192.168.1.46` 是本机局域网地址，若现场网络或 DHCP 变化，需要同步更新网关侧 broker 地址和本文档中的现场入口。
