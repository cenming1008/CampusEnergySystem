# PLAN-20260716 后端可靠性阶段 2A：确定性迁移基线

## 目标

- 用静态根迁移替代动态旧链。
- online、offline、roundtrip 三条路径得到相同 schema。
- 启动只校验 schema，不修改 schema。
- CI migration 恢复为阻塞门禁。

## 背景与问题

- 旧根迁移依赖当前 ORM metadata，同一 revision 无法稳定复现同一 schema。
- 旧链包含在线数据库查询，`alembic upgrade head --sql` 无法完整生成。
- 应用启动仍可能创建表、补字段、建索引或转换 hypertable，掩盖 migration 缺口。
- CI migration 当前不是阻断项，不能作为持久化准入证据。
- 本阶段只建立可信迁移底座，用于解除园区光储 Task 3 的持久化阻塞，不实现储能持久化本身。

## 数据边界

- 当前 `campus_energy` 数据经用户确认可清除。
- 迁移临时验证工具及临时验证流程中的所有破坏性操作只允许针对以下三个精确临时数据库：`ces_migration_fresh`、`ces_migration_offline`、`ces_migration_roundtrip`。
- Task 8 的 `campus_energy` 重建是临时验证工具之外的独立后置动作；三条临时路径全部通过后才允许执行该动作。
- 临时验证工具必须按精确名称白名单校验，不得创建、删除或修改上述三个临时数据库之外的数据库，也不得操作 `campus_energy`。
- Redis 与 MQTT 的数据、容器和卷不在本阶段清理范围内。

## 非目标

- 不处理 Redis。
- 不处理 MQTT 或其 health check。
- 不修改 readiness、rate limit 或部署顺序。
- 不实现储能持久化、储能 migration 或储能 API。
- 不扩展前端、公共 API、MQTT topic 或 payload。

## 固定版本

- 新根 revision：`20260716_0001`，`down_revision = None`。
- 后续储能 revision：`20260716_0002`，`down_revision = 20260716_0001`。
- 旧 revision `20260325_0001` 至 `20260515_0011` 只进入归档，不再属于 Alembic 活跃链。

## 实施范围

1. 建立数据库名称安全检查和规范化 schema 指纹。
2. 建立 online、offline、roundtrip 三条隔离 PostgreSQL 验证路径。
3. 归档旧链并创建静态、offline-safe 的 `20260716_0001` 根基线。
4. 证明三条路径的最终 schema 指纹一致。
5. 将应用启动改为只校验 schema，禁止运行时 schema mutation。
6. 恢复 TimescaleDB 支撑的阻断式 CI migration 门禁。
7. 临时库验证全部通过后，重建可丢弃的 `campus_energy` 并记录证据。
8. 阶段 2A 全部验收通过后，把唯一主主题交还园区光储并解除 Task 3 阻塞。

## 角色与交接

- 规则：维护本 PLAN、固定范围、版本和验收门禁。
- 后端：实现迁移验证工具、静态基线和启动校验契约。
- 验收：核对静态契约、三条数据库路径、开发库重建、启动行为和 CI 配置证据。
- 园区光储 Task 3 在本阶段通过前保持暂停，不作为并行活跃主题。

## 验收

- 静态迁移契约通过：活跃链只有静态根基线，不导入应用模型或动态 metadata，不依赖在线检查。
- online、offline、roundtrip 三条路径均完成，且三个规范化 schema 指纹一致。
- 三条临时路径通过后，开发库 `campus_energy` 重建成功并位于 `20260716_0001`。
- 应用启动无 schema mutation；缺失 schema 时给出可执行的迁移提示并失败。
- CI migration 使用 TimescaleDB，并且无 `continue-on-error`，失败会阻断工作流。
- 后端相关回归测试无新增失败，验收证据写入阶段 2A 验收文档。

## 风险与控制

- 静态基线遗漏运行时对象：重建前以三路径指纹和启动必需对象清单双重核对。
- 误删数据库：临时验证工具和流程只接受 `ces_migration_fresh`、`ces_migration_offline`、`ces_migration_roundtrip` 三个精确名称；Task 8 重建 `campus_energy` 是工具之外、通过全部临时验证后才执行的独立后置步骤。
- 归档文件仍被 Alembic 加载：契约测试要求旧 revision 离开 `migrations/versions/`。
- TimescaleDB 与普通 PostgreSQL 行为不同：本地和 CI 均使用 PostgreSQL 14 对应的 TimescaleDB 环境。

## 收口条件

- 只有全部验收项均有可重复证据，阶段 2A 才能标记完成。
- 只有阶段 2A 全部验收通过，且根基线完成三路径验证、开发库重建、启动仅校验和阻断式 CI 门禁后，主区才切回园区光储主题，并将 Task 3 从“阻塞”改为“可开始”；仅 `20260716_0001` revision 文件或静态契约通过不足以恢复 Task 3。
