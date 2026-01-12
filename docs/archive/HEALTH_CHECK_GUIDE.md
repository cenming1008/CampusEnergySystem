# 🏥 健康检查功能使用指南

## 📖 概述

健康检查功能已成功添加到系统中，用于监控系统各组件的运行状态。这对于生产环境部署、负载均衡、自动化运维非常重要。

---

## 🎯 功能特性

### 1. 完整健康检查 `/health`

**用途**：综合检查所有服务组件的健康状态

**检查内容**：
- ✅ 数据库（PostgreSQL/TimescaleDB）连接状态
- ✅ Redis 缓存服务状态
- ✅ 系统版本信息
- ✅ 时间戳

**返回示例**：
```json
{
  "status": "healthy",
  "timestamp": "2026-01-12T15:30:00.000000",
  "version": "2.0.0",
  "services": {
    "database": "healthy",
    "redis": "healthy"
  }
}
```

**状态说明**：
- `healthy`: 所有服务正常
- `degraded`: 部分服务降级（如 Redis 不可用，但核心功能可用）
- `unhealthy`: 核心服务（数据库）不可用

**HTTP 状态码**：
- `200`: 系统正常或降级（仍可用）
- `503`: 系统不健康（核心服务不可用）

---

### 2. 存活检查 `/health/live`

**用途**：检查应用进程是否还活着

**适用场景**：
- Kubernetes Liveness Probe
- Docker 容器健康检查
- 简单的应用存活监控

**特点**：
- ⚡ 快速响应（不检查依赖服务）
- 🎯 只判断应用本身是否运行

**返回示例**：
```json
{
  "status": "alive",
  "timestamp": "2026-01-12T15:30:00.000000"
}
```

---

### 3. 就绪检查 `/health/ready`

**用途**：检查应用是否准备好接收流量

**适用场景**：
- Kubernetes Readiness Probe
- 负载均衡器健康检查
- 流量路由决策

**检查内容**：
- ✅ 数据库连接（核心依赖）

**返回示例**：
```json
{
  "status": "ready",
  "timestamp": "2026-01-12T15:30:00.000000",
  "checks": {
    "database": "ready"
  }
}
```

---

## 🚀 快速测试

### 方法一：使用测试脚本（推荐）

```bash
cd /Users/todo/MineEnergySystem
./test_health.sh
```

测试脚本会自动检查：
1. 后端服务是否运行
2. `/health` 端点响应
3. `/health/live` 端点响应
4. `/health/ready` 端点响应
5. Docker 容器健康状态

---

### 方法二：手动测试

```bash
# 1. 完整健康检查
curl http://localhost:8088/health | python3 -m json.tool

# 2. 存活检查
curl http://localhost:8088/health/live | python3 -m json.tool

# 3. 就绪检查
curl http://localhost:8088/health/ready | python3 -m json.tool

# 4. 查看 Docker 容器健康状态
docker inspect mine_backend --format='{{.State.Health.Status}}'
```

---

### 方法三：浏览器访问

打开浏览器访问：
- **API 文档**: http://localhost:8088/docs
- **健康检查**: http://localhost:8088/health

在 Swagger UI 中找到 "系统健康" 标签，可以直接测试所有健康检查端点。

---

## 🐳 Docker 集成

### Docker Compose 配置

健康检查已自动集成到 `docker-compose.yml` 中：

```yaml
backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
    interval: 10s      # 每10秒检查一次
    timeout: 5s        # 5秒超时
    retries: 3         # 失败3次才标记为不健康
    start_period: 20s  # 启动后20秒开始检查
```

### 查看容器健康状态

```bash
# 查看所有容器状态
docker compose ps

# 查看后端容器健康状态
docker inspect mine_backend --format='{{.State.Health.Status}}'

# 查看健康检查日志
docker inspect mine_backend --format='{{json .State.Health}}' | python3 -m json.tool
```

---

## 🔄 重启服务以应用更改

健康检查功能已添加完成，需要重启服务使其生效：

```bash
cd /Users/todo/MineEnergySystem

# 方法一：重启后端服务
docker compose restart backend

# 方法二：重新构建并启动（如果修改了 Dockerfile）
docker compose up -d --build backend

# 方法三：完全重启所有服务
docker compose down
docker compose up -d
```

等待约 10-20 秒，让服务完全启动并通过健康检查。

---

## 📊 监控集成

### 1. Prometheus 监控

