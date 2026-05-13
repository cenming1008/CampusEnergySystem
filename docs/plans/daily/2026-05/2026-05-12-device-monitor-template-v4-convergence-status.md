# 2026-05-12 设备监控统一模板 V4 后续结构收敛状态快照

## 当前总目标
- 在不新增设备类型、不改接口路径、不改变前端展示结果的前提下，拆薄设备监控页和后端插件接口。

## 已完成
- `DeviceMonitor.vue` 已收敛为页面入口，负责加载态提示和普通 / 补偿 / 储能三类视图分发。
- 新增 `GenericMonitorView.vue`、`CompensationMonitorView.vue`、`StorageMonitorView.vue` 三个视图容器。
- 新增 `useDeviceMonitorPage` 收口 overview、trend、alarms、controlLogs、statusHistory、loading、polling、刷新入口、告警处理和设备启停逻辑。
- 新增后端内部 `DeviceMonitorContext`，`DeviceMonitorPlugin.build_monitor_payload()` 改为接收 context。
- `DeviceMonitorService.get_monitor_overview()` 负责构建 context，再交给插件生成专属 payload。
- `docs/guides/device-monitor-template.md` 已补充前端视图容器分层和后端插件 context 说明。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`32 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。

## 剩余风险
- 本轮只做结构迁移，不替代真实设备 UAT。
- `useDeviceMonitorPage` 后续若继续膨胀，应再按数据加载、趋势、告警控制等职责拆细。
