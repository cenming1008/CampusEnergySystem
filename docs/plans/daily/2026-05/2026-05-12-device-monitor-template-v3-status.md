# 2026-05-12 设备监控统一模板 V3 状态快照

## 本次目标
- 固化设备监控统一模板 V3 契约，覆盖后端 registry/spec、前端通用组件加固、接口样例文档和验收矩阵。

## 已完成
- 后端 `MonitorTemplateService` 已拆出模板 spec/registry。
- 已覆盖 `generic_device`、`water_meter`、`gas_meter`、`heat_meter`、`cooling_meter`、`capacitor_bank_controller`、`svg`、`storage`。
- 已新增表驱动契约测试，确保每个模板输出固定顶层字段。
- 前端 common 组件已支持空态、缺字段、长标签、空单位。
- `DeviceMonitor.vue` 保持补偿、储能专属路径，不误用通用 fallback。
- 已新增 `docs/guides/device-monitor-template.md`，包含覆盖矩阵和 overview 模板字段样例。

## 验证结果
- `./venv/bin/python -m pytest tests/test_device_monitor_service.py -q` 通过：`21 passed, 1 warning`。
- `./venv/bin/python -m pytest tests/test_mqtt_contracts.py -q` 通过：`2 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceMetricGrid.test.ts DeviceDiagnosticsSummary.test.ts DeviceTrendPanel.test.ts` 通过：`4 passed / 14 passed`。
- `cd frontend && npm run typecheck` 通过。
- `cd frontend && npm run lint -- --ext .vue,.ts ...` 通过退出码 0；仍有历史 warning。
- `git diff --check -- ...` 通过。
- `rg -n "[ \t]+$" ...` 未命中新增/本轮涉及文件尾随空白。
- `rg -n "TB[D]|TO[D]O|待[定]" docs/guides/device-monitor-template.md docs/guides/README.md` 未命中。
- `PYTHONPYCACHEPREFIX=/private/tmp/campus_pycache ./venv/bin/python -m py_compile app/services/devices/monitor_template_service.py` 通过。

## 剩余风险
- 冷热表供回水温、温差和单位需真实联调校准。
- 前端趋势字段仍受白名单限制。
- lint 历史 warning 未在本轮治理。
