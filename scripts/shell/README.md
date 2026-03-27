# shell 脚本说明

`scripts/shell/` 主要放仓库级 shell 正式实现。当前目录中既有正式入口，也有辅助检查和轻包装脚本，推荐按职责理解。

## 使用优先级

- 正式入口：启动、停止、状态、健康检查、备份恢复、部署发布
- 辅助入口：局部重启、WebSocket 检查、环境检查、清理类脚本
- 历史脚本：进入 `scripts/archive/shell/`

## 当前脚本

### 服务启停

- [start.sh](/Users/todo/MineEnergySystem/scripts/shell/start.sh)：启动整套 Docker 服务
- [start_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/start_dev_env.sh)：启动开发环境中间件
- [stop.sh](/Users/todo/MineEnergySystem/scripts/shell/stop.sh)：停止整套 Docker 服务
- [stop_dev_env.sh](/Users/todo/MineEnergySystem/scripts/shell/stop_dev_env.sh)：停止开发环境中间件
- [restart_backend.sh](/Users/todo/MineEnergySystem/scripts/shell/restart_backend.sh)：重启后端容器
- [rebuild_backend.sh](/Users/todo/MineEnergySystem/scripts/shell/rebuild_backend.sh)：重建后端容器

其中 `restart_backend.sh`、`rebuild_backend.sh` 更接近局部包装命令，不应高于 `start.sh`、`status.sh` 这类正式入口。

### 状态检查

- [status.sh](/Users/todo/MineEnergySystem/scripts/shell/status.sh)：查看系统状态
- [test_health.sh](/Users/todo/MineEnergySystem/scripts/shell/test_health.sh)：健康检查
- [pilot_smoke_test.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_smoke_test.sh)：试点联调冒烟检查
- [pilot_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_readiness.sh)：试点前总检查并归档证据
- [pilot_drill.sh](/Users/todo/MineEnergySystem/scripts/shell/pilot_drill.sh)：串联 readiness、容量基线和冒烟
- [load_baseline.sh](/Users/todo/MineEnergySystem/scripts/shell/load_baseline.sh)：生成容量基线和验收摘要
- [check_websocket.sh](/Users/todo/MineEnergySystem/scripts/shell/check_websocket.sh)：检查 WebSocket
- [check_mac_env.sh](/Users/todo/MineEnergySystem/scripts/shell/check_mac_env.sh)：检查 macOS 开发环境
- [restore_drill.sh](/Users/todo/MineEnergySystem/scripts/shell/restore_drill.sh)：执行恢复演练

### 维护与部署

- [backup.sh](/Users/todo/MineEnergySystem/scripts/shell/backup.sh)：备份数据库
- [restore.sh](/Users/todo/MineEnergySystem/scripts/shell/restore.sh)：恢复数据库
- [rollback_prod.sh](/Users/todo/MineEnergySystem/scripts/shell/rollback_prod.sh)：生产回滚入口
- [cleanup_logs.sh](/Users/todo/MineEnergySystem/scripts/shell/cleanup_logs.sh)：清理日志
- [cleanup_docker.sh](/Users/todo/MineEnergySystem/scripts/shell/cleanup_docker.sh)：清理 Docker 资源
- [fix_venv.sh](/Users/todo/MineEnergySystem/scripts/shell/fix_venv.sh)：修复虚拟环境
- [install_dependencies.sh](/Users/todo/MineEnergySystem/scripts/shell/install_dependencies.sh)：安装依赖
- [deploy_prod.sh](/Users/todo/MineEnergySystem/scripts/shell/deploy_prod.sh)：生产部署
- [release_readiness.sh](/Users/todo/MineEnergySystem/scripts/shell/release_readiness.sh)：发布前总检查
- [render_alertmanager_config.sh](/Users/todo/MineEnergySystem/scripts/shell/render_alertmanager_config.sh)：渲染 Alertmanager 配置
- [setup_mqtt_auth.sh](/Users/todo/MineEnergySystem/scripts/shell/setup_mqtt_auth.sh)：配置 MQTT 认证
- [uninstall_local_services.sh](/Users/todo/MineEnergySystem/scripts/shell/uninstall_local_services.sh)：卸载本机相关服务

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
./scripts/shell/pilot_smoke_test.sh
./scripts/shell/pilot_readiness.sh --env-file .env.prod
./scripts/shell/pilot_drill.sh
```

## 使用建议

- 日常快速启动优先看 [bin/README.md](/Users/todo/MineEnergySystem/bin/README.md)
- 需要完整能力时使用这里的脚本
- 详细总览见 [scripts/README.md](/Users/todo/MineEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/MineEnergySystem/scripts/SCRIPT_LIST.md)
