# CORS配置修复说明

## 问题诊断

### 现象
前端无法连接后端，网络请求失败。

### 根本原因
**CORS配置不匹配** - 前端实际运行端口与后端允许的CORS来源不一致。

- 前端实际运行端口: **3000** 
- 后端CORS允许端口: **5173** (默认Vite端口)
- 结果: 浏览器阻止了所有API请求（CORS错误）

### 检查结果
- ✅ 后端服务健康: `http://localhost:8088/health` 正常响应
- ✅ 后端API正常: `/docs` 可访问
- ✅ 后端端口监听: 8088端口正常工作
- ❌ CORS阻止: 前端3000端口不在允许列表中

---

## 解决方案（选择一种）

### 方案1: 修改后端CORS配置（推荐）

修改 `.env` 文件中的CORS配置，添加3000端口：

```bash
# 编辑 .env 文件
nano .env

# 修改或添加以下行
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5173", "http://127.0.0.1:5173"]
```

然后重启后端服务：

```bash
# 如果是Docker运行
docker compose restart backend

# 如果是本地运行
# Ctrl+C 停止，然后重新启动
python run.py
```

### 方案2: 修改前端端口为5173

修改 `frontend/vite.config.ts`，将端口改回默认的5173：

```typescript
server: {
  host: '0.0.0.0',
  port: 5173,  // 改为5173
  // ...
}
```

然后重启前端服务：

```bash
cd frontend
# Ctrl+C 停止当前服务
npm run dev
```

---

## 如何验证修复

### 1. 检查浏览器控制台
打开浏览器开发者工具（F12），查看Console选项卡，CORS错误应该消失。

### 2. 测试API连接
```bash
# 从前端端口测试（在浏览器Console中执行）
fetch('http://localhost:8088/health')
  .then(r => r.json())
  .then(data => console.log('后端健康检查:', data))
```

### 3. 检查Network选项卡
- 打开Network选项卡
- 刷新页面
- API请求应该返回200状态码（登录前可能是401，这是正常的认证错误）
- 不应该出现 CORS policy 错误

---

## 临时测试方案（不推荐生产使用）

如果只是快速测试，可以临时修改后端CORS为允许所有来源：

```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 临时允许所有来源
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

⚠️ **警告**: 这个配置只能用于开发测试，生产环境必须指定具体的允许来源！

---

## 常见CORS错误信息

如果看到以下错误，说明就是CORS问题：

```
Access to XMLHttpRequest at 'http://localhost:8088/...' from origin 'http://localhost:3000' 
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the 
requested resource.
```

---

## 完整检查清单

在修复后，确认以下各项：

- [ ] 前端能够正常访问 `/health` 端点
- [ ] 登录功能正常工作
- [ ] Dashboard能够加载设备列表
- [ ] WebSocket连接成功（顶部有"实时数据接收中"标签）
- [ ] 浏览器Console没有CORS错误
- [ ] Network选项卡中API请求有正确响应

---

## 进一步排查

如果修复CORS后仍有问题，检查：

1. **前后端URL配置**
   - 前端: `frontend/src/utils/request.ts` 的 baseURL
   - 前端: `frontend/vite.config.ts` 的 proxy 配置

2. **防火墙设置**
   ```bash
   # macOS检查防火墙
   /usr/libexec/ApplicationFirewall/socketfilterfw --getglobalstate
   ```

3. **网络代理**
   - 检查是否使用了VPN或代理
   - 尝试关闭代理后测试

4. **端口占用**
   ```bash
   lsof -i :8088  # 检查后端端口
   lsof -i :3000  # 检查前端端口
   ```

---

## 联系与支持

如果问题仍未解决，请提供：
1. 浏览器Console完整错误信息
2. Network选项卡中失败请求的详细信息
3. 前端和后端的运行日志
