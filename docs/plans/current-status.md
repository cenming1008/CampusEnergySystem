# Current Status

## 当前总目标

- 当前主主题：`园区光储协同仿真与 EMS 控制`。
- 当前总目标：从 Task 3 开始建立储能持久化契约，再按依赖推进仿真遥测、闭环控制、日前优化与收益证据。
- 当前执行依据：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md` 与 `docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。

## 当前阶段

- [x] Task 1：主题治理、固定契约与迁移门禁记录正式完成。
- [x] Task 2：纯电池领域模型、兼容惰性导出及测试正式完成。
- [ ] Task 3：持久化模型与 migration，具备准入条件，尚未开始、尚未完成。
- [ ] Task 4 及后续：按 Task 3 依赖顺序等待。

## Task 3 准入证据

- 后端可靠性阶段 2A 全部验收通过并完成治理交还；它现在是已完成依赖和历史证据，不是第二个活跃主主题。
- 静态根 revision 为 `20260716_0001`；fresh、offline、roundtrip 各 628 个对象且共同 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。
- `campus_energy` 已重建到 `20260716_0001`，包含 26 张 public 表，`public.energydata` 为 hypertable；启动校验前后结构指纹不变。
- CI workflow 阻断配置、本地固定 TimescaleDB 2.17.2 真实三路径和现有开发容器验收均已有证据；远端 GitHub Actions 本轮未实际运行。

## 固定契约

- 储能 migration：`revision = "20260716_0002"`，`down_revision = "20260716_0001"`。
- 根基线已经拥有基础 `storage_telemetry`；Task 3 只新增 profile、dispatch 和批准的 telemetry 扩展，不得重建基础表。
- `device_category=storage`，`device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电；所有模拟遥测必须标记 `data_source=simulated`。
- Task 3 必须按 TDD 实施；“具备准入条件”不等于完成。

## 当前待办

1. 后端储能角色先写 Task 3 model 与 migration 合同测试并观察 RED。
2. 以静态、offline-safe 的 `20260716_0002` migration 增加 profile、dispatch 和批准的 telemetry 扩展。
3. 完成 focused tests、offline SQL 和真实 PostgreSQL migration 验收后，再判断 Task 3 是否通过。

## 当前验收判断

- 阶段 2A：完成并归入历史依赖。
- 园区光储：唯一活跃主主题。
- Task 3：具备准入条件，尚未开始、尚未完成。
- 下一接手角色：后端储能角色。