可以配置 Prometheus 定期抓取健康检查端点：

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'mine_energy_health'
    metrics_path: '/health'
    static_configs:
      - targets: ['localhost:8088']
    scrape_interval: 30s
```

### 2. Kubernetes 配置

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mine-backend
spec:
  containers:
  - name: backend
    image: mine-backend:latest
    ports:
    - containerPort: 8088
    livenessProbe:
      httpGet:
        path: /health/live
        port: 8088
      initialDelaySeconds: 30
      periodSeconds: 10
      timeoutSeconds: 5
      failureThreshold: 3
    readinessProbe:
      httpGet:
        path: /health/ready
        port: 8088
      initialDelaySeconds: 10
      periodSeconds: 5
      timeoutSeconds: 3
      failureThreshold: 2
```

### 3. Nginx 负载均衡

```nginx
upstream backend {
    server 127.0.0.1:8088 max_fails=3 fail_timeout=30s;
    
    # 健康检查
    check interval=10000 rise=2 fall=3 timeout=5000 type=http;
    check_http_send "GET /health/ready HTTP/1.0\r\n\r\n";
    check_http_expect_alive http_2xx;
}
```

---

## 🔍 故障排查

### 问题1: `/health` 返回 503

**可能原因**：
- 数据库连接失败
- Redis 连接失败（导致降级）

**解决方法**：
```bash
# 检查所有容器状态
docker compose ps

# 查看后端日志
docker compose logs -f backend

# 检查数据库连接
docker exec -it mine_energy_db psql -U admin -d mine_energy -c "SELECT 1;"

# 检查 Redis 连接
docker exec -it ems_redis redis-cli ping
```

### 问题2: Docker 健康检查失败

**可能原因**：
- 后端服务启动时间过长
- 健康检查端点响应超时

**解决方法**：
```bash
# 查看健康检查日志
docker inspect mine_backend --format='{{json .State.Health}}' | python3 -m json.tool

# 手动测试端点
docker exec mine_backend curl -f http://localhost:8088/health

# 增加启动等待时间（修改 docker-compose.yml）
healthcheck:
  start_period: 30s  # 从 20s 增加到 30s
```

### 问题3: 健康检查返回 "degraded"

**说明**：
- 系统处于降级状态，但核心功能仍可用
- 通常是 Redis 不可用导致

**影响**：
- 缓存功能不可用，性能可能下降
- 核心功能（数据库操作）正常

**解决方法**：
```bash
# 检查 Redis 状态
docker compose ps redis
docker compose logs redis

# 重启 Redis
docker compose restart redis
```

---

## 📝 日志记录

健康检查会在日志中记录详细信息：

```bash
# 查看健康检查相关日志
tail -f logs/ems_app_$(date +%Y-%m-%d).log | grep "健康检查"

# 或使用 Docker 日志
docker compose logs -f backend | grep "健康检查"
```

日志示例：
```
2026-01-12 15:30:00.000 | DEBUG | ✅ 健康检查: 数据库正常
2026-01-12 15:30:00.000 | DEBUG | ✅ 健康检查: Redis正常
2026-01-12 15:30:10.000 | WARNING | ⚠️ 健康检查: Redis连接失败 - Connection refused
2026-01-12 15:30:20.000 | ERROR | ❌ 健康检查: 数据库连接失败 - could not connect to server
```

---

## ✅ 验证清单

完成以下步骤，确认健康检查功能正常：

- [ ] 重启后端服务
- [ ] 运行测试脚本：`./test_health.sh`
- [ ] 访问 http://localhost:8088/health，查看响应
- [ ] 检查 Docker 容器健康状态：`docker compose ps`
- [ ] 在 Swagger UI 中测试健康检查端点
- [ ] 查看健康检查日志，确认无错误

---

## 🎉 下一步

健康检查功能已完成！接下来可以考虑：

1. **添加单元测试**（第二步）
   - 测试健康检查端点
   - 测试各种故障场景

2. **添加 API 限流**（第三步）
   - 防止健康检查端点被滥用
   - 保护系统资源

3. **集成监控系统**
   - Prometheus + Grafana
   - 实时监控系统健康状态
   - 配置告警规则

---

## 📚 相关文档

- [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md) - 项目路线图
- [README.md](README.md) - 项目主文档
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - 故障排查指南

---

**最后更新**：2026-01-12
**版本**：v1.0
