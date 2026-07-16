# Current Status

## 当前总目标

- 当前主主题：`后端可靠性阶段 2A：确定性迁移基线`。
- 当前总目标：以静态根迁移建立可复现 schema，使 online、offline、roundtrip 三条路径一致，并恢复启动只校验与 CI 阻断门禁。
- 当前执行依据：`docs/plans/PLAN-20260716-backend-reliability-phase2a.md`。

## 当前阶段

- [x] 阶段 2A 设计经用户批准，实施计划已建立。
- [ ] 治理切换与园区光储暂停快照验收。
- [ ] 数据库安全与 schema 指纹核心。
- [ ] 隔离 PostgreSQL migration 验证工具。
- [ ] 旧链归档与静态根基线 `20260716_0001`。
- [ ] online、offline、roundtrip 三路径验证。
- [ ] 启动只校验、阻断式 CI、开发库后置重建与最终验收。

## 当前事实

- 当前 `campus_energy` 位于旧 revision `20260515_0011`，其数据经用户确认可丢弃。
- offline SQL 在旧 revision `20260412_0003` 的 `result.fetchone()` 处稳定失败。
- 旧根迁移使用动态 ORM metadata，应用启动仍可能执行 schema mutation，CI migration 仍允许失败。
- PostgreSQL Docker 服务可用不是 offline SQL 失败的根因；迁移链本身不满足确定性与离线生成契约。
- 所有破坏性操作只允许针对三个精确名称的临时库：`ces_migration_fresh`、`ces_migration_offline`、`ces_migration_roundtrip`；`campus_energy` 只可在三条临时路径全部通过后重建。

## 固定边界

- 新根 revision 固定为 `20260716_0001`，后续储能 revision 固定为 `20260716_0002`。
- 本阶段不处理 Redis、MQTT、readiness、rate limit、部署顺序或储能持久化。
- 园区光储 Task 1、Task 2 已正式完成；Task 3 作为暂停依赖保持阻塞，不是第二个活跃主主题。
- 园区光储暂停状态已追加到 `docs/plans/daily/2026-07/`；恢复条件为阶段 2A 全部验收通过，即根基线完成三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁，不能只依据 `20260716_0001` revision 自身验收恢复。

## 当前待办

1. 完成并验收阶段 2A 治理切换。
2. 交后端按 TDD 实现数据库名称安全、schema 指纹与三路径验证工具。
3. 在临时数据库验证通过前，不归因于数据、不重建 `campus_energy`、不启动储能 Task 3。

## 当前验收门禁

- 静态迁移契约：未验证。
- online、offline、roundtrip 指纹一致：未验证。
- 启动无 schema mutation：未验证。
- CI migration 无 `continue-on-error`：未验证。
- 临时路径通过后的开发库重建：未执行。

## 当前剩余风险

- 静态基线可能遗漏历史运行时补出的字段、索引或 TimescaleDB 对象。
- 数据库清理若缺少名称安全检查，可能误触非目标数据库。
- 在移除启动时修复前，migration 缺口仍可能被运行时行为掩盖。

## 当前验收判断

- 阶段 2A：已恢复为唯一主主题，尚未完成。
- 园区光储 Task 3：继续阻塞，等待阶段 2A 全部验收通过；仅根 revision 或静态迁移契约通过不得解除阻塞。
- 下一接手角色：后端，先实现 migration 验证工具的纯安全与指纹核心；完成后交验收。
