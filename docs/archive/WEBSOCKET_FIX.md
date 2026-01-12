# WebSocket 连接问题修复指南

## 🔍 问题诊断

如果 WebSocket 无法连接，请按以下步骤检查：

### 1. 检查后端服务是否运行

```bash
# 检查 Docker 容器状态
docker compose ps

# 检查后端 API 是否可访问
curl http://localhost:8088/docs

# 查看后端日志
docker compose logs -f backend
```

**如果后端未运行，请执行：**
```bash
cd /Users/todo/MineEnergySystem
./start.sh
# 或
docker compose up -d
```

### 2. 检查端口占用

```bash
# 检查后端端口
lsof -i :8088

# 检查前端端口
lsof -i :3000
```

### 3. 测试 WebSocket 端点

```bash
# 使用 curl 测试 WebSocket 升级
curl -i -N \
  -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Version: 13" \
  -H "Sec-WebSocket-Key: dGhlIHNhbXBsZSBub25jZQ==" \
  http://localhost:8088/ws
```

应该返回 `HTTP/1.1 101 Switching Protocols`

## 🔧 修复方案

### 方案 1: 重启所有服务（推荐）

```bash
# 停止所有服务
docker compose down

# 重新启动
docker compose up -d

# 等待服务就绪（约 10-20 秒）
sleep 10

# 检查服务状态
docker compose ps
```

### 方案 2: 检查 Vite 代理配置

确保 `frontend/vite.config.ts` 中的 WebSocket 代理配置正确：

```typescript
'/ws': {
  target: 'http://localhost:8088',
  ws: true,
  changeOrigin: true,
  secure: false
}
```

然后重启前端开发服务器：
```bash
cd frontend
npm run dev
```

### 方案 3: 使用直接连接（绕过 Vite 代理）

如果 Vite 代理有问题，前端会自动切换到直接连接后端。

你也可以在浏览器控制台手动切换：
```javascript
// 在浏览器控制台执行
const socketStore = useSocketStore()
socketStore.toggleConnectionMode()
```

### 方案 4: 检查 CORS 配置

确保 `docker-compose.yml` 中的 CORS 配置包含前端地址：

```yaml
- CORS_ORIGINS=["http://localhost:5173","http://127.0.0.1:5173","http://localhost:3000","http://127.0.0.1:3000"]
```

修改后需要重启后端：
```bash
docker compose restart backend
```

## 🐛 常见错误及解决方案

### 错误 1: `WebSocket connection to 'ws://127.0.0.1:3000/ws' failed`

**原因：** Vite 代理未正确转发 WebSocket 请求

**解决方案：**
1. 检查后端服务是否运行
2. 检查 Vite 配置中的 WebSocket 代理设置
3. 重启前端开发服务器

### 错误 2: `Code: 1006 (异常关闭)`

**原因：** 后端服务未运行或网络连接问题

**解决方案：**
1. 检查后端服务：`docker compose ps`
2. 查看后端日志：`docker compose logs backend`
3. 确保端口 8088 未被占用

### 错误 3: `CORS policy: No 'Access-Control-Allow-Origin' header`

**原因：** CORS 配置未包含前端地址

**解决方案：**
1. 更新 `docker-compose.yml` 中的 CORS_ORIGINS
2. 重启后端服务：`docker compose restart backend`

## 📋 完整启动流程

```bash
# 1. 启动后端服务
cd /Users/todo/MineEnergySystem
./start.sh

# 2. 等待服务就绪（约 10-20 秒）
sleep 15

# 3. 验证后端服务
curl http://localhost:8088/docs

# 4. 启动前端开发服务器
cd frontend
npm run dev

# 5. 打开浏览器访问
# http://localhost:3000 或 http://127.0.0.1:3000
```

## 🔍 调试技巧

### 在浏览器控制台查看详细信息

打开浏览器开发者工具（F12），查看 Console 标签页，会显示详细的 WebSocket 连接信息：

- 连接地址
- 环境信息
- 错误详情
- 重连尝试

### 查看后端 WebSocket 日志

```bash
docker compose logs -f backend | grep -i websocket
```

### 测试 WebSocket 连接

在浏览器控制台执行：
```javascript
const ws = new WebSocket('ws://localhost:8088/ws');
ws.onopen = () => console.log('✅ 连接成功');
ws.onerror = (e) => console.error('❌ 连接失败', e);
ws.onmessage = (e) => console.log('📨 收到消息', e.data);
```

## ✅ 验证修复

修复后，你应该看到：

1. **浏览器控制台：** `✅ [WebSocket] 连接成功`
2. **仪表盘页面：** 显示 "● 实时数据接收中"（绿色标签）
3. **数据更新：** 实时监控数据正常更新

如果问题仍然存在，请检查：
- 后端服务日志
- 浏览器控制台错误信息
- 网络连接和防火墙设置
