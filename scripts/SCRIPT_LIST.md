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
| `restore_drill.sh` | 执行备份恢复演练并验证恢复结果。 |

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
| `release_readiness.sh` | 发布前总检查。 |
| `render_alertmanager_config.sh` | 渲染 Alertmanager 配置。 |
| `setup_mqtt_auth.sh` | 配置 MQTT 认证用户与密码文件。 |
| `rollback_prod.sh` | 使用备份执行生产回滚。 |

## Python 脚本

### 初始化与管理

| 脚本 | 作用 |
|------|------|
| `init_complete_system.py` | 初始化完整演示/开发系统数据。 |
| `create_admin.py` | 创建管理员账号。 |
| `check_config.py` | 检查环境配置和连接状态。 |
| `check_production_readiness.py` | 检查生产环境配置是否满足上线要求。 |
| `send_test_alert.py` | 发送测试告警验证通知通道。 |
| `evaluate_capacity_baseline.py` | 校验压测结果是否达到试点阈值。 |
| `replay_mqtt_failures.py` | 重放 MQTT 失败/死信记录。 |
| `generate_prod_secrets.py` | 生成生产环境密钥片段。 |

### 演示脚本

| 脚本 | 作用 |
|------|------|

### 模拟、网关与压测

| 脚本 | 作用 |
|------|------|
| `simulator_unified.py` | 统一设备模拟器。 |
| `device_gateway.py` | 真实设备网关采集器。 |
| `stress_test.py` | 压力测试。 |

### MQTT/协议调试

| 脚本 | 作用 |
|------|------|
| `mqtt_send_test.py` | 发送 MQTT 测试消息。 |
| `send_svg_telemetry.py` | 向 SVG 设备发送模拟 MQTT 遥测数据。 |
| `send_capacitor_bank_telemetry.py` | 向电容补偿控制器发送可按场景和状态位控制的模拟 MQTT 遥测数据，并可监听 `start/stop/write_parameter` 控制指令回放最新快照。 |

### 串口演示工具

| 脚本 | 作用 |
|------|------|
## 已归档脚本

| 脚本 | 作用 |
|------|------|
| `archive/shell/start_frontend.sh` | 旧前端启动包装脚本，已从正式入口降级，统一改用 `cd frontend && npm run dev`。 |
| `archive/shell/uninstall_local_services.sh` | 历史本机服务卸载脚本，当前默认使用 Docker 中间件，不再作为主入口。 |
| `archive/python/rebuild_database.py` | 历史数据库重建脚本，已从正式入口降级，当前应优先使用 Alembic 迁移与初始化脚本。 |
| `archive/python/demo_unified_system.py` | 历史整套系统演示脚本。 |
| `archive/python/demo_device_group.py` | 历史设备分组演示脚本。 |
| `archive/python/demo_location.py` | 历史位置管理演示脚本。 |
| `archive/python/demo_maintenance.py` | 历史维护管理演示脚本。 |
| `archive/python/mqtt_subscriber_template.py` | 历史 MQTT 订阅模板。 |
| `archive/python/test_http_device.py` | 历史 HTTP 设备联调脚本。 |
| `archive/python/test_modbus_tcp.py` | 历史 Modbus TCP 联调脚本。 |
| `archive/python/test_serial_port.py` | 历史串口联调脚本。 |
| `archive/python/serial_device_sim.py` | 历史串口设备模拟脚本。 |
| `archive/python/serial_gateway_demo.py` | 历史串口网关演示脚本。 |
| `archive/python/serial_pair_demo.py` | 历史串口配对/联调演示脚本。 |

## 统计

| 类型 | 数量 |
|------|------|
| Shell | 27 |
| Python | 15 |
| Archive | 14 |
| 合计 | 56 |

## 与 bin 的关系

`bin/` 是快捷入口层，`scripts/` 是正式实现层和完整工具集。

| bin 脚本 | 对应脚本 | 说明 |
|---------|----------|------|
| `fast_start.sh` | `scripts/shell/start.sh` | 用途接近，但 `bin` 更偏快捷入口。 |
| `fast_start_dev.sh` | `scripts/shell/start_dev_env.sh` | `bin` 会继续编排本地前后端启动。 |
| `run_simulator.sh` | `scripts/python/simulator_unified.py` | `bin` 版在容器内运行模拟器。 |
