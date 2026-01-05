# 统一配置管理使用指南

## 📋 概述

项目已实现基于 Pydantic Settings 的统一配置管理，所有配置项都可以通过环境变量或 `.env` 文件进行管理。

## 🚀 快速开始

### 1. 创建 .env 文件

```bash
# 复制模板文件
cp env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

### 2. 配置必需项

**必须配置的项：**
- `DATABASE_URL` - 数据库连接URL
- `SECRET_KEY` - JWT密钥（生产环境必须修改！）

**可选配置项：**
- 其他配置项都有合理的默认值，可根据需要修改

### 3. 生成强密钥

```bash
# 使用 Python 生成安全的 SECRET_KEY
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

将生成的密钥复制到 `.env` 文件的 `SECRET_KEY` 项。

## 📝 配置项说明

### 应用基础配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 应用名称 | `APP_NAME` | 煤矿综合能源管理系统 | 应用显示名称 |
| 应用版本 | `APP_VERSION` | 2.0.0 | 应用版本号 |
| 调试模式 | `DEBUG` | False | 开发环境设为 True |

### 数据库配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 数据库URL | `DATABASE_URL` | **必需** | PostgreSQL连接字符串 |

**格式：** `postgresql://用户名:密码@主机:端口/数据库名`

**示例：**
```env
DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy
```

### Redis配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| Redis URL | `REDIS_URL` | redis://localhost:6379/0 | Redis连接字符串 |
| Redis密码 | `REDIS_PASSWORD` | None | 可选，如果需要认证 |

### MQTT配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| MQTT Broker | `MQTT_BROKER` | 127.0.0.1 | MQTT服务器地址 |
| MQTT端口 | `MQTT_PORT` | 1883 | MQTT端口 |
| MQTT用户名 | `MQTT_USERNAME` | None | 可选 |
| MQTT密码 | `MQTT_PASSWORD` | None | 可选 |
| MQTT主题 | `MQTT_TOPIC` | mine/telemetry | 订阅主题 |
| MQTT通配符主题 | `MQTT_TOPIC_WILDCARD` | mine/device/+/telemetry | 通配符主题 |

### JWT认证配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 密钥 | `SECRET_KEY` | **必需** | JWT签名密钥（至少32字符） |
| 算法 | `ALGORITHM` | HS256 | JWT算法 |
| 过期时间 | `ACCESS_TOKEN_EXPIRE_MINUTES` | 300 | Token有效期（分钟） |

⚠️ **重要：** `SECRET_KEY` 在生产环境必须修改！

### CORS配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 允许来源 | `CORS_ORIGINS` | ["http://localhost:5173"] | 前端URL列表 |

**格式：** JSON数组或逗号分隔的字符串

**示例：**
```env
# JSON格式
CORS_ORIGINS=["http://localhost:5173", "http://127.0.0.1:5173"]

# 或逗号分隔
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
```

### 日志配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 日志级别 | `LOG_LEVEL` | INFO | DEBUG/INFO/WARNING/ERROR/CRITICAL |
| 日志目录 | `LOG_DIR` | logs | 日志文件保存目录 |
| 保留天数 | `LOG_RETENTION_DAYS` | 7 | 日志文件保留天数 |

### 服务器配置

| 配置项 | 环境变量 | 默认值 | 说明 |
|--------|---------|--------|------|
| 监听地址 | `HOST` | 0.0.0.0 | 服务器监听地址 |
| 端口 | `PORT` | 8088 | 服务器端口 |
| 工作进程 | `WORKERS` | 1 | 工作进程数（生产环境建议设为CPU核心数） |
| 热重载 | `RELOAD` | False | 是否开启热重载（仅开发环境） |

## 🔧 在代码中使用配置

### 方式1：导入 settings 对象（推荐）

```python
from app.core.settings import settings

# 使用配置
database_url = settings.database_url
secret_key = settings.secret_key
mqtt_broker = settings.mqtt_broker
```

### 方式2：使用快捷导出（向后兼容）

```python
from app.core.settings import DATABASE_URL, SECRET_KEY, MQTT_BROKER

# 直接使用
print(DATABASE_URL)
```

## 🌍 环境配置示例

### 开发环境 (.env.development)

```env
DEBUG=True
DATABASE_URL=postgresql://admin:password123@localhost:5433/mine_energy
REDIS_URL=redis://localhost:6379/0
MQTT_BROKER=127.0.0.1
SECRET_KEY=dev-secret-key-min-32-chars-long
CORS_ORIGINS=["http://localhost:5173"]
RELOAD=True
LOG_LEVEL=DEBUG
```

### 生产环境 (.env.production)

```env
DEBUG=False
DATABASE_URL=postgresql://user:strong_password@db:5432/mine_energy
REDIS_URL=redis://redis:6379/0
MQTT_BROKER=mqtt
SECRET_KEY=your-very-strong-secret-key-here-min-32-chars
CORS_ORIGINS=["https://yourdomain.com"]
RELOAD=False
WORKERS=4
LOG_LEVEL=INFO
```

## 🐳 Docker 环境变量

在 `docker-compose.yml` 中，可以通过环境变量传递配置：

```yaml
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=False
```

或者使用 `.env` 文件（docker-compose 会自动读取）：

```bash
# .env 文件
DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy
SECRET_KEY=your-secret-key
```

## ✅ 配置验证

配置类会自动验证配置项：

- **必需项检查**：`DATABASE_URL` 和 `SECRET_KEY` 必须提供
- **格式验证**：数据库URL格式、密钥长度等
- **警告提示**：使用默认密钥时会发出警告

如果配置有误，应用启动时会立即报错，便于快速定位问题。

## 🔒 安全建议

1. **永远不要提交 .env 文件到版本控制**
   ```bash
   # 确保 .gitignore 包含
   .env
   .env.*
   !.env.example
   ```

2. **使用强密钥**
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **生产环境使用环境变量**
   - 不要在代码中硬编码敏感信息
   - 使用容器编排工具（如 Kubernetes Secrets）管理密钥

4. **限制 CORS 来源**
   - 生产环境只允许实际的前端域名
   - 不要使用 `["*"]`

## 🐛 故障排查

### 问题1：配置不生效

**检查：**
1. `.env` 文件是否在项目根目录
2. 环境变量名称是否正确（不区分大小写）
3. 是否重启了应用

### 问题2：导入错误

**可能原因：**
- Pydantic 版本不兼容

**解决方案：**
```bash
# 检查 Pydantic 版本
pip show pydantic

# 如果使用 Pydantic v2，需要安装 pydantic-settings
pip install pydantic-settings
```

### 问题3：配置验证失败

**检查：**
1. 必需项是否都已配置
2. 格式是否正确（如 DATABASE_URL）
3. 查看错误信息中的具体提示

## 📚 相关文件

- `app/core/settings.py` - 配置类定义
- `env.example` - 配置模板文件
- `app/core/config.py` - 旧的配置加载函数（保留用于报警阈值）

## 🔄 迁移说明

如果从旧配置迁移：

1. 查看旧代码中的硬编码配置
2. 在 `.env` 文件中设置对应值
3. 代码已自动更新为使用新配置系统
4. 旧代码中的 `os.getenv()` 调用已替换为 `settings.xxx`

所有更改都保持向后兼容，不会影响现有功能。

