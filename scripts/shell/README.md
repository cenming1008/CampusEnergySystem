# shell 脚本说明

`scripts/shell/` 主要放仓库级 shell 工具。当前目录中以状态检查、上线检查、备份恢复和部署辅助为主，推荐按职责理解。

## 使用优先级

- 正式工具：状态、健康检查、备份恢复、部署发布
- 辅助入口：部署与发布检查

## 当前脚本

### 状态检查

- [status.sh](/Users/todo/CampusEnergySystem/scripts/shell/status.sh)：查看系统状态
- [test_health.sh](/Users/todo/CampusEnergySystem/scripts/shell/test_health.sh)：健康检查

### 维护与部署

- [backup.sh](/Users/todo/CampusEnergySystem/scripts/shell/backup.sh)：备份数据库
- [restore.sh](/Users/todo/CampusEnergySystem/scripts/shell/restore.sh)：恢复数据库
- [install_dependencies.sh](/Users/todo/CampusEnergySystem/scripts/shell/install_dependencies.sh)：安装依赖
- [deploy_prod.sh](/Users/todo/CampusEnergySystem/scripts/shell/deploy_prod.sh)：生产部署
- [release_readiness.sh](/Users/todo/CampusEnergySystem/scripts/shell/release_readiness.sh)：发布前总检查
- [run_backend_coverage.sh](/Users/todo/CampusEnergySystem/scripts/shell/run_backend_coverage.sh)：后端覆盖率检查
- [render_alertmanager_config.sh](/Users/todo/CampusEnergySystem/scripts/shell/render_alertmanager_config.sh)：渲染 Alertmanager 配置
- [setup_mqtt_auth.sh](/Users/todo/CampusEnergySystem/scripts/shell/setup_mqtt_auth.sh)：配置 MQTT 认证

## 最常用组合

```bash
# 开发中间件 + 前后端本地
./bin/fast_start_dev.sh

# 停止开发环境
./bin/stop_dev.sh

# 状态检查
./scripts/shell/status.sh
./scripts/shell/test_health.sh
```

## 使用建议

- 日常快速启动优先看 [bin/README.md](/Users/todo/CampusEnergySystem/bin/README.md)
- 需要完整能力时使用这里的脚本
- 详细总览见 [scripts/README.md](/Users/todo/CampusEnergySystem/scripts/README.md)
- 完整清单见 [scripts/SCRIPT_LIST.md](/Users/todo/CampusEnergySystem/scripts/SCRIPT_LIST.md)
