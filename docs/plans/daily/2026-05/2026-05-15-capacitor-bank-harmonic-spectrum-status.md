# 2026-05-15 电容补偿控制器高次谐波频谱状态快照

## 当前主题
- 设备监控统一模板 V4 后续结构收敛
- 本日子任务：补偿设备增加 2~31 次高次谐波频谱展示，并将其从历史谐波趋势中拆成独立 tab。

## 已完成
- 后端 `CapacitorBankTelemetry` 新增 `voltage_harmonics_a/b/c` 与 `current_harmonics_a/b/c` JSON 谱线字段。
- MQTT 补偿设备提取逻辑支持 `{ order, value }` 数组，并清洗非法阶次与非数值项。
- 电容补偿控制器模板专属面板声明新增 `harmonic_spectrum`。
- 前端补偿监控已拆为 `谐波趋势` 和 `高次谐波` 两个 tab：前者保留原 THD / 谐波电流历史趋势，后者展示最新采样 2~31 次谐波柱状谱图。
- MQTT 网关协议、设备监控模板文档和迁移 README 已同步。
- 已新增 `scripts/python/send_capacitor_bank_harmonic_uat_payloads.py` 准真实联调脚本，覆盖 A 相 5 次电压谐波超限、B 相电流谱线缺失、旧 CAP-001 无谱线和非法谱线项过滤。
- `docs/guides/mqtt-gateway-protocol.md` 已补充联调命令、验收场景表和示例片段。

## 验证
- `./venv/bin/python -m pytest tests/test_capacitor_bank_ingestion.py tests/test_device_monitor_service.py tests/test_compensation_device_nested_api.py -q` 通过：`54 passed, 1 warning`。
- `cd frontend && npm run test:unit -- viewMapping.test.ts DeviceTemplateDiagnosticsPanel.test.ts DeviceMonitor.test.ts` 通过：`4 files / 47 tests passed`。
- `cd frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_capacitor_bank_harmonic_uat_payloads.py tests/test_capacitor_bank_ingestion.py tests/test_device_monitor_service.py tests/test_compensation_device_nested_api.py -q` 通过：`57 passed, 1 warning`。
- `./venv/bin/python scripts/python/send_capacitor_bank_harmonic_uat_payloads.py --print-only --timestamp 2026-05-15T14:44:21+08:00` 通过，输出 4 条准真实联调消息。
- `cd frontend && npm run test:unit -- viewMapping.test.ts DeviceMonitor.test.ts` 通过：`2 files / 45 tests passed`。
- `git diff --check` 针对本次修改文件通过。

## 剩余风险
- 第一版逐次谐波只展示最新采样谱线，不做 2~31 次历史谱线回放。
- 网关必须先把 JKWF-LCD 原始寄存器换算为工程值后再上报 MQTT。
- 电流逐次谐波单位需现场网关确认；当前前端按 `A` 显示。
