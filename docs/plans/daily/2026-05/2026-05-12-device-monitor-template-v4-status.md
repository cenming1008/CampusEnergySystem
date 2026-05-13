# 2026-05-12 设备监控统一模板 V4 状态快照

## 本次目标
- 在设备监控统一模板上增加接入诊断视图，帮助验收模板命中、指标覆盖、趋势可绘图能力、专属面板声明和采集健康。

## 已完成
- 后端 overview 已新增 `template_diagnostics` 增量字段。
- 已实现 `passed/partial/missing/offline` 状态判定。
- 已新增前端 `DeviceTemplateDiagnosticsPanel`。
- `DeviceMonitor.vue` 已在通用、补偿、储能路径展示诊断面板。
- `docs/guides/device-monitor-template.md` 已更新诊断字段、状态规则和新增设备判断说明。
- 后端已新增代码内插件注册机制，补偿、储能、普通表计和通用设备通过 `DeviceMonitorPluginRegistry` 接入统一 overview 模板构建。

## 验证结果
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`31 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。

## 剩余风险
- 接入诊断不替代真实 payload 语义校准。
- 前端趋势字段仍受白名单限制。
- 专属面板声明本轮只展示，不驱动布局。
