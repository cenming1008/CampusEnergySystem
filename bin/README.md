# bin 目录说明

`bin/` 是仓库的高频快捷入口层，只保留少量适合人工直接执行的短命令。

它不作为完整脚本实现目录。状态检查、备份、恢复、部署、发布检查和调试工具统一放在 [scripts/](../scripts/README.md)。

## 和 scripts 的区别

| 目录 | 定位 | 适合场景 |
|------|------|----------|
| `bin/` | 快捷入口层 | 日常把系统快速跑起来 |
| `scripts/shell/` | Shell 正式实现层 | 检查、备份、恢复、部署、发布检查 |
| `scripts/python/` | Python 工具层 | 初始化、配置检查、压测、告警通道验证等 |

判断规则：

- 高频、面向人工、命令值得缩短：可以放 `bin/`
- 需要完整参数、检查、恢复、部署或长期维护：放 `scripts/`
- 前端原生命令：放 `frontend/package.json`

## 当前入口

| 脚本 | 用途 | 对应能力 |
|------|------|----------|
| `fast_start.sh` | 生产快速启动 | 使用 `docker-compose.prod.yml` 和 `.env.prod` 启动生产服务 |
| `stop_prod.sh` | 生产快速停止 | 停止 `docker-compose.prod.yml` 中的生产服务，不删除挂载数据 |
| `fast_start_dev.sh` | 开发快速启动 | 启动开发中间件，并编排本地后端、worker 和前端 |
| `stop_dev.sh` | 开发快速停止 | 停止本地后端、worker、前端和开发中间件 |

## 推荐使用

开发模式：

```bash
./bin/fast_start_dev.sh
```

停止开发环境：

```bash
./bin/stop_dev.sh
```

生产快速启动：

```bash
./bin/fast_start.sh
```

生产快速停止：

```bash
./bin/stop_prod.sh
```

需要细粒度运维或排查时，改用 `scripts/`：

```bash
./scripts/shell/status.sh
./scripts/shell/test_health.sh
./scripts/shell/backup.sh
./scripts/shell/release_readiness.sh
```

## 维护原则

- `bin/` 不新增低频脚本
- `bin/` 只承载高频启停编排，不放低频运维工具
- `bin/` 不替代 `scripts/README.md` 和 `scripts/SCRIPT_LIST.md`
- 如果快捷入口开始承载低频运维能力，优先拆回 `scripts/`
