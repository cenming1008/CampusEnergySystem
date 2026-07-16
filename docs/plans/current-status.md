# Current Status

## 当前总目标

- 当前主主题：`园区光储协同仿真与 EMS 控制`。
- 当前总目标：完成系统级储能仿真、MQTT 遥测、控制回执、规则 EMS、日前优化和收益对比。
- 当前执行依据：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。

## 当前阶段

- [x] 完成 Task 1 主题治理、固定契约和迁移门禁实测。
- [ ] 由后端角色实施 Task 2 纯领域模型，不触碰 ORM、数据库或 migration。
- [ ] Task 3 持久化模型与迁移；当前阻塞。
- [ ] 阶段 A：仿真遥测。
- [ ] 阶段 B：控制与规则闭环。
- [ ] 阶段 C：日前优化与收益证据。

## 当前阻塞

- offline SQL 门禁失败：配置 PostgreSQL URL 后，`alembic upgrade head --sql` 在 revision `20260412_0003` 的 `result.fetchone()` 处报 `AttributeError: 'NoneType' object has no attribute 'fetchone'`。
- fresh、migration-built existing、runtime-sync existing 三类 PostgreSQL fixture 缺失，三条升级路径没有通过证据。
- Task 3 及所有依赖持久化的后续任务阻塞；不得修改数据库模型或 migration。
- 前一主题“后端可靠性阶段 2A”已由用户批准暂停并归档，待恢复；并未完成或通过。

## 当前验证结论

- `tests/test_backend_tooling_contracts.py`：13 passed。
- offline SQL：失败，不通过。
- fresh PostgreSQL：未验证，不通过门禁。
- migration-built existing：未验证，不通过门禁。
- runtime-sync existing：未验证，不通过门禁。
- 主题切换治理：已建立正式 PLAN，并把前一主题 status/handoff 快照归档到 `docs/plans/daily/2026-07/`。

## 固定契约

- `device_category=storage`
- `device_subtype=battery_energy_storage_system`
- 正功率充电，负功率放电。
- 仿真数据必须标记 `data_source=simulated`。

## 当前待办

1. 后端角色按正式 PLAN 实施 Task 2 纯领域模型和单元测试。
2. 在任何持久化实现前，恢复后端可靠性阶段 2A 并取得 offline、fresh 和两类 existing database 的完整通过证据。
3. 门禁通过后再解除 Task 3 及其下游持久化依赖阻塞。
4. 每一验收阶段结束时核对固定契约、非目标和可重复证据。

## 当前剩余风险

- 现有 Alembic 动态 baseline 与 runtime schema sync 使 schema 不可复现。
- 现有 `storage_telemetry` 缺少正式 migration 承载，不能直接复用为已就绪的持久化能力。
- 功率符号、SOC 时序和控制回执若跨层重复定义，可能产生契约漂移。
- 收益结论对输入假设敏感，阶段 C 必须固定基准与成本口径。

## 当前验收判断

- Task 1：治理内容已完成，待提交后复核。
- Task 2：允许作为下一棒。
- Task 3 及依赖持久化任务：打回门禁，保持阻塞。
- 下一接手角色：后端；仅限 Task 2 纯领域模型。
