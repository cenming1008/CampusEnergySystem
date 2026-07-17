# Current Status

## 当前总目标

- 当前主主题：`园区光储协同仿真与 EMS 控制`。
- 当前总目标：Task 4 扩展仿真遥测入库与监控聚合已通过验收；当前从 Task 5 开始构建可复用 MQTT 储能仿真器。
- 当前执行依据：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md` 与 `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。

## 当前阶段

- [x] Task 1：主题治理、固定契约与迁移门禁记录正式完成。
- [x] Task 2：纯电池领域模型、兼容惰性导出及测试正式完成。
- [x] Task 3：持久化模型、静态 migration 与真实三路径验收完成。
- [x] Task 4：扩展仿真遥测入库、状态映射与监控聚合完成。
- [ ] Task 5：可复用 MQTT 储能仿真器，已解除依赖，尚未开始。
- [ ] Task 6 及后续：按实施计划依赖顺序等待。

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

## Task 4 完成证据

- 实现提交：`0e1fd1bc`。
- 仿真 payload 的目标功率、可充放电功率、三个设备状态、命令来源和 `data_source=simulated` 均可落入专属遥测层。
- `active_power=-120.0` 入库与监控聚合后保持负值，不改变放电符号。
- 监控聚合新增目标功率、可用功率、BMS/PCS/并网状态、命令来源和模拟来源指标。
- 完整环境全量后端：`742 passed, 5 warnings`；Task 4 Ruff 检查通过。

## 当前待办

1. 后端储能角色按 TDD 添加 Task 5 CLI、确定性 payload 与默认关闭设置测试并观察 RED。
2. 实现 `--print-only`、固定 seed、场景/速度参数和明确的 `data_source=simulated`。
3. 增加默认关闭的储能 EMS/仿真配置与环境示例，并记录 MQTT topic、功率符号和系统级仿真边界。
4. 正常 MQTT 模式联调前，显式升级并复核 `campus_energy` 到 `20260716_0002`；`--print-only` 与纯测试不依赖开发库升级。

## 当前验收判断

- 阶段 2A：完成并归入历史依赖。
- 园区光储：唯一活跃主主题。
- Task 3：通过并正式完成。
- Task 4：通过并正式完成。
- Task 5：已解除依赖，尚未开始。
- 下一接手角色：后端储能角色。
