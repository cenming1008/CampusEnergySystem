# shell 脚本说明

`scripts/shell/` 主要放仓库级 shell 正式实现。当前目录中以正式入口、上线检查和少量环境脚本为主，推荐按职责理解。

## 使用优先级

- 正式入口：启动、停止、状态、健康检查、备份恢复、部署发布
- 辅助入口：部署与发布检查
- 历史脚本：进入 `scripts/archive/shell/`

## 当前脚本

### 服务启停

- [start.sh](/Users/todo/MineEnergySystem/scripts/shell/start.sh)：启动整套 Docker 服务
- [start_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/start_dev_env.sh)：启动开发环境中间件
- [stop.sh](/Users/todo/MineEnergySystem/scripts/shell/stop.sh)：停止整套 Docker 服务
- [stop_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/stop_dev_env.sh)：停止开发环境中间件

### 状态检查

- [status.sh](/Users/todo/MineEnergySystem/scripts/shell/status.sh)：查看系统状态
- [test_health.sh](/Users/todo/MineEnergySystem/scripts/shell/test_health.sh)：健康检查

### 维护与部署

- [backup.sh](/Users/todo/MineEnergySystem/scripts/shell/backup.sh)：备份数据库
- [restore.sh](/Users/todo/MineEnergySystem/scripts/shell/restore.sh)：恢复数据库
- [install_dependencies.sh](/Users/todo/MineEnergySystem/scripts/shell/install_dependencies.sh)：安装依赖
- [deploy_prod.sh](/Users/todo/MineEnergySystem/scripts/shell/deploy_prod.sh)：生产部署
- [release_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/release_readiness.sh)：发布前总检查
- [render_alertmanager_config.sh](/Users/todo/MineEnergySystem/scripts/shell/render_alertmanager_config.sh)：渲染 Alertmanager 配置
- [setup_mqtt_auth.sh](/Users/todo/MineEnergySystem/scripts/shell/setup_mqtt_auth.sh)：配置 MQTT 认证
- [archive/shell/uninstall_local_services.sh](/Users/todo/CampusEnergySystem/scripts/archive/shell/uninstall_local_services.sh)：历史本机服务卸载脚本，已归档

## 最常用组合

```bash
# 默认启动
./scripts/shell/start.sh

# 开发模式
./scripts/shell/start_dev_env.sh
cd frontend && npm run dev

# 状态检查
./scripts/shell/status.sh
./scripts/shell/test_health.sh
```

## 使用建议

- 日常快速启动优先看 [bin/README.md](/Users/todo/CampusEnergySystem/bin/README.md)
- 需要完整能力时使用这里的脚本
- 详细总览见 [scripts/README.md](/Users/todo/CampusEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/CampusEnergySystem/scripts/SCRIPT_LIST.md)
