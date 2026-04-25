# scripts 目录说明

`scripts/` 是项目的“正式实现层 + 完整工具集”。和 [bin/](../bin/README.md) 的快捷入口不同，这里放的是仓库级正式脚本、调试工具和已降级历史脚本。

## 目录职责

- `shell/`：启动、停止、检查、备份、恢复、清理、部署
- `python/`：系统初始化、演示数据、协议调试、压力测试
- `archive/`：已从正式入口降级的历史脚本
- `SCRIPT_LIST.md`：完整脚本清单

## 推荐使用方式

### 1. 需要确认事实来源时看完整清单

- [SCRIPT_LIST.md](./SCRIPT_LIST.md)

适合“我想知道这个目录里到底都有什么，不重复地看一遍”。

### 2. 需要按职责查看时看子目录文档

- [shell/README.md](./shell/README.md)
- [python/README.md](./python/README.md)

## 入口优先级

1. 日常快速启动：优先看 `bin/`
2. 正式执行某项仓库级能力：优先看 `scripts/`
3. 想确认“当前到底有哪些脚本”：只看 `SCRIPT_LIST.md`

---

## 最常用正式脚本

### Shell

- [start.sh](./shell/start.sh)：启动整套 Docker 服务
- [start_dev_env.sh](./shell/start_dev_env.sh)：启动开发环境中间件
- [status.sh](./shell/status.sh)：查看系统状态
- [test_health.sh](./shell/test_health.sh)：健康检查

### Python

- [init_complete_system.py](./python/init_complete_system.py)：初始化整套演示/开发数据
- [create_admin.py](./python/create_admin.py)：创建管理员
- [check_config.py](./python/check_config.py)：配置检查
- [send_test_alert.py](./python/send_test_alert.py)：验证告警通知通道

## 脚本分类

### 服务管理

- 启动/停止：`start.sh`、`stop.sh`、`start_dev_env.sh`、`stop_dev_env.sh`

### 前端开发入口

- 正式入口：`cd frontend && npm run dev`
- 构建验证：`cd frontend && npm run build`
- 代码检查：`cd frontend && npm run lint`
- 预览构建：`cd frontend && npm run preview`

### 状态与排查

- `status.sh`
- `test_health.sh`
- `check_config.py`
- `stress_test.py`
- `evaluate_capacity_baseline.py`

### 数据与环境维护

- `backup.sh`
- `restore.sh`
- `install_dependencies.sh`

### 已归档/历史脚本

- `archive/python/rebuild_database.py`
- `archive/python/demo_unified_system.py`
- `archive/python/demo_device_group.py`
- `archive/python/demo_location.py`
- `archive/python/demo_maintenance.py`
- `archive/shell/start_frontend.sh`
- `archive/shell/uninstall_local_services.sh`

### 初始化与演示

- `init_complete_system.py`
- `create_admin.py`

历史演示脚本已归档到 `scripts/archive/python/`，避免继续占用当前正式/联调目录。

### 设备接入与协议调试

- `send_test_alert.py`

本地设备采集/网关脚本已移除，真实联调以 Windows 工控机运行脚本和平台接入记录为准。

### 压测

- `stress_test.py`

## 与 bin 的关系

`bin/` 是高频快捷壳，`scripts/` 是仓库级正式实现层与事实来源。

例如：

- [bin/fast_start.sh](../bin/fast_start.sh) 对应 [scripts/shell/start.sh](./shell/start.sh)

## 整理原则

这个目录后续建议继续保持：

- 不移动现有脚本路径，避免打断文档和使用习惯
- 新脚本先补进 `SCRIPT_LIST.md`
- 不再维护第二份“快捷参考型”脚本总表，`SCRIPT_LIST.md` 是唯一总览
- 先判断脚本属于正式入口、调试脚本还是历史脚本，再决定是否进入 README 第一层入口
- 生成文件不留在目录里，比如 `__pycache__`、`.DS_Store`
