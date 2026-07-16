# Handoff

## 当前主题

- 当前主题：`园区光储协同仿真与 EMS 控制`。
- 正式 PLAN：`docs/plans/PLAN-20260716-campus-pv-storage-simulation.md`。
- 详细实施计划：`docs/superpowers/plans/2026-07-16-campus-pv-storage-simulation.md`。
- 当前目标：交后端储能角色执行 Task 3，不提前展开 Task 4 或后续任务。

## 已完成与准入

- Task 1、Task 2 已正式完成；Task 2 纯领域实现提交保留至 `efbbe808`。
- 后端可靠性阶段 2A 全部验收通过并完成治理交还，现作为已完成依赖和历史证据保留，不是第二个活跃主主题。
- 阶段 2A 验收提交为 `2c738e61`，补证据提交为 `735ea5c0` 与 `0f22eb60`；共同结构指纹 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。
- `campus_energy` 位于 `20260716_0001`，public 表 26 张，`public.energydata` 为 hypertable，启动仅校验。
- Task 3 当前具备准入条件，但尚未开始、尚未完成。

## 下一棒：后端储能 Task 3

1. 先按详细计划添加 model 与 migration 合同测试，确认有效 RED。
2. 使用 `revision = "20260716_0002"`、`down_revision = "20260716_0001"`。
3. 根基线已拥有基础 `storage_telemetry`；只创建 storage profile、dispatch，并添加批准的 telemetry 扩展，不得重建基础表。
4. 保持 migration 静态、offline-safe，不导入应用 metadata，不查询在线数据库状态。
5. focused tests、offline SQL 和真实 PostgreSQL migration 路径全部通过后，交验收判断 Task 3；不能只依据文件存在或 Alembic head 宣称完成。

## 固定业务契约

- `device_category=storage`。
- `device_subtype=battery_energy_storage_system`。
- 正功率充电、负功率放电。
- 模拟数据必须带 `data_source=simulated`。
- 控制回执必须区分已接收、执行中、成功和失败，不能用入队替代设备执行成功。

## 本轮边界

- 本轮 Task 9 只完成治理交还，没有开始 Task 3 生产代码、model 或 migration，也没有操作数据库。
- Redis、MQTT health、readiness、rate limit 和部署顺序仍不在当前 Task 3 范围内。
- 主工作树的用户改动 `app/api/README.md` 不得触碰。

## 交接结论

- 园区光储是唯一活跃主主题。
- Task 3：具备准入条件，交后端储能角色执行。
