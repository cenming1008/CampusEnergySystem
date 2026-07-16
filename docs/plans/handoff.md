# Handoff

## 当前主题

- 当前主题：`后端可靠性阶段 2A：确定性迁移基线`。
- 正式 PLAN：`docs/plans/PLAN-20260716-backend-reliability-phase2a.md`。
- 当前目标：建立静态 `20260716_0001` 根基线、三条一致的迁移路径、启动只校验契约和阻断式 CI 门禁。

## 已知证据

- 旧根 migration 依赖 ORM metadata，无法保证同 revision 复现同 schema。
- 旧链 offline SQL 在 `20260412_0003` 的在线结果读取处失败；开启 Docker 不会修复该链缺陷。
- 当前 `campus_energy` 数据可丢弃，但只能在三条临时路径全部通过后执行一次后置重建。
- 园区光储 Task 1、Task 2 已正式完成，相关提交保留至 `efbbe808`；Task 3 未开始。

## 固定契约

- 所有破坏性操作仅允许三个精确名称的临时数据库：`ces_migration_fresh`、`ces_migration_offline`、`ces_migration_roundtrip`；验证工具必须拒绝其他任何数据库名称。
- 新根 revision 为 `20260716_0001`；储能 Task 3 后续使用 `20260716_0002`，其 down revision 为 `20260716_0001`。
- online、offline、roundtrip 三条路径必须产生一致的规范化 schema 指纹。
- 应用启动只校验 schema，不创建表、不补字段或索引、不执行 hypertable DDL。
- CI migration 不得配置 `continue-on-error`。

## 下一棒

### 后端

- 按实施计划 Task 2 先用 TDD 建立纯数据库名称安全和 schema 指纹核心。
- 后续再编排三个固定临时库：`ces_migration_fresh`、`ces_migration_offline`、`ces_migration_roundtrip`。
- 在 Tasks 1-7 全部通过前，不得重建 `campus_energy`。

### 验收

- 每个任务结束后核对文件边界、RED-GREEN 证据和相关回归。
- 最终核对静态迁移契约、三指纹一致、开发库重建、启动无 mutation、CI 阻断五类证据。

## 暂停依赖

- 园区光储不是当前活跃主题。
- 园区光储 Task 1、Task 2 保持已完成；Task 3 因阶段 2A 迁移门禁保持阻塞。
- 只有阶段 2A 全部验收通过，且根基线完成三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁，才切回园区光储并把 Task 3 改为可开始；仅 `20260716_0001` revision 自身验收通过不满足恢复门禁。

## 非目标

- Redis、MQTT、readiness、rate limit、部署顺序和储能持久化均不在本阶段处理。
- 不以 startup metadata 建表、直接 stamp 或人工补表掩盖 migration 缺口。

## 交接结论

- 阶段 2A 已恢复为唯一主主题，当前处于治理切换后的实现起点。
- 下一接手角色为后端；首个实现对象是 migration 验证工具的安全与指纹核心。
