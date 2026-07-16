# python 脚本说明

`scripts/python/` 主要放仓库级 Python 工具。当前目录以正式工具和仍在使用的联调脚本为主。

## 使用优先级

- 正式入口：初始化、配置检查、生产检查
- 辅助入口：告警联调、MQTT 重放、压力测试

## 当前脚本

### 初始化与管理

- [init_complete_system.py](/Users/todo/CampusEnergySystem/scripts/python/init_complete_system.py)：初始化完整系统数据
- [create_admin.py](/Users/todo/CampusEnergySystem/scripts/python/create_admin.py)：创建管理员
- [check_config.py](/Users/todo/CampusEnergySystem/scripts/python/check_config.py)：检查配置
- [check_production_readiness.py](/Users/todo/CampusEnergySystem/scripts/python/check_production_readiness.py)：检查生产环境配置是否满足上线要求
- [check_ruff_regressions.py](/Users/todo/CampusEnergySystem/scripts/python/check_ruff_regressions.py)：维护并校验 Ruff 历史债务基线
- [evaluate_capacity_baseline.py](/Users/todo/CampusEnergySystem/scripts/python/evaluate_capacity_baseline.py)：校验压测结果是否满足试点阈值
- [replay_mqtt_failures.py](/Users/todo/CampusEnergySystem/scripts/python/replay_mqtt_failures.py)：重放 MQTT 失败/死信记录
- [run_mqtt_ingest_worker.py](/Users/todo/CampusEnergySystem/scripts/python/run_mqtt_ingest_worker.py)：MQTT 入站采集 worker 入口
- [generate_prod_secrets.py](/Users/todo/CampusEnergySystem/scripts/python/generate_prod_secrets.py)：生成生产环境密钥片段
- [send_test_alert.py](/Users/todo/CampusEnergySystem/scripts/python/send_test_alert.py)：验证告警通知通道
- [send_capacitor_bank_harmonic_uat_payloads.py](/Users/todo/CampusEnergySystem/scripts/python/send_capacitor_bank_harmonic_uat_payloads.py)：生成或发送电容补偿控制器 2~31 次逐次谐波联调验收 payload
- [migration_schema.py](/Users/todo/CampusEnergySystem/scripts/python/migration_schema.py)：提供迁移临时库白名单和规范化 schema 指纹核心，仅供迁移验证工具复用
- [verify_postgres_migrations.py](/Users/todo/CampusEnergySystem/scripts/python/verify_postgres_migrations.py)：在三个固定临时库验证 Alembic online、offline 与 roundtrip 路径

这些脚本优先视为正式入口。

### PostgreSQL 迁移三路径验收

该验收要求本机运行 PostgreSQL 14 对应的 TimescaleDB，并由管理员连接串显式授权。验证器只会创建或删除以下三个精确名称：

- `ces_migration_fresh`
- `ces_migration_offline`
- `ces_migration_roundtrip`

本地三路径证据当前已在 TimescaleDB `2.19.3`（PostgreSQL 14）通过；这说明静态基线与当前开发环境兼容，不替代正式版本门禁。Task 7 必须把 CI 服务固定为 `timescale/timescaledb:2.17.2-pg14`，并在该固定版本重新执行同一组三路径验收，作为正式兼容性证据。

`campus_energy` 永远不是验证器目标；不要把它或其他业务库名称传给验证器。执行正式验收：

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
  /Users/todo/CampusEnergySystem/venv/bin/python \
  scripts/python/verify_postgres_migrations.py \
  --json-output /tmp/phase2a-migration-result.json

MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
  /Users/todo/CampusEnergySystem/venv/bin/python -m pytest -q \
  tests/test_postgres_migration_paths.py
```

验证器先通过 PostgreSQL advisory lock 串行化整个生命周期，再依次执行 fresh online upgrade、offline SQL 生成并应用、upgrade-downgrade-upgrade，比较三份最终指纹。第二个并发运行会立即拒绝，不等待，也不会创建、删除或终止临时库连接。全部成功时会自动删除三个临时库；迁移、指纹或比较失败时不自动清理，以保留现场。使用 `--keep-success` 可在成功后也保留临时库。诊断完成后只用以下命令清理固定临时库：

```bash
MIGRATION_ADMIN_URL=postgresql://admin:password123@localhost:5432/postgres \
  /Users/todo/CampusEnergySystem/venv/bin/python \
  scripts/python/verify_postgres_migrations.py --cleanup
```

`--cleanup` 同样先获取这把锁；若另一轮验证正在运行，它会立即拒绝，不会执行部分清理。若已取得锁但某个清理步骤自身失败，工具仍会 best-effort 尝试另外两个固定库，因此可能只剩部分临时库；按错误中列出的固定库名处理后再次运行 `--cleanup`。不要用此工具重建 `campus_energy`。

### 压测

- [stress_test.py](/Users/todo/CampusEnergySystem/scripts/python/stress_test.py)：压力测试

### MQTT/协议调试

- [send_capacitor_bank_harmonic_uat_payloads.py](/Users/todo/CampusEnergySystem/scripts/python/send_capacitor_bank_harmonic_uat_payloads.py)：逐次谐波准真实 payload 验收，可用 `--print-only` 先打印 topic 与 JSON

本地设备采集/网关脚本已移除，真实联调以 Windows 工控机运行脚本和平台 MQTT 接入记录为准。

## 最常用组合

```bash
# 初始化系统
python scripts/python/init_complete_system.py

# 创建管理员
python scripts/python/create_admin.py

# 容量基线判定
python scripts/python/evaluate_capacity_baseline.py --report artifacts/load/health_live.json --min-rps 20 --max-p95-ms 200 --min-success-rate 99 --expect-status-code 200

# 校验 Ruff 历史债务基线
./venv/bin/python scripts/python/check_ruff_regressions.py

# 首次创建基线，或在历史债务收缩后同步基线
./venv/bin/python scripts/python/check_ruff_regressions.py --write-baseline
```

## 使用建议

- `--write-baseline` 只允许首次创建或收缩现有基线；发现新增 finding 或 count 时会拒绝写入。基线 JSON 的手工修改仍必须经过 code review。
- 改真实设备接入时，优先调整设备侧网关或现场工控机工程；系统侧只约定 MQTT topic / payload、字段归一和入库规则
- 当前数据库结构应优先通过 `python -m alembic upgrade head` 维护，不再把重建数据库当正式流程
- 详细总览见 [scripts/README.md](/Users/todo/CampusEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/CampusEnergySystem/scripts/SCRIPT_LIST.md)
