# 脚本清单

以下为 `scripts/` 下脚本的完整清单，每个脚本只列一次。

## Shell 脚本

### 服务启停

| 脚本 | 作用 |
|------|------|
| `start.sh` | 启动整套 Docker 服务，适合默认/完整环境。 |
| `start_dev_env.sh` | 启动开发环境中间件，不启动本地后端和前端。 |
| `stop.sh` | 停止整套 Docker 服务。 |
| `stop_dev_env.sh` | 停止开发环境中间件。 |
| `restart_backend.sh` | 只重启后端容器。 |
| `rebuild_backend.sh` | 重建并重启后端容器。 |
| `start_frontend.sh` | 启动前端 Vite 开发服务器。 |

### 状态检查

| 脚本 | 作用 |
|------|------|
| `status.sh` | 查看容器状态、端口映射和整体运行情况。 |
| `test_health.sh` | 调用后端健康检查接口。 |
| `pilot_smoke_test.sh` | 试点部署后的冒烟验收。 |
| `pilot_readiness.sh` | 执行试点前总检查并归档证据。 |
| `pilot_drill.sh` | 串联 readiness、容量基线和冒烟验收。 |
| `load_baseline.sh` | 生成后端容量基线并输出 Markdown 验收摘要。 |
| `check_websocket.sh` | 检查 WebSocket 链路。 |
| `check_mac_env.sh` | 检查 macOS 本地开发环境。 |

### 维护与部署

| 脚本 | 作用 |
|------|------|
| `backup.sh` | 备份数据库。 |
| `restore.sh` | 从备份恢复数据库。 |
| `cleanup_logs.sh` | 清理日志文件。 |
| `cleanup_docker.sh` | 清理 Docker 资源。 |
| `fix_venv.sh` | 修复 Python 虚拟环境。 |
| `install_dependencies.sh` | 安装本地依赖。 |
| `deploy_prod.sh` | 执行生产部署流程。 |
| `uninstall_local_services.sh` | 卸载本机安装的相关服务。 |

## Python 脚本

### 初始化与管理

| 脚本 | 作用 |
|------|------|
| `init_complete_system.py` | 初始化完整演示/开发系统数据。 |
| `create_admin.py` | 创建管理员账号。 |
| `rebuild_database.py` | 重建数据库，危险操作。 |
| `check_config.py` | 检查环境配置和连接状态。 |
| `send_test_alert.py` | 发送测试告警验证通知通道。 |
| `evaluate_capacity_baseline.py` | 校验压测结果是否达到试点阈值。 |

### 演示脚本

| 脚本 | 作用 |
|------|------|
| `demo_unified_system.py` | 演示整套业务能力。 |
| `demo_device_group.py` | 演示设备分组功能。 |
| `demo_location.py` | 演示位置管理功能。 |
| `demo_maintenance.py` | 演示维护管理功能。 |

### 模拟、网关与训练

| 脚本 | 作用 |
|------|------|
| `simulator_unified.py` | 统一设备模拟器。 |
| `device_gateway.py` | 真实设备网关采集器。 |
| `generate_training_data.py` | 生成模型训练数据。 |
| `stress_test.py` | 压力测试。 |

### MQTT/协议调试

| 脚本 | 作用 |
|------|------|
| `mqtt_send_test.py` | 发送 MQTT 测试消息。 |
| `mqtt_subscriber_template.py` | MQTT 订阅模板。 |
| `test_http_device.py` | 测试 HTTP 设备接口。 |
| `test_modbus_tcp.py` | 测试 Modbus TCP 设备连接。 |
| `test_serial_port.py` | 测试串口可用性。 |

### 串口演示工具

| 脚本 | 作用 |
|------|------|
| `serial_device_sim.py` | 串口设备模拟。 |
| `serial_gateway_demo.py` | 串口网关演示。 |
| `serial_pair_demo.py` | 串口配对/联调演示。 |

## 统计

| 类型 | 数量 |
|------|------|
| Shell | 22 |
| Python | 22 |
| 合计 | 44 |

## 与 bin 的关系

`bin/` 是快捷入口，`scripts/` 是完整工具集。

| bin 脚本 | 对应脚本 | 说明 |
|---------|----------|------|
| `fast_start.sh` | `scripts/shell/start.sh` | 用途接近，但 `bin` 更偏快捷入口。 |
| `fast_start_dev.sh` | `scripts/shell/start_dev_env.sh` | `bin` 会继续编排本地前后端启动。 |
| `run_simulator.sh` | `scripts/python/simulator_unified.py` | `bin` 版在容器内运行模拟器。 |
