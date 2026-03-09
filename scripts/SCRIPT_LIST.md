# 脚本清单（每个脚本仅列一次）

以下为 `scripts/` 下全部脚本的**唯一清单**，按类型与用途分组，无重复。

---

## Shell 脚本（`scripts/shell/`）

### 服务启停

| 脚本 | 作用 |
|------|------|
| **start.sh** | 使用 Docker Compose 启动整套系统（数据库、Redis、MQTT、后端），检查 Docker、端口与目录，适用于生产或一键启动。 |
| **start_dev_env.sh** | 仅启动开发用中间件（数据库、Redis、MQTT），不启动后端容器，便于本地跑 `run.py` 调试。 |
| **stop.sh** | 停止所有 Docker 容器，不删除数据卷，用于临时停机。 |
| **stop_dev_env.sh** | 仅停止开发环境中的中间件容器。 |
| **restart_backend.sh** | 仅重启后端容器，不动数据库/Redis/MQTT，适合代码更新后快速生效。 |
| **rebuild_backend.sh** | 重新构建后端镜像并启动，适用于修改 `requirements.txt` 或 Dockerfile 后。 |
| **start_frontend.sh** | 启动前端开发服务器（Vite），检查 Node 与依赖，输出访问地址。 |

### 状态检查

| 脚本 | 作用 |
|------|------|
| **status.sh** | 列出所有相关容器的运行状态、健康检查结果与端口映射，便于一眼查看系统是否正常。 |
| **test_health.sh** | 请求后端健康检查接口（存活、就绪、系统健康等），用彩色输出判断服务是否可用。 |
| **check_websocket.sh** | 测试 WebSocket 连接与实时推送是否正常。 |
| **check_mac_env.sh** | 检查 macOS 上 Docker、Python、Node、端口占用与必要目录，用于首次部署或环境排查。 |

### 维护工具

| 脚本 | 作用 |
|------|------|
| **backup.sh** | 备份数据库（PostgreSQL/TimescaleDB），压缩并带时间戳保存到 `backups/`，适合定期或上线前备份。 |
| **restore.sh** | 从指定备份文件恢复数据库，会覆盖当前数据，使用前需确认。 |
| **cleanup_logs.sh** | 清理过期日志文件，释放磁盘，可配置保留天数。 |
| **cleanup_docker.sh** | 清理未使用的 Docker 镜像、已停容器、未使用网络与构建缓存。 |
| **fix_venv.sh** | 重建 Python 虚拟环境并重装依赖，用于 venv 损坏或依赖冲突。 |
| **install_dependencies.sh** | 安装系统级与 Python 依赖，检查系统类型与版本，用于首次环境搭建。 |

### 部署工具

| 脚本 | 作用 |
|------|------|
| **deploy_prod.sh** | 生产环境部署流程：检查、拉代码、构建、备份、启服、健康检查，失败可回滚。 |
| **uninstall_local_services.sh** | 卸载本机安装的 PostgreSQL/Redis 等本地服务，便于从本地迁移到 Docker。 |

---

## Python 脚本（`scripts/python/`）

### 系统初始化与管理

| 脚本 | 作用 |
|------|------|
| **init_complete_system.py** | 一次性初始化完整系统：管理员账号、多种设备、历史能源数据、告警与分组/位置/维护等，适合首次部署或演示环境搭建。 |
| **create_admin.py** | 交互式创建或重置管理员账号（用户名/密码），不涉及其他数据。 |
| **rebuild_database.py** | 删除并重建所有数据库表（危险：清空全部数据），仅用于库结构变更或开发环境重置。 |
| **check_config.py** | 检查环境变量、数据库与 Redis/MQTT 连接、路径等配置，输出可读报告，便于排错。 |

### 功能演示

| 脚本 | 作用 |
|------|------|
| **demo_unified_system.py** | 演示完整系统能力：创建设备、能源数据、告警、查询与报表等，用于培训或验收。 |
| **demo_device_group.py** | 演示设备分组：创建分组、关联设备、分组查询与统计。 |
| **demo_location.py** | 演示位置层级：区域→车间→设备位置，以及设备与位置的关联与树形查询。 |
| **demo_maintenance.py** | 演示维护流程：维护计划、任务执行、记录与状态流转。 |

### 开发与数据工具

| 脚本 | 作用 |
|------|------|
| **simulator_unified.py** | 统一设备模拟器：从数据库读设备列表，按类型生成多能源遥测数据，通过 MQTT 上报到 `mine/telemetry`，支持远程启停控制，用于开发与演示。 |
| **device_gateway.py** | 设备网关：从真实设备（Modbus TCP/RTU、HTTP API 等）定时采集数据并发布到 MQTT `mine/telemetry`，需在脚本内配置 `DEVICE_CONFIG`，用于接入真实电表/水表等。 |
| **generate_training_data.py** | 生成 LSTM 等模型所需的训练用历史能耗数据，可配置时间范围与设备，输出符合训练格式的数据。 |
| **stress_test.py** | 对 API 与数据库做压力测试：并发请求、响应时间、吞吐与错误率，用于性能评估与容量规划。 |

---

## 统计

| 类型 | 数量 |
|------|------|
| Shell | 19 |
| Python | 12 |
| **合计** | **31** |

---

## bin/ 与 scripts/ 的对应关系（是否有重复）

`bin/` 是**快捷入口**，`scripts/` 是**完整工具集**。对应关系如下，**无重复实现**，只有用途重叠时的不同入口。

| bin/ 脚本 | 对应 scripts/ | 关系说明 |
|-----------|----------------|----------|
| **fast_start.sh** | scripts/shell/start.sh | **用途重叠**：都是“启动整套服务”。bin 版优先用镜像缓存（有则 `up -d`，无则 `--build`），启动更快；scripts 版做目录/端口检查并每次 `--build`，更完整。二者选一即可，日常推荐 `bin/fast_start.sh`。 |
| **run_simulator.sh** | scripts/python/simulator_unified.py | **非重复**：bin 脚本只是在**容器内**执行 `simulator_unified.py`（并注入 MQTT/API 环境变量）。本地直接跑模拟器用 `python scripts/python/simulator_unified.py`。 |

**bin 中未实现的脚本**：bin/README 曾提到的 `dev_start.sh`（只启动中间件）**不存在**于 bin/，请直接使用 **scripts/shell/start_dev_env.sh**。

**结论**：scripts 与 bin 之间没有重复的脚本文件；仅“启动服务”有两条路径（bin 快捷 / scripts 完整），可按需选用。

---

## 危险操作提醒

- **rebuild_database.py**：会删除所有数据，使用前务必备份。
- **restore.sh**：会覆盖当前数据库，使用前确认备份文件与环境。

---

**说明**：更细的使用方法、示例命令与故障排查见 [README.md](./README.md)、[python/README.md](./python/README.md)、[shell/README.md](./shell/README.md) 与 [QUICK_REFERENCE.md](./QUICK_REFERENCE.md)。
