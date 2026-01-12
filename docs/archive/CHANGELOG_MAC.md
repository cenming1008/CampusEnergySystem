# Mac 适配更新日志

## 📝 更新内容

本次更新将项目完全适配 Mac 环境，并优化为使用 Docker 一键启动，**任何人都可以直接使用**。

---

## ✅ 已完成的修改

### 1. Docker Compose 优化

**文件**: `docker-compose.yml`

- ✅ 添加服务健康检查（healthcheck）
- ✅ 优化服务启动顺序（depends_on + condition）
- ✅ 使用 `unless-stopped` 重启策略（更友好）
- ✅ 移除 MQTT 配置覆盖命令（使用已有配置文件）
- ✅ 添加日志目录挂载（方便查看日志）
- ✅ 优化环境变量配置（容器内使用服务名连接）

**关键改进**：
- 后端服务等待数据库、Redis、MQTT 健康后再启动
- 所有服务通过 Docker 内部网络连接（服务名：`db`, `redis`, `mqtt`）

### 2. 启动脚本优化

**文件**: `restart_backend.sh`, `rebuild_backend.sh`

- ✅ 修改路径为动态获取（适配 Mac）
- ✅ 使用 `docker compose`（新版本命令）
- ✅ 移除硬编码的 Linux 路径

### 3. 新增便捷脚本

**新增文件**:
- `start.sh` - 一键启动所有服务（带环境检查）
- `stop.sh` - 停止所有服务
- `status.sh` - 查看服务状态和健康检查
- `check_mac_env.sh` - Mac 环境检查脚本

**功能**:
- 自动检查 Docker 环境
- 自动创建必要目录
- 端口占用检查
- 服务状态监控
- 友好的输出提示

### 4. Dockerfile 优化

**文件**: `Dockerfile`

- ✅ 添加 `curl` 工具（用于健康检查）
- ✅ 保持跨平台兼容（Mac/Linux/Windows）

### 5. 文档完善

**新增文档**:
- `MAC_SETUP_GUIDE.md` - Mac 详细配置指南
- `MAC_QUICK_START.md` - Mac 快速启动指南
- `DOCKER_README.md` - Docker 部署完整指南
- `CHANGELOG_MAC.md` - 本更新日志

---

## 🚀 使用方法

### 快速启动（推荐）

```bash
# 1. 进入项目目录
cd MineEnergySystem

# 2. 一键启动
./start.sh
```

### 手动启动

```bash
docker compose up -d --build
```

### 查看状态

```bash
./status.sh
# 或
docker compose ps
```

### 停止服务

```bash
./stop.sh
# 或
docker compose down
```

---

## 🔧 配置说明

### 服务连接地址

**在 Docker 容器内**（自动配置，无需修改）：
- 数据库: `postgresql://admin:password123@db:5432/mine_energy`
- Redis: `redis://redis:6379/0`
- MQTT: `mqtt:1883`

**从 Mac 本地访问**（如果需要）：
- 数据库: `postgresql://admin:password123@localhost:5433/mine_energy`
- Redis: `redis://localhost:6379/0`
- MQTT: `127.0.0.1:1883`

### 端口映射

| 服务 | 容器端口 | Mac 端口 | 说明 |
|------|----------|----------|------|
| 后端 | 8088 | 8088 | http://localhost:8088 |
| 数据库 | 5432 | 5433 | 避免与本地 PostgreSQL 冲突 |
| Redis | 6379 | 6379 | 标准端口 |
| MQTT | 1883 | 1883 | 标准端口 |
| MQTT WS | 9001 | 9001 | WebSocket 端口 |

---

## 📦 数据持久化

所有数据保存在本地目录，删除容器不会丢失：

- **数据库**: `./pg_data/`
- **Redis**: Docker volume `redis_data`
- **MQTT**: `./mosquitto/data/`
- **日志**: `./logs/`

---

## ✨ 主要优势

1. **一键启动**: 无需手动配置，运行 `./start.sh` 即可
2. **跨平台**: Mac、Linux、Windows 均可使用
3. **环境隔离**: 所有服务在 Docker 中运行，不污染本地环境
4. **数据持久化**: 数据保存在本地，重启不丢失
5. **健康检查**: 自动等待服务就绪，启动更可靠
6. **易于分享**: 任何人都可以克隆项目后直接运行

---

## 🔍 验证清单

启动后验证：

- [ ] 所有容器状态为 "Up"
  ```bash
  docker compose ps
  ```

- [ ] 后端 API 可访问
  ```bash
  curl http://localhost:8088/docs
  # 或浏览器打开: http://localhost:8088/docs
  ```

- [ ] 数据库连接正常
  ```bash
  docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"
  ```

- [ ] Redis 连接正常
  ```bash
  docker exec -it ems_redis redis-cli ping
  ```

- [ ] MQTT 服务正常
  ```bash
  docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'mine/#' -v
  ```

---

## 📚 相关文档

- [DOCKER_README.md](DOCKER_README.md) - Docker 完整使用指南
- [MAC_SETUP_GUIDE.md](MAC_SETUP_GUIDE.md) - Mac 详细配置
- [MAC_QUICK_START.md](MAC_QUICK_START.md) - 快速启动参考
- [README.md](README.md) - 项目主文档

---

## 🎉 总结

现在项目已经完全适配 Mac 环境，并且使用 Docker 容器化部署，**任何人都可以克隆项目后直接运行 `./start.sh` 启动整个系统**，无需任何额外配置！

**享受编码的乐趣！** 🚀
