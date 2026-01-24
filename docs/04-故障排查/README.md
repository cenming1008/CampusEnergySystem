# 故障排查指南

> 常见问题快速解决方案

---

## 📚 文档列表

### 🔧 虚拟环境问题修复

**[fix_venv_issue.md](./fix_venv_issue.md)**

解决 Python 虚拟环境相关问题：

- pip 命令不可用
- 虚拟环境损坏
- 依赖安装失败
- Python 版本问题

**适合人群**：
- 遇到 `command not found: pip` 的用户
- 虚拟环境无法激活的用户
- 依赖安装出错的用户

---

## 🔍 快速诊断

### 系统健康检查

```bash
# 一键检查系统状态
./scripts/shell/test_health.sh

# 或手动检查
docker compose ps              # 查看容器状态
curl http://localhost:8088/health  # 测试 API
```

### 常见问题分类

| 类别 | 症状 | 快速解决 |
|------|------|---------|
| **启动问题** | 容器无法启动 | 查看 [启动问题](#启动问题) |
| **连接问题** | 无法访问 API | 查看 [连接问题](#连接问题) |
| **环境问题** | pip 不可用 | 查看 [环境问题](#环境问题) |
| **性能问题** | 系统响应慢 | 查看 [性能问题](#性能问题) |

---

## 🚨 启动问题

### 问题1：Docker 未安装或未启动

**症状**：
```
❌ Docker 未安装
❌ Docker 未运行
```

**解决方案**：
```bash
# macOS：安装 Docker Desktop
brew install --cask docker

# 启动 Docker Desktop
open /Applications/Docker.app

# 验证
docker info
```

### 问题2：端口被占用

**症状**：
```
Error: Bind for 0.0.0.0:8088 failed: port is already allocated
```

**解决方案**：
```bash
# 方案1：停止占用端口的服务
docker compose down
lsof -i :8088
kill <PID>

# 方案2：修改端口映射
# 编辑 docker-compose.yml
# 将 8088:8088 改为 8089:8088
```

### 问题3：容器启动后立即退出

**症状**：
```bash
docker compose ps
# 显示 Exit 状态
```

**解决方案**：
```bash
# 1. 查看日志找出错误
docker compose logs backend

# 2. 常见原因：
# - 数据库未就绪：等待20秒后重试
# - 环境变量错误：检查 .env 文件
# - 代码错误：查看日志详情

# 3. 重新启动
docker compose restart backend
```

### 问题4：首次启动非常慢

**原因**：需要下载镜像和构建（正常现象）

**预期时间**：
- 首次：3-5 分钟
- 后续：30-60 秒

**加速方案**：
```bash
# 使用快速启动脚本（跳过构建）
./bin/fast_start.sh
```

---

## 🔌 连接问题

### 问题1：无法访问 API (http://localhost:8088)

**诊断步骤**：
```bash
# 1. 检查容器状态
docker compose ps
# backend 应该是 Up 状态

# 2. 检查端口监听
lsof -i :8088
# 应该显示 docker-proxy

# 3. 测试本地连接
curl http://localhost:8088/health

# 4. 查看后端日志
docker compose logs backend
```

**解决方案**：
```bash
# 容器未运行
docker compose restart backend

# 端口映射错误
# 检查 docker-compose.yml 中的 ports 配置

# 防火墙阻止
# macOS：系统偏好设置 → 安全性与隐私 → 防火墙
```

### 问题2：数据库连接失败

**症状**：
```
sqlalchemy.exc.OperationalError: could not connect to server
```

**解决方案**：
```bash
# 1. 等待数据库启动完成
sleep 20

# 2. 测试数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 3. 检查数据库状态
docker compose ps db

# 4. 重启数据库
docker compose restart db
```

### 问题3：MQTT 连接失败

**症状**：
```
❌ 无法连接 MQTT Broker
```

**解决方案**：
```bash
# 1. 检查 MQTT 服务
docker compose ps mqtt

# 2. 测试 MQTT 连接
docker exec -it mine_mqtt mosquitto_sub -h localhost -t 'test'

# 3. 检查环境变量
# Docker 内：MQTT_BROKER=mqtt
# 本地：MQTT_BROKER=localhost
```

---

## 🐍 环境问题

### 问题1：command not found: pip

**原因**：macOS 默认只有 `pip3`

**解决方案**：
```bash
# 方案1：使用 pip3
pip3 install -r requirements.txt

# 方案2：激活虚拟环境
source venv/bin/activate
pip install -r requirements.txt  # 现在可以用 pip 了

# 方案3：使用模块方式
python3 -m pip install -r requirements.txt
```

**详细文档**：[fix_venv_issue.md](./fix_venv_issue.md)

### 问题2：虚拟环境损坏

**症状**：
```bash
source venv/bin/activate
# 激活后 python 和 pip 仍然指向系统版本
```

**解决方案**：
```bash
# 重新创建虚拟环境
./scripts/shell/fix_venv.sh

# 或手动重建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install -r requirements.txt
```

### 问题3：TensorFlow 未安装

**症状**：
```
TensorFlow未安装，无法使用LSTM预测功能
```

**解决方案**：
```bash
# 激活虚拟环境
source venv/bin/activate

# 安装 TensorFlow（使用国内镜像）
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple tensorflow scikit-learn

# 验证
python -c "import tensorflow; print('✓ TensorFlow 已安装')"
```

---

## ⚡ 性能问题

### 问题1：Git push 很慢

**原因**：使用 HTTPS 协议，或有大文件

**解决方案**：
```bash
# 详细优化步骤请查看：
# docs/03-开发与部署/Git完整指南.md
```

### 问题2：Docker 占用过多资源

**诊断**：
```bash
# 查看资源占用
docker stats
```

**解决方案**：
```bash
# 清理未使用的镜像
docker image prune -a

# 清理未使用的容器
docker container prune

# 清理未使用的卷
docker volume prune
```

### 问题3：API 响应慢

**诊断**：
```bash
# 查看后端日志
docker compose logs -f backend

# 检查数据库性能
docker exec -it mine_energy_db psql -U admin -d mine_energy
```

**解决方案**：
- 启用 Redis 缓存
- 优化数据库查询
- 增加 uvicorn workers
- 查看 [../03-开发与部署/OPTIMIZATION_RECOMMENDATIONS.md](../03-开发与部署/OPTIMIZATION_RECOMMENDATIONS.md)

---

## 🔄 LSTM 功能问题

### 问题1：历史数据不足

**症状**：
```
历史数据不足，至少需要100个数据点
```

**解决方案**：
```bash
# 生成训练数据
curl -X POST "http://localhost:8088/data-generator/generate/device/1" \
  -H "Content-Type: application/json" \
  -d '{"days": 60, "interval_minutes": 60}'
```

### 问题2：模型不存在

**症状**：
```
模型不存在，请先训练模型
```

**解决方案**：
```bash
# 训练模型
curl -X POST "http://localhost:8088/forecast/lstm/train" \
  -H "Content-Type: application/json" \
  -d '{"prediction_type": "load", "device_id": 1}'
```

### 问题3：训练失败

**可能原因**：
- 内存不足
- 数据质量问题
- TensorFlow 未安装

**解决方案**：
```bash
# 检查 TensorFlow
python -c "import tensorflow; print(tensorflow.__version__)"

# 减少训练数据量
# 使用 30 天而不是 60 天

# 查看详细日志
docker compose logs -f backend
```

---

## 📊 诊断工具

### 系统健康检查

```bash
# 完整系统检查
./scripts/shell/test_health.sh

# Docker 服务状态
docker compose ps

# 后端健康检查
curl http://localhost:8088/health

# 数据库检查
docker exec mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# Redis 检查
docker exec ems_redis redis-cli ping

# MQTT 检查
docker exec mine_mqtt mosquitto_sub -h localhost -t 'test' -C 1
```

### 日志查看

```bash
# 查看所有日志
docker compose logs

# 查看特定服务
docker compose logs backend

# 实时查看日志
docker compose logs -f backend

# 最近 100 行
docker compose logs --tail=100 backend
```

---

## 🆘 获取帮助

### 1. 查看文档

- [快速启动指南](../01-新手入门/快速启动指南.md) - 启动问题
- [安装配置指南](../01-新手入门/安装配置完整指南.md) - 环境问题
- [LSTM 指南](../02-功能使用/LSTM预测完整指南.md) - LSTM 问题
- [Git 指南](../03-开发与部署/Git完整指南.md) - Git 问题

### 2. 检查日志

```bash
# 后端日志
docker compose logs backend

# 数据库日志
docker compose logs db

# 所有日志
docker compose logs
```

### 3. 系统诊断

```bash
# 运行诊断脚本
./scripts/shell/test_health.sh

# 查看系统状态
./scripts/shell/status.sh
docker stats
```

### 4. 完全重置（最后手段）

```bash
# ⚠️ 警告：会删除所有数据！
docker compose down -v
rm -rf pg_data/* mosquitto/data/* logs/*
./scripts/shell/start.sh
```

---

## 🔗 相关资源

### 内部文档

- [快速启动指南](../01-新手入门/快速启动指南.md)
- [安装配置指南](../01-新手入门/安装配置完整指南.md)
- [LSTM 完整指南](../02-功能使用/LSTM预测完整指南.md)
- [Git 完整指南](../03-开发与部署/Git完整指南.md)

### 外部资源

- [Docker 故障排查](https://docs.docker.com/config/daemon/)
- [Python 虚拟环境](https://docs.python.org/3/tutorial/venv.html)
- [PostgreSQL 文档](https://www.postgresql.org/docs/)

---

## 💡 预防措施

### 日常维护

```bash
# 定期清理 Docker
docker system prune

# 定期备份数据
docker exec mine_energy_db pg_dump -U admin mine_energy > backup.sql

# 定期更新依赖
pip install --upgrade -r requirements.txt
```

### 最佳实践

- ✅ 使用虚拟环境
- ✅ 定期查看日志
- ✅ 及时备份数据
- ✅ 保持文档更新
- ✅ 遇到问题先查日志

---

**返回**：[docs 主目录](../README.md)
