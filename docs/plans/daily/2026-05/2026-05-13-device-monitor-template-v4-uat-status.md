# 2026-05-13 设备监控统一模板 V4 真实联调与诊断闭环状态快照

## 当前总目标
- 用准真实 payload 复核普通表计、补偿 / SVG、储能三类监控路径的模板诊断能力，并校准冷热表、SVG、储能的字段语义。

## 已完成
- 热 / 冷量表监控实时 payload 已包含 `supply_temp`、`return_temp`、`heat_flow` 和派生 `temperature_delta`。
- 热 / 冷量表第一屏指标已展示供水温度、回水温度、供回水温差、压力、累计量和瞬时功率。
- 热 / 冷量表趋势字段收敛为当前前端可绘图的 `consumption` 与 `flow_rate`。
- SVG 缺少资产 profile 时，`module_count` 会通过 `template_diagnostics.metric_coverage.missing_keys` 暴露为缺失。
- 储能缺少 `soh/cell_temp_max/charge_energy_today/discharge_energy_today` 时，诊断会暴露对应缺失字段。
- `docs/guides/device-monitor-template.md` 已补充冷热表单位、温差计算和 SVG 模块数来源说明。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`34 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。

## 剩余风险
- 准真实 payload 不替代现场真实设备 UAT。
- 现场协议若上报 `kWh/MWh` 或厂商自定义单位，仍需在接入层换算为当前模板口径。
