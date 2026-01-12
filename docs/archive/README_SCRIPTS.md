# 后端容器管理脚本使用说明

## 📋 脚本列表

### 1. `restart_backend.sh` - 快速重启容器

**功能**：仅重启后端容器，不重新构建镜像

**适用场景**：
- ✅ 服务异常，需要重启恢复
- ✅ 修改了环境变量（需要重启生效）
- ✅ 代码未修改，只是需要重启服务
- ✅ 容器运行正常，但想刷新连接

**使用方法**：
```bash
cd /www/wwwroot/MineEnergySystem
./restart_backend.sh
```

**执行时间**：约 5-10 秒

---

### 2. `rebuild_backend.sh` - 重新构建并重启

**功能**：重新构建 Docker 镜像（包含最新代码）并重启容器

**适用场景**：
- ✅ 修改了 Python 代码（`app/` 目录下的文件）
- ✅ 修改了 `requirements.txt`（添加了新依赖）
- ✅ 修改了 `Dockerfile`
- ✅ 需要应用最新的代码更改

**使用方法**：
```bash
cd /www/wwwroot/MineEnergySystem
./rebuild_backend.sh
```

**执行时间**：约 1-3 分钟（取决于网络和依赖）

---

## 🚀 快速使用指南

### 场景1：代码已修改，需要应用更改

```bash
# 1. 进入项目目录
cd /www/wwwroot/MineEnergySystem

# 2. 重新构建并重启
./rebuild_backend.sh

# 3. 查看日志确认启动成功
docker-compose logs -f backend
```

### 场景2：服务异常，需要重启

```bash
# 1. 进入项目目录
cd /www/wwwroot/MineEnergySystem

# 2. 快速重启
./restart_backend.sh

# 3. 查看日志
docker-compose logs -f backend
```

### 场景3：查看容器状态和日志

```bash
# 查看容器状态
docker-compose ps

# 查看后端日志（实时）
docker-compose logs -f backend

# 查看最近100行日志
docker-compose logs --tail=100 backend

# 查看容器详细信息
docker inspect mine_backend
```

---

## ⚠️ 常见问题

### Q1: 提示 "Permission denied"
```bash
# 解决方案：添加执行权限
chmod +x restart_backend.sh rebuild_backend.sh
```

### Q2: 提示 "docker-compose: command not found"
```bash
# 解决方案：使用 docker compose（新版本）
# 或者安装 docker-compose
# 或者修改脚本中的 docker-compose 为 docker compose
```

### Q3: 构建失败，提示找不到文件
```bash
# 确保在项目根目录执行
cd /www/wwwroot/MineEnergySystem
pwd  # 确认路径正确
```

### Q4: 容器启动后立即退出
```bash
# 查看详细错误日志
docker-compose logs backend

# 检查代码是否有语法错误
# 检查依赖是否安装成功
```

---

## 📝 手动操作（如果脚本不可用）

### 仅重启容器
```bash
docker restart mine_backend
# 或
docker-compose restart backend
```

### 重新构建并重启
```bash
docker-compose build backend
docker-compose up -d backend
# 或一条命令
docker-compose up -d --build backend
```

---

## 🔍 验证重启是否成功

```bash
# 1. 检查容器状态
docker-compose ps backend

# 2. 检查端口是否监听
netstat -tlnp | grep 8088
# 或
ss -tlnp | grep 8088

# 3. 测试API是否响应
curl http://localhost:8088/docs

# 4. 查看日志确认无错误
docker-compose logs --tail=50 backend
```

---

## 💡 最佳实践

1. **开发时**：修改代码后使用 `rebuild_backend.sh`
2. **生产环境**：谨慎使用，建议在维护窗口期操作
3. **查看日志**：重启后务必查看日志确认服务正常
4. **备份数据**：重要操作前建议备份数据库

---

## 📞 需要帮助？

如果遇到问题，可以：
1. 查看容器日志：`docker-compose logs backend`
2. 检查容器状态：`docker-compose ps`
3. 查看系统资源：`docker stats mine_backend`


