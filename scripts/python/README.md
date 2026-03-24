# python 脚本说明

`scripts/python/` 主要放初始化、演示、模拟器、网关和协议调试脚本。

## 当前脚本

### 初始化与管理

- [init_complete_system.py](/Users/todo/MineEnergySystem/scripts/python/init_complete_system.py)：初始化完整系统数据
- [create_admin.py](/Users/todo/MineEnergySystem/scripts/python/create_admin.py)：创建管理员
- [rebuild_database.py](/Users/todo/MineEnergySystem/scripts/python/rebuild_database.py)：重建数据库
- [check_config.py](/Users/todo/MineEnergySystem/scripts/python/check_config.py)：检查配置

### 演示脚本

- [demo_unified_system.py](/Users/todo/MineEnergySystem/scripts/python/demo_unified_system.py)：整套系统演示
- [demo_device_group.py](/Users/todo/MineEnergySystem/scripts/python/demo_device_group.py)：设备分组演示
- [demo_location.py](/Users/todo/MineEnergySystem/scripts/python/demo_location.py)：位置管理演示
- [demo_maintenance.py](/Users/todo/MineEnergySystem/scripts/python/demo_maintenance.py)：维护管理演示

### 模拟、网关与训练

- [simulator_unified.py](/Users/todo/MineEnergySystem/scripts/python/simulator_unified.py)：统一设备模拟器
- [device_gateway.py](/Users/todo/MineEnergySystem/scripts/python/device_gateway.py)：真实设备网关
- [generate_training_data.py](/Users/todo/MineEnergySystem/scripts/python/generate_training_data.py)：生成训练数据
- [stress_test.py](/Users/todo/MineEnergySystem/scripts/python/stress_test.py)：压力测试

### MQTT/协议调试

- [mqtt_send_test.py](/Users/todo/MineEnergySystem/scripts/python/mqtt_send_test.py)：发送 MQTT 测试消息
- [mqtt_subscriber_template.py](/Users/todo/MineEnergySystem/scripts/python/mqtt_subscriber_template.py)：MQTT 订阅模板
- [test_http_device.py](/Users/todo/MineEnergySystem/scripts/python/test_http_device.py)：测试 HTTP 设备
- [test_modbus_tcp.py](/Users/todo/MineEnergySystem/scripts/python/test_modbus_tcp.py)：测试 Modbus TCP 设备
- [test_serial_port.py](/Users/todo/MineEnergySystem/scripts/python/test_serial_port.py)：测试串口

### 串口演示

- [serial_device_sim.py](/Users/todo/MineEnergySystem/scripts/python/serial_device_sim.py)：串口设备模拟
- [serial_gateway_demo.py](/Users/todo/MineEnergySystem/scripts/python/serial_gateway_demo.py)：串口网关演示
- [serial_pair_demo.py](/Users/todo/MineEnergySystem/scripts/python/serial_pair_demo.py)：串口联调演示

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
```

## 使用建议

- 改真实设备接入时，优先配 [config/gateway_devices.json](/Users/todo/MineEnergySystem/config/gateway_devices.json)
- 运行危险脚本前先确认数据是否需要备份，比如 `rebuild_database.py`
- 详细总览见 [scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)
