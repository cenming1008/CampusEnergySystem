# 2026-05-12 设备监控统一模板 V3 交接快照

## 当前主题
- `设备监控统一模板 V3`

## 阶段结论
- V3 已完成后端、前端和文档契约收口。
- 后端模板定义已集中为 registry/spec，service 负责选择模板与组装 payload。
- 前端通用组件已可承接通用设备模板字段，补偿和储能路径仍使用专属组件。
- 契约文档已包含模板覆盖矩阵与水、气、冷热、储能、SVG、补偿控制器样例。

## 下一棒
- 验收角色：
  - 复核模板覆盖矩阵、测试 fixture 和文档样例是否一致。
- 后端角色：
  - 后续真实联调时校准冷热表、储能、SVG 的现场 payload 映射。
- 前端角色：
  - 后续可把模板覆盖矩阵产品化为接入验收/诊断视图。

## 已验证
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
- 样例仍基于当前公共遥测字段，需要现场 payload 校准后进一步细化。
- 当前不新增独立 `/monitor/template` 接口。
