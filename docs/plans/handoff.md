# Handoff

## 当前主题

- 当前主题：`后端可靠性阶段 2A：确定性迁移基线`。
- 正式 PLAN：`docs/plans/PLAN-20260716-backend-reliability-phase2a.md`。
- 验收记录：`docs/plans/backend-reliability-phase2a-acceptance.md`。
- 当前目标：只执行 Task 9 的主题交还，不再扩张阶段 2A 实现范围。

## 已完成证据

- pre-reset focused gate：`89 passed, 2 skipped, 3 warnings`。
- fresh、offline、roundtrip 各成功生成 628 个对象，公共指纹 SHA-256 为 `9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`；三个临时库已清理。
- `campus_energy` 仅在上述门禁通过后重建，当前 revision 为 `20260716_0001`，public 表 26 张，`energydata` 为 hypertable。
- `DB_AUTO_CREATE_TABLES=False`、`DB_RUNTIME_SCHEMA_SYNC=False` 下执行 `init_db()` 成功，前后结构指纹不变。
- 全量 `727 passed, 2 skipped, 5 warnings`，覆盖率 74%，Ruff 基线、compileall 和 diff 门禁通过。
- Ruff 基线只删除 10 条已修复 finding：168 条降至 158 条；新增 0 条，剩余集合完全一致。
- CI workflow 配置已通过本地契约及 YAML/Compose 解析；独立临时 `timescale/timescaledb:2.17.2-pg14` 容器（image ID `sha256:11505c6957fd755f9ee6e1938988fde0a5f0f3f16943aa522e3d94bb316609e7`，`127.0.0.1:55432`）已真实完成三路径验证：各 628 个对象且指纹一致，三个临时库均为 `20260716_0001` 且 `public.energydata` 为 hypertable，随后数据库与容器均已清理。现有 `latest-pg14` 也在 Task 5/8 通过但不替代固定版本证据；workflow 无 `continue-on-error`，远端 GitHub Actions 本轮未实际运行。
- 提交 `2c738e61` 同时同步了 Ruff 质量 baseline（纯删除 10 条已修复 finding）；后续证据提交不改写该历史提交。

## 下一棒：Task 9 规则/验收

1. 将储能实施计划中的 revision 更新为 `20260716_0002`、down revision 更新为 `20260716_0001`。
2. 明确根基线已拥有基础 `storage_telemetry`，储能 Task 3 只增加已批准的 profile、dispatch 和 telemetry 扩展。
3. 向当天 daily 状态与交接文件追加阶段 2A 完成快照，不覆盖已有快照。
4. 通过治理与迁移契约测试后，把主区唯一主题切回园区光储，并将 Task 3 标记为具备准入条件而非已完成。

## 固定边界

- Task 9 完成前，阶段 2A 仍是唯一活跃主主题，园区光储 Task 3 继续暂停。
- 只有阶段 2A 全部验收通过并完成 Task 9 治理交还，才能解除园区光储 Task 3 暂停状态。
- Redis 与 MQTT 容器、数据和 volumes 未修改；MQTT health 仍为本阶段非目标。
- 不在 Task 9 中实现储能 migration、持久化、API 或前端功能。
- 不触碰主工作树的用户改动 `app/api/README.md`。

## 交接结论

- Task 8：通过。
- 下一角色：规则/验收，按实施计划执行 Task 9 并完成主题收口。
