# scripts 目录说明

`scripts/` 是项目的“完整工具集”，和 [bin/](/Users/todo/MineEnergySystem/bin/README.md) 的快捷入口不同，这里放的是更细分、更适合运维、初始化、接入调试和排查的脚本。

## 目录职责

- `shell/`：启动、停止、检查、备份、恢复、清理、部署
- `python/`：系统初始化、演示数据、模拟器、网关、协议调试、压力测试
- `QUICK_REFERENCE.md`：常用命令速查
- `SCRIPT_LIST.md`：完整脚本清单

## 当前规模

- Shell 脚本：22 个
- Python 脚本：22 个

## 推荐使用方式

### 1. 先看快速参考

- [QUICK_REFERENCE.md](/Users/todo/MineEnergySystem/scripts/QUICK_REFERENCE.md)

适合“我现在要做一件事，直接给我命令”。

### 2. 再看完整清单

- [SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)

适合“我想知道这个目录里到底都有什么，不重复地看一遍”。

### 3. 需要细节时看子目录文档

- [shell/README.md](/Users/todo/MineEnergySystem/scripts/shell/README.md)
- [python/README.md](/Users/todo/MineEnergySystem/scripts/python/README.md)

## 最常用脚本

### Shell

- [start.sh](/Users/todo/MineEnergySystem/scripts/shell/start.sh)：启动整套 Docker 服务
- [start_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/start_dev_env.sh)：启动开发环境中间件
- [start_frontend.sh](/Users/todo/MineEnergySystem/scripts/shell/start_frontend.sh)：启动前端开发服务器
- [status.sh](/Users/todo/MineEnergySystem/scripts/shell/status.sh)：查看系统状态
- [test_health.sh](/Users/todo/MineEnergySystem/scripts/shell/test_health.sh)：健康检查
- [pilot_smoke_test.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_smoke_test.sh)：试点联调冒烟检查
- [pilot_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_readiness.sh)：试点前总检查并输出证据目录
- [pilot_drill.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_drill.sh)：串联 readiness、容量基线和冒烟
- [load_baseline.sh](/Users/todo/MineEnergySystem/scripts/shell/load_baseline.sh)：生成容量基线和 Markdown 验收摘要

### Python

- [init_complete_system.py](/Users/todo/MineEnergySystem/scripts/python/init_complete_system.py)：初始化整套演示/开发数据
- [create_admin.py](/Users/todo/MineEnergySystem/scripts/python/create_admin.py)：创建管理员
- [simulator_unified.py](/Users/todo/MineEnergySystem/scripts/python/simulator_unified.py)：统一设备模拟器
- [device_gateway.py](/Users/todo/MineEnergySystem/scripts/python/device_gateway.py)：真实设备网关采集器
- [check_config.py](/Users/todo/MineEnergySystem/scripts/python/check_config.py)：配置检查
- [send_test_alert.py](/Users/todo/MineEnergySystem/scripts/python/send_test_alert.py)：验证告警通知通道

## 脚本分类

### 服务管理

- 启动/停止：`start.sh`、`stop.sh`、`start_dev_env.sh`、`stop_dev_env.sh`
- 局部操作：`restart_backend.sh`、`rebuild_backend.sh`、`start_frontend.sh`

### 状态与排查

- `status.sh`
- `test_health.sh`
- `pilot_smoke_test.sh`
- `pilot_readiness.sh`
- `pilot_drill.sh`
- `check_websocket.sh`
- `check_mac_env.sh`
- `check_config.py`
- `stress_test.py`
- `evaluate_capacity_baseline.py`

### 数据与环境维护

- `backup.sh`
- `restore.sh`
- `cleanup_logs.sh`
- `cleanup_docker.sh`
- `fix_venv.sh`
- `install_dependencies.sh`
- `rebuild_database.py`

### 初始化与演示

- `init_complete_system.py`
- `create_admin.py`
- `demo_unified_system.py`
- `demo_device_group.py`
- `demo_location.py`
- `demo_maintenance.py`

### 设备接入与协议调试

- `device_gateway.py`
- `send_test_alert.py`
- `mqtt_send_test.py`
- `mqtt_subscriber_template.py`
- `test_http_device.py`
- `test_modbus_tcp.py`
- `test_serial_port.py`
- `serial_device_sim.py`
- `serial_gateway_demo.py`
- `serial_pair_demo.py`

### 模拟与训练

- `simulator_unified.py`
- `generate_training_data.py`

## 与 bin 的关系

`bin/` 是最常用命令的短入口，`scripts/` 是完整工具集。

例如：

- [bin/fast_start.sh](/Users/todo/MineEnergySystem/bin/fast_start.sh) 对应 [scripts/shell/start.sh](/Users/todo/MineEnergySystem/scripts/shell/start.sh)
- [bin/run_simulator.sh](/Users/todo/MineEnergySystem/bin/run_simulator.sh) 对应 [scripts/python/simulator_unified.py](/Users/todo/MineEnergySystem/scripts/python/simulator_unified.py)

## 整理原则

这个目录后续建议继续保持：

- 不移动现有脚本路径，避免打断文档和使用习惯
- 新脚本先补进 `SCRIPT_LIST.md`
- 生成文件不留在目录里，比如 `__pycache__`、`.DS_Store`
