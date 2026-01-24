# 🔧 可执行脚本目录

> 本目录包含常用的启动和管理脚本（精简版）

## 📋 脚本列表

### 🚀 快速启动

| 脚本 | 用途 | 适用场景 |
|------|------|----------|
| **fast_start.sh** | 快速启动（缓存优化） | 日常开发使用 ⭐ |

**特点**：
- ✅ 智能检测镜像缓存
- ✅ 首次自动完整构建
- ✅ 后续使用缓存快速启动（10-30秒）

### 🔧 工具脚本

| 脚本 | 用途 | 说明 |
|------|------|------|
| **run_simulator.sh** | 运行设备模拟器 | 在Docker容器内生成测试数据 |

## 🎯 使用方法

### 从项目根目录运行

```bash
# 方式1：使用相对路径
./bin/fast_start.sh

# 方式2：直接运行（如果已在 bin 目录）
cd bin
./fast_start.sh
```

### 从任意目录运行

```bash
# 使用绝对路径
/path/to/MineEnergySystem/bin/fast_start.sh
```

## 📝 详细说明

### fast_start.sh ⭐ 推荐日常使用

**功能**：智能启动，自动检测是否需要重新构建镜像

**执行流程**：
1. 检查 Docker 是否运行
2. 检查镜像缓存是否存在
3. 如果镜像缺失 → 完整构建（3-5分钟）
4. 如果镜像存在 → 快速启动（10-30秒）
5. 显示服务状态和访问地址

**适用场景**：
- ✅ 日常开发使用
- ✅ 重启服务
- ✅ 代码修改后快速测试

**执行时间**：
- 首次启动：3-5分钟
- 后续启动：10-30秒

### run_simulator.sh

**功能**：在 Docker 容器中运行设备模拟器

**特点**：
- 自动设置 MQTT 和 API 环境变量
- 在容器内运行，环境隔离
- 生成真实的测试数据

**使用方法**：
```bash
./bin/run_simulator.sh

# 停止：按 Ctrl+C
```

**模拟的设备类型**：
- 智能电表
- 主通风机
- 中央排水泵
- 矿用变压器
- 瓦斯抽放泵
- MG500采煤机
- 皮带输送机
- 副井提升机
- 空气压缩机
- 刮板输送机

## 🔗 更多功能

`bin/` 目录提供最常用的快捷脚本，更多完整功能请使用 `scripts/` 目录：

### 完整启动脚本

```bash
# 完整启动（带详细检查和提示）
./scripts/shell/start.sh

# 停止所有服务
./scripts/shell/stop.sh

# 查看服务状态
./scripts/shell/status.sh

# 重启后端服务
./scripts/shell/restart_backend.sh

# 重建后端
./scripts/shell/rebuild_backend.sh
```

### 前端开发

```bash
# 启动前端开发服务器（完整版，带检查）
./scripts/shell/start_frontend.sh
```

### 健康检查

```bash
# 完整的健康检查测试
./scripts/shell/test_health.sh
```

### Python 工具

```bash
# 创建管理员账户
python scripts/python/create_admin.py

# 设备分组演示
python scripts/python/demo_device_group.py

# 位置管理演示
python scripts/python/demo_location.py

# 维护管理演示
python scripts/python/demo_maintenance.py

# 重建数据库
python scripts/python/rebuild_database.py

# 数据迁移
python scripts/python/migrate_devicedata_to_energydata.py
```

## 💡 使用建议

### 典型工作流程

```bash
# 1. 日常启动（最常用）⭐
./bin/fast_start.sh

# 2. 查看服务状态
./scripts/shell/status.sh

# 3. 启动前端（需要Web界面时）
./scripts/shell/start_frontend.sh

# 4. 生成测试数据
./bin/run_simulator.sh

# 5. 停止服务（下班时）
./scripts/shell/stop.sh
```

### 首次使用

```bash
# 1. 启动所有服务（会自动构建）
./bin/fast_start.sh

# 2. 创建管理员账户
docker exec mine_backend python scripts/python/create_admin.py

# 3. 运行演示脚本（可选）
docker exec mine_backend python scripts/python/demo_unified_system.py

# 4. 启动前端
./scripts/shell/start_frontend.sh

# 5. 启动模拟器生成数据
./bin/run_simulator.sh
```

### 故障排查

```bash
# 查看日志
docker compose logs -f backend

# 查看所有服务日志
docker compose logs -f

# 健康检查
./scripts/shell/test_health.sh

# 查看状态
./scripts/shell/status.sh

# 重启服务
./scripts/shell/restart_backend.sh
```

## 🆘 常见问题

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
MineEnergySystem/
├── bin/                    # 🚀 常用快捷脚本（本目录）
│   ├── fast_start.sh      # 日常快速启动
│   └── run_simulator.sh   # 运行模拟器
├── scripts/               # 🔧 完整工具集
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
- ✅ **完整**：包含所有功能脚本
- ✅ **专业**：详细的检查和提示
- ✅ **灵活**：各种场景的工具

---

**💡 提示**：日常使用推荐 `./bin/fast_start.sh`，它会智能判断是否需要重新构建，大大节省启动时间！

**📞 技术支持**：如有问题请查看主文档或相关文档链接
