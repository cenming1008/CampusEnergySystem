# shell 脚本说明

`scripts/shell/` 主要放系统运维和服务管理脚本。

## 当前脚本

### 服务启停

- [start.sh](/Users/todo/MineEnergySystem/scripts/shell/start.sh)：启动整套 Docker 服务
- [start_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/start_dev_env.sh)：启动开发环境中间件
- [stop.sh](/Users/todo/MineEnergySystem/scripts/shell/stop.sh)：停止整套 Docker 服务
- [stop_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/stop_dev_env.sh)：停止开发环境中间件
- [restart_backend.sh](/Users/todo/MineEnergySystem/scripts/shell/restart_backend.sh)：重启后端容器
- [rebuild_backend.sh](/Users/todo/MineEnergySystem/scripts/shell/rebuild_backend.sh)：重建后端容器
- [start_frontend.sh](/Users/todo/MineEnergySystem/scripts/shell/start_frontend.sh)：启动前端开发服务器

### 状态检查

- [status.sh](/Users/todo/MineEnergySystem/scripts/shell/status.sh)：查看系统状态
- [test_health.sh](/Users/todo/MineEnergySystem/scripts/shell/test_health.sh)：健康检查
- [check_websocket.sh](/Users/todo/MineEnergySystem/scripts/shell/check_websocket.sh)：检查 WebSocket
- [check_mac_env.sh](/Users/todo/MineEnergySystem/scripts/shell/check_mac_env.sh)：检查 macOS 开发环境

### 维护与部署

- [backup.sh](/Users/todo/MineEnergySystem/scripts/shell/backup.sh)：备份数据库
- [restore.sh](/Users/todo/MineEnergySystem/scripts/shell/restore.sh)：恢复数据库
- [cleanup_logs.sh](/Users/todo/MineEnergySystem/scripts/shell/cleanup_logs.sh)：清理日志
- [cleanup_docker.sh](/Users/todo/MineEnergySystem/scripts/shell/cleanup_docker.sh)：清理 Docker 资源
- [fix_venv.sh](/Users/todo/MineEnergySystem/scripts/shell/fix_venv.sh)：修复虚拟环境
- [install_dependencies.sh](/Users/todo/MineEnergySystem/scripts/shell/install_dependencies.sh)：安装依赖
- [deploy_prod.sh](/Users/todo/MineEnergySystem/scripts/shell/deploy_prod.sh)：生产部署
- [uninstall_local_services.sh](/Users/todo/MineEnergySystem/scripts/shell/uninstall_local_services.sh)：卸载本机相关服务

## 最常用组合

```bash
# 默认启动
./scripts/shell/start.sh

# 开发模式
./scripts/shell/start_dev_env.sh
./scripts/shell/start_frontend.sh

# 状态检查
./scripts/shell/status.sh
./scripts/shell/test_health.sh
```

## 使用建议

- 日常快速启动优先看 [bin/README.md](/Users/todo/MineEnergySystem/bin/README.md)
- 需要完整能力时使用这里的脚本
- 详细总览见 [scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)
