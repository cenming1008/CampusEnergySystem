# bin 目录说明

`bin/` 是这个项目的“快捷入口层”。

它的用途不是承载完整实现，而是把最常用的几个动作收成短命令，方便日常启动和演示。真正的正式实现统一放在 [`scripts/`](../scripts/README.md)。

## 目录职责

- `bin/`：给人直接敲的快捷脚本，命令短、上手快
- `scripts/shell/`：完整 shell 工具集，检查更全、场景更细
- `scripts/python/`：Python 工具和模拟器的真实实现

## 当前脚本

| 脚本 | 用途 | 本质 |
|------|------|------|
| `fast_start.sh` | 快速启动整套 Docker 服务 | 快捷启动入口 |
| `fast_start_dev.sh` | 启动开发模式 | 快捷编排入口 |
| `run_simulator.sh` | 运行设备模拟器 | 对 Python 模拟器的容器包装 |

## 推荐理解

- `bin/` 适合“我现在就想把系统跑起来”
- `scripts/` 适合“我需要正式执行某项能力、做排查或单独执行某一部分”
- 当 `bin/` 与 `scripts/` 同时能完成某件事时，以 `scripts/` 中的实现为事实来源，以 `bin/` 为快捷壳

## 常用命令

```bash
# 日常快速启动
./bin/fast_start.sh

# 开发模式：中间件 Docker，前后端本地
./bin/fast_start_dev.sh

# 运行模拟器
./bin/run_simulator.sh
```

## 与 scripts 的关系

| bin 脚本 | 对应实现/能力 |
|---------|---------------|
| `fast_start.sh` | 与 [`scripts/shell/start.sh`](../scripts/shell/start.sh) 用途接近，但更偏“快” |
| `fast_start_dev.sh` | 复用 [`scripts/shell/start_dev_env.sh`](../scripts/shell/start_dev_env.sh) 的中间件启动能力，再补本地前后端启动 |
| `run_simulator.sh` | 包装 [`scripts/python/simulator_unified.py`](../scripts/python/simulator_unified.py) |

## 什么时候不该用 bin

- 你要做细粒度运维时
- 你要单独启动某个服务时
- 你要排查环境或做恢复、备份、清理时

这类场景请直接看 [`scripts/README.md`](../scripts/README.md)。

### Q: 脚本提示 "permission denied"

```bash
# 解决：添加执行权限
chmod +x bin/*.sh
chmod +x scripts/shell/*.sh
```

### Q: Docker 未运行

```bash
# macOS: 启动 Docker Desktop
open /Applications/Docker.app

# 等待 Docker 启动完成（菜单栏图标不再闪烁）
```

### Q: 端口被占用

```bash
# 检查占用
lsof -i :8088

# 停止旧服务
docker compose down

# 清理并重启
docker compose down -v
./bin/fast_start.sh
```

### Q: 镜像构建失败

```bash
# 清理旧镜像
docker compose down -v
docker system prune -a

# 重新构建
docker compose up -d --build
```

### Q: 需要完整重建

```bash
# 方案1：使用 scripts 中的完整启动脚本
./scripts/shell/start.sh

# 方案2：手动构建
docker compose down -v
docker compose up -d --build
```

## 📚 相关文档

- [项目主文档](../README.md) - 完整项目说明
- [快速启动指南](../docs/01-新手入门/快速启动指南.md) - 新手入门
- [安装配置指南](../docs/01-新手入门/安装配置完整指南.md) - 详细配置
- [脚本使用指南](../scripts/README.md) - Scripts 目录完整说明
- [Docker脚本指南](../docs/03-开发与部署/DOCKER_SCRIPTS.md) - Docker 详细指南

## 📂 目录结构说明

```
CampusEnergySystem/
├── bin/                    # 🚀 常用快捷脚本（本目录，3 个）
│   ├── fast_start.sh      # 日常快速启动（包装正式实现，偏快捷）
│   ├── fast_start_dev.sh  # 开发模式快捷启动
│   └── run_simulator.sh   # 在容器内运行 scripts/python/simulator_unified.py
├── scripts/               # 🔧 正式实现层与完整工具集（见 scripts/SCRIPT_LIST.md）
│   ├── shell/            # Shell 脚本（启动、停止、测试等）
│   └── python/           # Python 脚本（模拟器、工具等）
└── docs/                  # 📚 文档中心
    ├── 01-新手入门/      # 快速开始
    ├── 02-功能使用/      # 功能指南
    ├── 03-开发与部署/    # 开发部署
    └── 04-故障排查/      # 故障诊断
```

## 🎯 设计理念

**bin/ 目录定位**：
- ✅ **精简**：只保留最常用的脚本
- ✅ **快速**：优化启动速度
- ✅ **易用**：简单明了，开箱即用

**scripts/ 目录定位**：
- ✅ **正式**：作为仓库级脚本的事实来源
- ✅ **完整**：包含正式脚本、调试脚本与已归档脚本
- ✅ **专业**：详细的检查和提示
- ✅ **灵活**：各种场景的工具

---

**💡 提示**：日常使用推荐 `./bin/fast_start.sh`，它会智能判断是否需要重新构建，大大节省启动时间！

**📞 技术支持**：如有问题请查看主文档或相关文档链接
