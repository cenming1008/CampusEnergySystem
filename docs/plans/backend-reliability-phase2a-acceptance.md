# 后端可靠性阶段 2A 验收记录

## 验收结论

- Task 8 验收通过：确定性迁移基线已通过临时三路径验证，并已用于重建经用户批准可清除的开发数据库 `campus_energy`。
- 当前唯一主主题仍为“后端可靠性阶段 2A：确定性迁移基线”；Task 9 完成主题交还前，不启动园区光储 Task 3。
- Redis 与 MQTT 的容器、数据和 volumes 均未修改；MQTT health 状态不属于本阶段验收范围。

## 运行环境

- 数据库容器：`campusenergysystem-db-1`，TimescaleDB/PostgreSQL 14 服务健康。
- Python：`/Users/todo/CampusEnergySystem/venv/bin/python`。当前工作树没有独立 `venv`，因此命令通过共享项目虚拟环境执行；质量脚本通过将该虚拟环境置于 `PATH` 首位执行。
- 开发数据库：`campus_energy`；其数据已由用户明确确认可丢弃。

## 破坏性操作门禁

重建前先执行：

```bash
/Users/todo/CampusEnergySystem/venv/bin/python -m pytest -q \
  tests/test_migration_baseline_contract.py \
  tests/test_postgres_migration_verifier.py \
  tests/test_postgres_migration_paths.py \
  tests/test_database_core.py \
  tests/test_startup_checks.py \
  tests/test_backend_tooling_contracts.py
```

结果：`89 passed, 2 skipped, 3 warnings`。

随后执行：

```bash
MIGRATION_ADMIN_URL=postgresql://admin:***@localhost:5432/postgres \
  /Users/todo/CampusEnergySystem/venv/bin/python \
  scripts/python/verify_postgres_migrations.py \
  --json-output /tmp/phase2a-final.json
```

结果：

- `fresh`：成功，628 个 schema objects。
- `offline`：成功，628 个 schema objects。
- `roundtrip`：成功，628 个 schema objects。
- 三个临时数据库已自动删除。
- 三条路径规范化指纹的共同 SHA-256：`9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`。

只有上述门禁全部通过后，才执行已批准动作：

```bash
docker exec campusenergysystem-db-1 dropdb -U admin --if-exists --force campus_energy
docker exec campusenergysystem-db-1 createdb -U admin campus_energy
```

两条命令均退出 `0`。没有清理 Redis 或 MQTT volumes。

## 基线应用与数据库结构

执行：

```bash
DATABASE_URL=postgresql://admin:***@localhost:5432/campus_energy \
  /Users/todo/CampusEnergySystem/venv/bin/python -m alembic upgrade head
```

结果：退出 `0`，应用静态根迁移 `20260716_0001`。

数据库查询结果：

- `alembic_version.version_num`：`20260716_0001`。
- `public` schema 表数量：26。
- `alembic_version` 表：存在，计入上述 26 张表。
- `timescaledb_information.hypertables`：`public.energydata`。

## 启动只校验证明

启动校验前，`campus_energy` 规范化结构为 628 个对象，SHA-256 为：

`9f52eafa4140a7328074fa3c6fa4414fe3107a5fa49cbca23a34de60b5acf42c`

执行：

```bash
DATABASE_URL=postgresql://admin:***@localhost:5432/campus_energy \
DB_AUTO_CREATE_TABLES=False \
DB_RUNTIME_SCHEMA_SYNC=False \
  /Users/todo/CampusEnergySystem/venv/bin/python \
  -c "from app.core.database import init_db; init_db()"
```

结果：退出 `0`。执行后仍为 628 个对象，SHA-256 不变，证明 `init_db()` 未创建表、补字段、补索引或执行 hypertable DDL。

## 完整回归与质量门禁

所有命令均设置 `DATABASE_URL` 指向重建后的 `campus_energy`，并设置 `DB_AUTO_CREATE_TABLES=False`、`DB_RUNTIME_SCHEMA_SYNC=False`。

| 门禁 | 结果 |
| --- | --- |
| `python -m pytest -q` | `727 passed, 2 skipped, 5 warnings` |
| `bash ./scripts/shell/run_backend_coverage.sh` | `727 passed, 2 skipped, 5 warnings`；总覆盖率 74%，高于 57% 门槛 |
| `python scripts/python/check_ruff_regressions.py` | 通过；Ruff 基线为 158 条 |
| `python -m compileall -q app tests scripts/python migrations` | 通过；使用 `PYTHONPYCACHEPREFIX=/tmp/phase2a-pycache` 避免写入工作区外的 macOS 缓存目录 |
| `git diff --check` | 通过 |

Ruff 基线由 168 条缩减为 158 条。严格集合比较结果为：新增 0 条、删除 10 条、其余 158 条内容和计数完全不变；本次没有扩大忽略范围或引入新债务。

## 警告与范围说明

- 测试警告包括：共享 Python 使用 LibreSSL 2.8.3 触发 urllib3 `NotOpenSSLWarning`；默认 `SECRET_KEY` 触发开发环境安全提示。
- 这些警告未影响迁移、结构校验、启动只校验或测试结果；生产环境仍必须提供非默认 `SECRET_KEY`。
- MQTT 容器当前 health 状态及其修复不在阶段 2A 范围内；本轮未操作 MQTT。
- Redis、readiness、rate limit、部署顺序和储能持久化均未扩入本轮。

## 最终判断与交接

- Task 8：通过。
- 阶段 2A 的迁移底座验收证据已完整；Task 9 仍需执行主主题交还、daily 完成快照和储能 revision 契约更新。
- 下一角色：规则/验收执行 Task 9。Task 9 完成前，园区光储 Task 3 继续保持暂停。
