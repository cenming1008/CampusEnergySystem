# 后端可靠性阶段 2A 验收记录

## 验收结论

- Task 8 验收通过：确定性迁移基线已通过临时三路径验证，并已用于重建经用户批准可清除的开发数据库 `campus_energy`。
- 当前唯一主主题仍为“后端可靠性阶段 2A：确定性迁移基线”；Task 9 完成主题交还前，不启动园区光储 Task 3。
- Redis 与 MQTT 的容器、数据和 volumes 均未修改；MQTT health 状态不属于本阶段验收范围。

## 运行环境

- 数据库容器：`campusenergysystem-db-1`，TimescaleDB/PostgreSQL 14 服务健康。
- Python：`/Users/todo/CampusEnergySystem/venv/bin/python`。当前工作树没有独立 `venv`，因此命令通过共享项目虚拟环境执行；质量脚本通过将该虚拟环境置于 `PATH` 首位执行。
- 开发数据库：`campus_energy`；其数据已由用户明确确认可丢弃。

在仓库工作树根目录执行验收前，统一设置以下可复制环境：

```bash
export PATH=/Users/todo/CampusEnergySystem/venv/bin:$PATH
export DATABASE_URL=postgresql://admin:password123@localhost:5432/campus_energy
export MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres
export DB_AUTO_CREATE_TABLES=False
export DB_RUNTIME_SCHEMA_SYNC=False
export PYTHONPYCACHEPREFIX=/tmp/phase2a-pycache
```

其中 `MIGRATION_ADMIN_URL` 只供三个固定临时数据库的三路径验证使用；`DATABASE_URL` 指向已获用户批准可重建的开发数据库。上述凭据为本地 Docker 开发环境固定值，不适用于生产环境。

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
python scripts/python/verify_postgres_migrations.py \
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
python -m alembic upgrade head
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
python -c "from app.core.database import init_db; init_db()"
```

结果：退出 `0`。执行后仍为 628 个对象，SHA-256 不变，证明 `init_db()` 未创建表、补字段、补索引或执行 hypertable DDL。

## 完整回归与质量门禁

以下命令均在“运行环境”代码块的 `export` 前置条件下执行：

| 门禁 | 结果 |
| --- | --- |
| `python -m pytest -q` | `727 passed, 2 skipped, 5 warnings` |
| `bash ./scripts/shell/run_backend_coverage.sh` | `727 passed, 2 skipped, 5 warnings`；总覆盖率 74%，高于 57% 门槛 |
| `python scripts/python/check_ruff_regressions.py` | 通过；Ruff 基线为 158 条 |
| `python -m compileall -q app tests scripts/python migrations` | 通过；使用 `PYTHONPYCACHEPREFIX=/tmp/phase2a-pycache` 避免写入工作区外的 macOS 缓存目录 |
| `git diff --check` | 通过 |

Ruff 基线由 168 条缩减为 158 条。严格集合比较结果为：新增 0 条、删除 10 条、其余 158 条内容和计数完全不变；本次没有扩大忽略范围或引入新债务。

## 首次环境失败与纠正

这些失败均发生在运行环境解析或缓存写入层，不是代码、测试断言或迁移执行失败：

| 首次现象 | 原因 | 纠正动作 | 最终结果 |
| --- | --- | --- | --- |
| 裸 `python -m pytest ...` 退出 `127` | 当前 shell 没有 `python` 命令 | 将 `/Users/todo/CampusEnergySystem/venv/bin` 放到 `PATH` 首位 | focused gate 最终 `89 passed, 2 skipped, 3 warnings` |
| coverage 首次解析到系统 Python，缺少 `coverage` | 工作树没有本地 `venv`，脚本回退到 PATH 中的 `python3` | 使用上述 `export PATH=...`，使脚本的 `python3` 解析到共享项目虚拟环境 | coverage 测试 `727 passed, 2 skipped, 5 warnings`，覆盖率 74% |
| `compileall` 首次因默认 macOS cache 目录无写权限失败 | 字节码默认写入工作树外的 `~/Library/Caches/com.apple.python/...` | 设置 `PYTHONPYCACHEPREFIX=/tmp/phase2a-pycache` | `compileall` 退出 `0` |

纠正后所有必需门禁均已重跑并通过；没有为解决这些环境问题修改生产代码或迁移文件。

## CI 配置验证边界

- CI workflow 配置已通过本地契约测试及 YAML/Compose 配置解析；契约确认 workflow 的 service image 固定为 `timescale/timescaledb:2.17.2-pg14`。
- 本地真实三路径运行在现有 `timescale/timescaledb:latest-pg14` 开发容器上并通过；这不能替代固定 2.17.2 镜像在远端 workflow 中的实际运行证据。
- workflow 中的迁移步骤无 `continue-on-error`，配置语义为失败即阻断。
- 远端 GitHub Actions 本轮未实际运行，因此本记录不声称远端 CI 已绿；后续推送后仍需以远端运行结果作为仓库托管环境证据。
- 提交 `2c738e61` 在写入 Task 8 验收文档的同时同步更新了 Ruff 质量 baseline（纯删除 10 条已修复 finding）；本次后续提交只补充可复现证据与边界表述，不改写该历史提交。

## 警告与范围说明

- 测试警告包括：共享 Python 使用 LibreSSL 2.8.3 触发 urllib3 `NotOpenSSLWarning`；默认 `SECRET_KEY` 触发开发环境安全提示。
- 这些警告未影响迁移、结构校验、启动只校验或测试结果；生产环境仍必须提供非默认 `SECRET_KEY`。
- MQTT 容器当前 health 状态及其修复不在阶段 2A 范围内；本轮未操作 MQTT。
- Redis、readiness、rate limit、部署顺序和储能持久化均未扩入本轮。

## 最终判断与交接

- Task 8：通过。
- 阶段 2A 的迁移底座验收证据已完整；Task 9 仍需执行主主题交还、daily 完成快照和储能 revision 契约更新。
- 下一角色：规则/验收执行 Task 9。Task 9 完成前，园区光储 Task 3 继续保持暂停。
