# Current Status

## 当前总目标

- 当前主主题：`后端可靠性阶段 2A：确定性迁移基线`。
- 当前总目标：完成 Task 9 的主题交还与储能迁移契约更新，在此之前保持阶段 2A 为唯一活跃主题。
- 当前执行依据：`docs/plans/PLAN-20260716-backend-reliability-phase2a.md`。
- 验收证据：`docs/plans/backend-reliability-phase2a-acceptance.md`。

## 当前阶段

- [x] 数据库名称安全、schema 指纹与隔离迁移验证工具。
- [x] 静态根基线 `20260716_0001` 与旧链归档。
- [x] online、offline、roundtrip 三路径一致性。
- [x] 启动只校验与阻断式 TimescaleDB CI 门禁。
- [x] Task 8：重建经批准可清除的 `campus_energy` 并完成本地验收。
- [ ] Task 9：交还园区光储主主题，更新储能 revision 契约与 daily 完成快照。

## 当前验收事实

- focused pre-reset gate：`89 passed, 2 skipped, 3 warnings`。
- 三条路径各为 628 个 schema objects，共同 SHA-256：`9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。
- `campus_energy` 已重建到 `20260716_0001`；public 表 26 张（含 `alembic_version`）；`energydata` 为 TimescaleDB hypertable。
- `init_db()` 执行前后对象数和指纹完全不变，启动无 schema mutation。
- 全量测试：`727 passed, 2 skipped, 5 warnings`；覆盖率 74%；Ruff、compileall、diff 门禁通过。
- Ruff 基线只删除 10 条前序已修复记录，无新增 finding，其余内容不变。
- Redis 与 MQTT volumes 未修改；MQTT health 属于非目标。

## 固定边界

- 当前唯一主主题仍为阶段 2A；Task 9 完成前不得启动园区光储 Task 3。
- 只有阶段 2A 全部验收通过并完成 Task 9 治理交还，才能解除园区光储 Task 3 暂停状态。
- 新根 revision 为 `20260716_0001`；Task 9 将储能 revision 更新为 `20260716_0002`，其 down revision 为 `20260716_0001`。
- 本阶段不处理 Redis、MQTT、readiness、rate limit、部署顺序或储能持久化。

## 当前待办

1. 执行 Task 9：更新储能两份计划中的 revision 契约。
2. 追加阶段 2A 完成 daily 快照。
3. 通过治理与迁移契约测试后，将唯一主主题切回园区光储并把 Task 3 标记为具备准入条件。

## 当前验收判断

- Task 8：通过。
- 阶段 2A：技术与本地验收门禁已通过，等待 Task 9 治理交还后收口。
- 园区光储 Task 3：继续暂停，不能提前开始。
- 下一接手角色：规则/验收，执行 Task 9。
