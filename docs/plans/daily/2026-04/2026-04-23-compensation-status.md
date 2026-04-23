# 2026-04-23 Compensation Status

## 当前总目标
- 推进 `设备监控页实时数据语义收敛专题` 的 `P1`，压缩无功补偿监控页里仍为 `mock / estimated / configured_fallback` 的关键字段。

## 当前阶段
- 已完成 `P1` 第一轮收口：电容补偿控制器的控制模式、回路投入数、容量利用率现已优先消费参数快照回读。
- 已完成 `P1` 第二轮收口：柜内温度已补齐 `temperature_health` 语义，前端概览会优先展示真实告警位/参数上限回读得出的健康判定。
- 当前结论：补偿专题仍保持 `MVP+` 阶段完成口径，但“关键指标真实化”已从纯分析进入实际收口阶段。

## 当前验证结论
- `./venv/bin/python -m pytest tests/test_database_core.py tests/test_device_monitor_service.py -q` 通过（`21 passed, 1 warning`）。
- `./venv/bin/python -m pytest tests/test_compensation_device_contract.py tests/test_compensation_monitor_service_boundary.py tests/test_capacitor_bank_service.py tests/test_device_monitor_service.py tests/test_database_core.py -q` 通过（`37 passed, 1 warning`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 通过（`18 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceMonitor DeviceControlConsole capacitorBankControlProfile src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 通过（`25 passed`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run typecheck` 通过。
- `./venv/bin/python -m pytest tests/test_compensation_monitor_service_boundary.py tests/test_device_monitor_service.py tests/test_database_core.py tests/test_capacitor_bank_service.py -q` 通过（`36 passed, 1 warning`）。
- `cd /Users/todo/CampusEnergySystem/frontend && npm run test:unit -- DeviceMonitor src/features/device-monitor/components/compensation/__tests__/viewMapping.test.ts` 通过（`21 passed`）。

## 当前剩余风险
- 当前收口仍建立在“参数快照已真实回读”前提上，不等于真实设备/网关控制协议已经冻结。
- 高风险控制动作边界仍未定版，不能把本轮字段真实化外推为“正式交付已完成”。
- 若现场真实协议后续不给 `temp_alarm` 或不给稳定阈值回读，温度健康度还需要按真实报文再次校准。
