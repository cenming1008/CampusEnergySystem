# 故障排查指南

## 🔴 数据库容器启动失败

### 常见原因

#### 1. pg_data 目录权限问题

**症状**：容器启动失败，日志显示权限错误

**解决方案**：
```bash
# 停止所有容器
docker compose down

# 修复权限
sudo chown -R $(id -u):$(id -g) pg_data/
chmod -R 755 pg_data/

# 重新启动
docker compose up -d
```

#### 2. 数据库版本不兼容

**症状**：pg_data 目录包含旧版本 PostgreSQL 数据

**解决方案**（⚠️ 会删除现有数据）：
```bash
# 停止所有容器
docker compose down

# 备份现有数据（如果需要）
tar -czf pg_data_backup_$(date +%Y%m%d).tar.gz pg_data/

# 删除旧数据
rm -rf pg_data/*

# 重新启动（会自动创建新数据库）
docker compose up -d --build
```

#### 3. 端口被占用

**症状**：端口 5433 已被占用

**解决方案**：
```bash
# 检查端口占用
lsof -i :5433

# 停止占用端口的进程，或修改 docker-compose.yml 中的端口映射
```

#### 4. Docker 权限问题

**症状**：`permission denied while trying to connect to the docker API`

**解决方案**：
```bash
# 确保 Docker Desktop 正在运行
open /Applications/Docker.app

# 等待 Docker 完全启动（菜单栏图标不再闪烁）

# 验证 Docker 权限
docker ps
```

---

## 🔍 查看详细错误信息

### 方法一：查看容器日志

```bash
# 查看数据库容器日志
docker compose logs db

# 查看最近 50 行
docker compose logs --tail=50 db

# 实时查看日志
docker compose logs -f db
```

### 方法二：查看容器状态

```bash
# 查看所有容器状态
docker compose ps

# 查看容器详细信息
docker inspect mine_energy_db
```

### 方法三：进入容器调试

```bash
# 进入数据库容器（如果容器在运行）
docker exec -it mine_energy_db bash

# 检查数据库状态
docker exec -it mine_energy_db psql -U admin -d mine_energy
```

---

## 🛠️ 常见错误及解决方案

### 错误 1: "permission denied" 或 "operation not permitted"

**原因**：文件权限问题

**解决**：
```bash
# 修复项目目录权限
sudo chown -R $(id -u):$(id -g) .
chmod -R 755 pg_data/ mosquitto/ logs/
```

### 错误 2: "port is already allocated"

**原因**：端口被占用

**解决**：
```bash
# 查找占用端口的进程
lsof -i :5433
lsof -i :8088
lsof -i :6379
lsof -i :1883

# 停止占用端口的进程，或修改 docker-compose.yml
```

### 错误 3: "database files are incompatible"

**原因**：PostgreSQL 版本不匹配

**解决**：
```bash
# 删除旧数据，重新创建
docker compose down
rm -rf pg_data/*
docker compose up -d
```

### 错误 4: "Cannot connect to the Docker daemon"

**原因**：Docker Desktop 未运行

**解决**：
```bash
# 启动 Docker Desktop
open /Applications/Docker.app

# 等待启动完成（约 1-2 分钟）
# 验证
docker ps
```

### 错误 5: "no space left on device"

**原因**：磁盘空间不足

**解决**：
```bash
# 检查磁盘空间
df -h

# 清理 Docker 资源
docker system prune -a

# 清理未使用的卷
docker volume prune
```

---

## 🔄 完全重置（最后手段）

如果以上方法都不行，可以完全重置：

```bash
# 1. 停止所有容器
docker compose down -v

# 2. 删除所有数据（⚠️ 会丢失所有数据）
rm -rf pg_data/*
rm -rf mosquitto/data/*
rm -rf logs/*

# 3. 清理 Docker 资源
docker system prune -f

# 4. 重新构建并启动
docker compose up -d --build
```

---

## 📊 诊断命令集合

```bash
# 1. 检查 Docker 状态
docker info
docker compose version

# 2. 检查容器状态
docker compose ps
docker ps -a

# 3. 查看日志
docker compose logs
docker compose logs db
docker compose logs backend

# 4. 检查端口
lsof -i :8088
lsof -i :5433
lsof -i :6379
lsof -i :1883

# 5. 检查磁盘空间
df -h
du -sh pg_data/

# 6. 检查权限
ls -la pg_data/
ls -la mosquitto/
```

---

## 💡 预防措施

1. **定期备份数据**
   ```bash
   docker exec mine_energy_db pg_dump -U admin mine_energy > backup.sql
   ```

2. **监控磁盘空间**
   ```bash
   df -h
   ```

3. **检查日志**
   ```bash
   docker compose logs --tail=100
   ```

---

## 🆘 获取帮助

如果以上方法都无法解决问题，请提供以下信息：

1. **错误日志**：
   ```bash
   docker compose logs > error_log.txt
   ```

2. **系统信息**：
   ```bash
   uname -a
   docker --version
   docker compose version
   ```

3. **容器状态**：
   ```bash
   docker compose ps > container_status.txt
   ```

---

**记住：大多数问题都可以通过查看日志找到原因！** 📋
