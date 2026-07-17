# Current Status

## 当前总目标

- 当前主主题：`园区光储协同仿真与 EMS 控制`。
- 当前总目标：Task 3 持久化契约已通过验收；当前从 Task 4 开始接入扩展仿真遥测，再推进闭环控制、日前优化与收益证据。
- 当前执行依据：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md` 与 `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。

## 当前阶段

- [x] Task 1：主题治理、固定契约与迁移门禁记录正式完成。
- [x] Task 2：纯电池领域模型、兼容惰性导出及测试正式完成。
- [x] Task 3：持久化模型、静态 migration 与真实三路径验收完成。
- [ ] Task 4：扩展仿真遥测接入，已解除依赖，尚未开始。
- [ ] Task 5 及后续：按实施计划依赖顺序等待。

## Task 3 完成证据

- 后端可靠性阶段 2A 全部验收通过并完成治理交还；它现在是已完成依赖和历史证据，不是第二个活跃主主题。
- 实现提交：`aa97e3ad`。
- `20260716_0002` 保持静态、offline-safe，仅创建 `storage_asset_profile`、`storage_dispatch_plan` 并增加八个批准遥测扩展。
- fresh、offline、roundtrip 各 682 个对象，共同 SHA-256 为 `b81c0db6aaef07fad85a7b617b005e99e1aaafee382e06da6f378eea6d4cbaec`。
- 三条路径均位于 `20260716_0002`，均保留 `public.energydata` hypertable，并已核对两张新增表和八个扩展列。
- 全量后端：`740 passed, 5 warnings`；Task 3 变更文件 Ruff 检查通过。
- 实际开发库 `campus_energy` 仍在 `20260716_0001`，尚未应用两张 Task 3 表；临时三路径验收通过不等于开发库已经升级。

## 固定契约

- 储能 migration：`revision = "20260716_0002"`，`down_revision = "20260716_0001"`。
- 根基线已经拥有基础 `storage_telemetry`；Task 3 只新增 profile、dispatch 和批准的 telemetry 扩展，不得重建基础表。
- `device_category=storage`，`device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电；所有模拟遥测必须标记 `data_source=simulated`。
- MQTT 设备侧状态键继续使用 `bms_state`、`pcs_state`、`grid_connection_state`；Task 4 入库时分别映射到 `bms_status`、`pcs_status`、`grid_status`。

## 当前待办

1. 后端储能角色按 TDD 添加 Task 4 仿真 payload 入库与监控聚合测试并观察 RED。
2. 扩展 MQTT 数值字段，并把设备侧三个 state 键显式映射到持久化 status 列。
3. 验证负功率放电符号和 `data_source=simulated` 不被改写，再运行储能接入与监控相关回归。
4. 在启动依赖 Task 3 新结构的真实运行链路前，显式升级并复核 `campus_energy` 到 `20260716_0002`；不得隐式依赖 runtime metadata 建表。

## 当前验收判断

- 阶段 2A：完成并归入历史依赖。
- 园区光储：唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：已解除依赖，尚未开始。
- 下一接手角色：后端储能角色。
