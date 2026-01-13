# 🔧 可执行脚本目录

> 本目录包含所有常用的启动和管理脚本

## 📋 脚本列表

### 🚀 启动脚本

| 脚本 | 用途 | 适用场景 |
|------|------|----------|
| **quick_start.sh** | 完整启动 | 首次使用或修改了依赖 |
| **fast_start.sh** | 快速启动 | 日常使用（使用缓存）⭐ |
| **start_frontend.sh** | 启动前端 | 需要 Web 界面时 |

### 🔧 工具脚本

| 脚本 | 用途 | 说明 |
|------|------|------|
| **run_simulator.sh** | 运行模拟器 | 生成测试数据 |
| **init_devices.sh** | 初始化设备 | 创建10个测试设备 |
| **check_system.sh** | 系统检查 | 检查服务状态和配置 |

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

### quick_start.sh
- **功能**：完整构建并启动所有服务
- **执行时间**：首次 3-5分钟，后续 30-60秒
- **适用场景**：
  - 首次安装
  - 修改了 Dockerfile 或 requirements.txt
  - 需要重新构建镜像

### fast_start.sh ⭐
- **功能**：快速启动（使用缓存的镜像）
- **执行时间**：10-30秒
- **适用场景**：
  - 日常使用
  - 重启服务
  - 代码没有变化

### start_frontend.sh
- **功能**：启动前端开发服务器
- **端口**：5173
- **说明**：会自动检测并安装依赖

### run_simulator.sh
- **功能**：在 Docker 容器中运行设备模拟器
- **说明**：自动设置 MQTT 和 API 环境变量
- **停止**：按 Ctrl+C

### init_devices.sh
- **功能**：初始化10个测试设备
- **设备列表**：
  1. 智能电表
  2. 主通风机
  3. 中央排水泵
  4. 矿用变压器
  5. 瓦斯抽放泵
  6. MG500采煤机
  7. 皮带输送机
  8. 副井提升机
  9. 空气压缩机
  10. 刮板输送机

### check_system.sh
- **功能**：全面的系统检查
- **检查内容**：
  - Docker 容器状态
  - 系统配置
  - API 健康检查

## 🔗 相关文档

- [START_HERE.md](../START_HERE.md) - 快速开始指南
- [README.md](../README.md) - 完整项目文档
- [docs/快速启动指南.md](../docs/快速启动指南.md) - 详细启动教程
- [docs/DOCKER_SCRIPTS.md](../docs/DOCKER_SCRIPTS.md) - Docker 脚本完整指南

## 💡 提示

1. **首次使用**：运行 `./quick_start.sh`
2. **日常使用**：运行 `./fast_start.sh`
3. **需要前端**：运行 `./start_frontend.sh`
4. **生成数据**：依次运行 `./init_devices.sh` 和 `./run_simulator.sh`
5. **检查状态**：运行 `./check_system.sh`

## 🆘 常见问题

**Q: 脚本提示 "permission denied"**
```bash
# 解决：添加执行权限
chmod +x bin/*.sh
```

**Q: Docker 未运行**
```bash
# macOS: 启动 Docker Desktop
open /Applications/Docker.app
```

**Q: 端口被占用**
```bash
# 检查占用
lsof -i :8088

# 停止旧服务
docker compose down
```

---

**📚 更多帮助请查看项目主文档**
