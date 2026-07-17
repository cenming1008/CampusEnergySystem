# Handoff

## 当前主题

- 当前主题：`园区光储协同仿真与 EMS 控制`。
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。
- 详细实施计划：`docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 当前目标：交后端储能角色执行 Task 4，不提前展开 Task 5 或后续任务。

## 已完成与准入

- Task 1、Task 2 已正式完成；Task 2 纯领域实现提交保留至 `efbbe808`。
- 后端可靠性阶段 2A 全部验收通过并完成治理交还，现作为已完成依赖和历史证据保留，不是第二个活跃主主题。
- 阶段 2A 验收提交为 `2c738e61`，补证据提交为 `735ea5c0` 与 `0f22eb60`；共同结构指纹 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。
- `campus_energy` 位于 `20260716_0001`，public 表 26 张，`public.energydata` 为 hypertable，启动仅校验。
- Task 3 已完成，提交为 `aa97e3ad`；三条 migration 路径各 682 个对象且共同指纹为 `b81c0db6aaef07fad85a7b617b005e99e1aaafee382e06da6f378eea6d4cbaec`。
- 三条路径均到 `20260716_0002`，均保留 `energydata` hypertable；两张新增表和八个扩展列已核对。
- 全量后端 `740 passed, 5 warnings`，Task 3 Ruff 通过。
- 实际开发库 `campus_energy` 仍在 `20260716_0001`，`storage_asset_profile` 与 `storage_dispatch_plan` 尚未应用。

## 下一棒：后端储能 Task 4

1. 先添加仿真 payload 入库和 monitor 聚合测试，确认新字段断言形成有效 RED。
2. MQTT payload 保持 `bms_state`、`pcs_state`、`grid_connection_state`；入库分别映射到 `bms_status`、`pcs_status`、`grid_status`。
3. `target_active_power`、可充放电功率、命令来源和数据来源按批准列直接落库。
4. 保持负功率表示放电，不得转换符号；模拟数据必须保留 `data_source=simulated`。
5. focused tests 和相关设备监控回归通过后，交验收判断 Task 4。
6. 若进入依赖新结构的真实运行联调，先显式升级 `campus_energy` 到 `20260716_0002` 并核对两张表、八个列和 `energydata` hypertable；纯单元/合同测试阶段不应借 runtime metadata 隐式补表。

## 固定业务契约

- `device_category=storage`。
- `device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电。
- 模拟数据必须带 `data_source=simulated`。
- 控制回执必须区分已接收、执行中、成功和失败，不能用入队替代设备执行成功。

## 本轮边界

- 本轮只完成 Task 3，不开始 Task 4 生产代码。
- Redis、MQTT health、readiness、rate limit 和部署顺序仍不在当前 Task 4 范围内。
- 主工作树的用户改动 `app/api/README.md` 不得触碰。

## 交接结论

- 园区光储是唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：已解除依赖，交后端储能角色执行。
