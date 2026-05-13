# 2026-05-13 设备监控统一模板 V4 真实联调与诊断闭环交接快照

## 阶段结论
- 准真实 payload 校准已覆盖热量表、冷量表、SVG 和储能缺字段归因。
- 外部 `/devices/{id}/monitor/*` endpoint 未变化，未新增数据库表，未改变 MQTT 协议。
- 当前模板口径：热 / 冷累计量 `GJ`，瞬时热 / 冷功率 `kW`，供回水温和温差 `degC`。
- `temperature_delta = abs(supply_temp - return_temp)`，只在供回水温都有值时为 live。

## 下一棒
- 验收角色：打开普通表计、补偿 / SVG、储能页面，确认诊断面板不影响既有专属面板、告警表、趋势、状态面板和控制入口。
- 后端 / 设备接入角色：现场真实协议如果上报非当前模板单位，先在接入层统一换算，再进入 `EnergyData` / 专属遥测。
- 前端角色：如果现场发现诊断字段完整但 UI 显示异常，只改对应视图容器或公共诊断组件，不回填到 `DeviceMonitor.vue`。

## 已验证
- `./venv/bin/python -m pytest tests/test_device_monitor_plugin_registry.py tests/test_device_monitor_service.py tests/test_mqtt_contracts.py -q` 通过：`34 passed, 2 warnings`。
- `cd frontend && npm run test:unit -- DeviceMonitor.test.ts DeviceTemplateDiagnosticsPanel.test.ts` 通过：`2 files / 10 tests passed`。
- `cd frontend && npm run typecheck` 通过。

## 剩余风险
- 准真实测试不能替代真实设备长时间在线采集验证。
- 专属面板声明仍只展示，不驱动布局显隐。
