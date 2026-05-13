# 2026-05-12 设备监控统一模板 V4 交接快照

## 当前主题
- `设备监控统一模板 V4`

## 阶段结论
- V4 已完成接入诊断视图的后端字段、前端组件、页面挂载、测试和文档更新。
- `template_diagnostics` 是 overview 增量字段，不改变旧字段语义。
- 通用、补偿、储能监控路径均可展示诊断面板。
- 后端已完成代码内插件注册第一阶段，新增专属设备优先新增监控插件，普通表计优先补轻量模板。

## 下一棒
- 验收角色复核四种状态展示和既有专属页面不受影响。
- 后端/设备接入角色用真实 payload 校准字段缺失、单位和语义。
- 后端新增设备时继续使用 `DeviceMonitorPluginRegistry`，不要回到中心 service 手写分流。
- 前端角色后续可扩展接入验收 checklist。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`31 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。

## 剩余风险
- 诊断结果只代表当前模板字段覆盖，不代表真实设备 UAT 完成。
- 趋势接口未扩展任意动态字段。
- 专属面板声明未驱动页面布局。
