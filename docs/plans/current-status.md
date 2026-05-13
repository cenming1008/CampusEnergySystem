# Current Status

## 当前总目标
- 当前主主题：`设备监控统一模板 V4 后续结构收敛`
- 当前总目标：在不扩展新设备类型、不改现有接口路径、不改变前端展示结果的前提下，拆薄设备监控页和后端插件接口，让后续新增设备更容易接入。
- 当前执行依据：
  - 用户提供的《设备监控模块下一阶段收敛计划》

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

## 当前验收判断
- 当前可判定：设备监控统一模板 V4 已完成后端、前端和文档接入。
- 现有 `/devices/{id}/monitor/overview` 路径保持不变，`template_diagnostics` 为增量字段。
- 通用、补偿、储能三条页面路径均可展示接入诊断结果。
- 当前可判定：后端设备监控已进入代码内插件注册形态；新增专属设备优先新增插件，不继续扩大中心 service 手动分流。
- 当前可判定：本轮结构收敛未新增设备类型、未改变 `/devices/{id}/monitor/*` endpoint、未改变补偿 / 储能 / 普通设备 overview 返回兼容字段。
- 当前可判定：`DeviceMonitor.vue`、`DeviceMonitorService.get_monitor_overview()` 已从继续堆积复杂度转为入口编排层。
- 当前可判定：准真实 payload 校准已覆盖冷热表、SVG 和储能缺字段归因；冷热表供回水温 / 温差已经进入监控模板第一屏。

## 当前剩余风险
- 接入诊断仅判断当前模板字段覆盖，不替代真实 payload 语义校准。
- 前端趋势可绘图字段仍受白名单限制。
- 专属面板声明本轮只展示，不驱动页面显隐。
- 冷热量表现场若上报 `kWh/MWh` 或厂商自定义单位，仍需在设备接入层按当前模板口径统一换算。
