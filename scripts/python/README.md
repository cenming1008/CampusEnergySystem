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

这些脚本优先视为正式入口。

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
