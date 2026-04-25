# 脚本清单

以下为 `scripts/` 下脚本的完整清单，每个脚本只列一次。

## Shell 脚本

### 状态检查

| 脚本 | 作用 |
|------|------|
| `status.sh` | 查看容器状态、端口映射和整体运行情况。 |
| `test_health.sh` | 调用后端健康检查接口。 |

### 维护与部署

| 脚本 | 作用 |
|------|------|
| `backup.sh` | 备份数据库。 |
| `restore.sh` | 从备份恢复数据库。 |
| `install_dependencies.sh` | 安装本地依赖。 |
| `deploy_prod.sh` | 执行生产部署流程。 |
| `release_readiness.sh` | 发布前总检查。 |
| `run_backend_coverage.sh` | 运行后端覆盖率检查。 |
| `render_alertmanager_config.sh` | 渲染 Alertmanager 配置。 |
| `setup_mqtt_auth.sh` | 配置 MQTT 认证用户与密码文件。 |

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
| `run_mqtt_ingest_worker.py` | MQTT 入站采集 worker 入口。 |
| `generate_prod_secrets.py` | 生成生产环境密钥片段。 |

### 压测

| 脚本 | 作用 |
|------|------|
| `stress_test.py` | 压力测试。 |

## 统计

| 类型 | 数量 |
|------|------|
| Shell | 10 |
| Python | 10 |
| 合计 | 20 |

## 与 bin 的关系

`bin/` 是快捷入口层，`scripts/` 是正式实现层和完整工具集。

| bin 脚本 | 对应脚本 | 说明 |
|---------|----------|------|
| `fast_start.sh` | `docker-compose.prod.yml` | 生产快速启动入口。 |
| `stop_prod.sh` | `docker-compose.prod.yml` | 生产快速停止入口，不删除挂载数据。 |
| `fast_start_dev.sh` | `docker-compose.dev.yml` | 开发快速启动入口。 |
| `stop_dev.sh` | `docker-compose.dev.yml` | 开发快速停止入口。 |
