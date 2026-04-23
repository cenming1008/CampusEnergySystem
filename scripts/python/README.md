# python 脚本说明

`scripts/python/` 主要放仓库级 Python 工具。当前目录以正式工具和仍在使用的联调脚本为主，低频演示/一次性联调脚本已迁入 `scripts/archive/python/`。

## 使用优先级

- 正式入口：初始化、配置检查、模拟器、网关、生产检查
- 辅助入口：演示脚本、协议调试脚本、串口联调脚本
- 历史脚本：进入 `scripts/archive/python/`

## 当前脚本

### 初始化与管理

- [init_complete_system.py](/Users/todo/MineEnergySystem/scripts/python/init_complete_system.py)：初始化完整系统数据
- [create_admin.py](/Users/todo/MineEnergySystem/scripts/python/create_admin.py)：创建管理员
- [check_config.py](/Users/todo/MineEnergySystem/scripts/python/check_config.py)：检查配置
- [evaluate_capacity_baseline.py](/Users/todo/MineEnergySystem/scripts/python/evaluate_capacity_baseline.py)：校验压测结果是否满足试点阈值
- [replay_mqtt_failures.py](/Users/todo/MineEnergySystem/scripts/python/replay_mqtt_failures.py)：重放 MQTT 失败/死信记录
- [generate_prod_secrets.py](/Users/todo/MineEnergySystem/scripts/python/generate_prod_secrets.py)：生成生产环境密钥片段
- [send_test_alert.py](/Users/todo/MineEnergySystem/scripts/python/send_test_alert.py)：验证告警通知通道

这些脚本优先视为正式入口。

### 已归档演示脚本

- [demo_unified_system.py](/Users/todo/CampusEnergySystem/scripts/archive/python/demo_unified_system.py)：整套系统演示
- [demo_device_group.py](/Users/todo/CampusEnergySystem/scripts/archive/python/demo_device_group.py)：设备分组演示
- [demo_location.py](/Users/todo/CampusEnergySystem/scripts/archive/python/demo_location.py)：位置管理演示
- [demo_maintenance.py](/Users/todo/CampusEnergySystem/scripts/archive/python/demo_maintenance.py)：维护管理演示

这些脚本已归档，不再作为当前目录第一层入口。

### 模拟、网关与压测

- [simulator_unified.py](/Users/todo/MineEnergySystem/scripts/python/simulator_unified.py)：统一设备模拟器
- [device_gateway.py](/Users/todo/MineEnergySystem/scripts/python/device_gateway.py)：真实设备网关
- [stress_test.py](/Users/todo/MineEnergySystem/scripts/python/stress_test.py)：压力测试

### MQTT/协议调试

- [mqtt_send_test.py](/Users/todo/MineEnergySystem/scripts/python/mqtt_send_test.py)：发送 MQTT 测试消息
- [send_svg_telemetry.py](/Users/todo/CampusEnergySystem/scripts/python/send_svg_telemetry.py)：向 SVG 设备发送模拟 MQTT 遥测数据
- [send_capacitor_bank_telemetry.py](/Users/todo/CampusEnergySystem/scripts/python/send_capacitor_bank_telemetry.py)：向电容补偿控制器发送模拟 MQTT 遥测数据

低频协议模板和一次性联调脚本已归档：

- [mqtt_subscriber_template.py](/Users/todo/CampusEnergySystem/scripts/archive/python/mqtt_subscriber_template.py)
- [test_http_device.py](/Users/todo/CampusEnergySystem/scripts/archive/python/test_http_device.py)
- [test_modbus_tcp.py](/Users/todo/CampusEnergySystem/scripts/archive/python/test_modbus_tcp.py)
- [test_serial_port.py](/Users/todo/CampusEnergySystem/scripts/archive/python/test_serial_port.py)

这些脚本优先视为联调/验证工具，而不是长期正式入口。

### 已归档串口演示

- [serial_device_sim.py](/Users/todo/CampusEnergySystem/scripts/archive/python/serial_device_sim.py)：串口设备模拟
- [serial_gateway_demo.py](/Users/todo/CampusEnergySystem/scripts/archive/python/serial_gateway_demo.py)：串口网关演示
- [serial_pair_demo.py](/Users/todo/CampusEnergySystem/scripts/archive/python/serial_pair_demo.py)：串口联调演示

这些脚本已归档，保留给专项演示和接入排查使用。

## 最常用组合

```bash
# 初始化系统
python scripts/python/init_complete_system.py

# 创建管理员
python scripts/python/create_admin.py

# 模拟数据
python scripts/python/simulator_unified.py

# 真实设备接入
python scripts/python/device_gateway.py

# 容量基线判定
python scripts/python/evaluate_capacity_baseline.py --report artifacts/load/health_live.json --min-rps 20 --max-p95-ms 200 --min-success-rate 99 --expect-status-code 200
```

## 使用建议

- 改真实设备接入时，优先配 [config/gateway_devices.json](/Users/todo/MineEnergySystem/config/gateway_devices.json)
- 当前数据库结构应优先通过 `python -m alembic upgrade head` 维护，不再把重建数据库当正式流程
- 历史脚本 [archive/python/rebuild_database.py](/Users/todo/CampusEnergySystem/scripts/archive/python/rebuild_database.py) 已降级归档，仅供历史排查参考
- 详细总览见 [scripts/README.md](/Users/todo/CampusEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/CampusEnergySystem/scripts/SCRIPT_LIST.md)
