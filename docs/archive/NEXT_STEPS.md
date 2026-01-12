# 📋 下一步行动指南

## ✅ 已完成
- ✅ 后端代码全面重构（33 个文件）
- ✅ 架构分层优化（API/Service/Core/Model）
- ✅ 统一异常处理和响应格式
- ✅ 完善日志和配置管理
- ✅ 编写完整的文档和规范

---

## 🚀 立即可用

### 1. 启动后端服务
```bash
cd /www/wwwroot/MineEnergySystem

# 启动所有服务（包含数据库、Redis、MQTT、后端）
docker-compose up -d

# 或者单独启动后端（需要先启动依赖服务）
./venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. 访问 API 文档
打开浏览器访问：
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. 测试 WebSocket 连接
```javascript
const ws = new WebSocket('ws://localhost:8000/ws');
ws.onmessage = (event) => {
  console.log('实时数据:', JSON.parse(event.data));
};
```

---

## 📚 推荐阅读顺序

如果你是新成员加入项目，建议按以下顺序阅读文档：

1. **README.md** - 项目整体介绍
2. **QUICK_START_REFACTORED.md** - 快速上手指南
3. **app/README.md** - 后端目录结构和架构说明
4. **CODE_STYLE_GUIDE.md** - 代码规范（开发前必读）
5. **REFACTORING_SUMMARY.md** - 重构总结
6. **REFACTORING_COMPLETE.md** - 完整的重构报告

---

## 🛠️ 常见开发任务

### 添加新的 API 端点
```bash
# 1. 在 Service 层添加业务逻辑
vim app/services/your_service.py

# 2. 创建 API 端点
vim app/api/endpoints/your_endpoint.py

# 3. 在 main.py 注册路由
vim app/main.py

# 4. 测试
curl http://localhost:8000/your_endpoint
```

### 添加新的数据模型
```bash
# 1. 在 models/tables.py 添加模型定义
vim app/models/tables.py

# 2. 生成数据库迁移（如果使用 Alembic）
alembic revision --autogenerate -m "Add new model"
alembic upgrade head

# 3. 在 models/__init__.py 导出
vim app/models/__init__.py
```

### 修改配置
```bash
# 1. 在 core/settings.py 添加配置项
vim app/core/settings.py

# 2. 在 .env 文件设置环境变量
vim .env

# 3. 重启服务生效
docker-compose restart backend
```

### 查看日志
```bash
# 应用日志
tail -f logs/ems_app_$(date +%Y-%m-%d).log

# 错误日志
tail -f logs/ems_error_$(date +%Y-%m-%d).log

# Docker 日志
docker-compose logs -f backend
```

---

## 🧪 推荐的后续优化

### 高优先级（建议 1-2 周内完成）

#### 1. 添加单元测试
```bash
# 创建测试目录
mkdir -p tests/{test_api,test_services,test_core}

# 安装测试依赖
./venv/bin/pip install pytest pytest-cov pytest-asyncio

# 编写测试用例
vim tests/test_services/test_device_service.py
```

**示例测试**：
```python
import pytest
from sqlmodel import Session, create_engine, SQLModel
from app.models import Device
from app.services import DeviceService
from app.core.exceptions import ResourceNotFoundException

@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

def test_get_device_by_id_success(session):
    # 创建测试设备
    device = Device(name="测试设备", sn="TEST001", location="A区")
    session.add(device)
    session.commit()
    session.refresh(device)
    
    # 测试获取设备
    result = DeviceService.get_device_by_id(session, device.id)
    assert result.name == "测试设备"

def test_get_device_by_id_not_found(session):
    # 测试不存在的设备
    with pytest.raises(ResourceNotFoundException):
        DeviceService.get_device_by_id(session, 9999)
```

**运行测试**：
```bash
./venv/bin/pytest tests/ -v --cov=app --cov-report=html
```

#### 2. 添加 API 限流
```bash
# 安装依赖
./venv/bin/pip install slowapi

# 修改 main.py
vim app/main.py
```

**示例代码**：
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 在端点上使用
@router.get("/devices")
@limiter.limit("10/minute")
def get_devices(request: Request, session: Session = Depends(get_session)):
    return DeviceService.get_all_devices(session)
```

#### 3. 添加数据库迁移工具
```bash
# 安装 Alembic
./venv/bin/pip install alembic

# 初始化迁移
./venv/bin/alembic init alembic

# 配置 alembic.ini 和 env.py
vim alembic.ini
vim alembic/env.py

# 生成初始迁移
./venv/bin/alembic revision --autogenerate -m "Initial migration"

# 应用迁移
./venv/bin/alembic upgrade head
```

---

### 中优先级（1-2 个月内完成）

#### 4. 添加性能监控
```bash
# 安装 Prometheus 客户端
./venv/bin/pip install prometheus-fastapi-instrumentator

# 在 main.py 添加监控
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator().instrument(app).expose(app)
```

访问 http://localhost:8000/metrics 查看指标。

#### 5. 添加 CI/CD
创建 `.github/workflows/ci.yml`：
```yaml
name: CI

on:
  push:
    branches: [ main, dev ]
  pull_request:
    branches: [ main, dev ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: timescale/timescaledb:latest-pg14
        env:
          POSTGRES_USER: admin
          POSTGRES_PASSWORD: password123
          POSTGRES_DB: mine_energy_test
        ports:
          - 5432:5432
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov
    
    - name: Run tests
      env:
        DATABASE_URL: postgresql://admin:password123@localhost:5432/mine_energy_test
      run: |
        pytest tests/ -v --cov=app --cov-report=xml
    
    - name: Upload coverage
      uses: codecov/codecov-action@v2
      with:
        files: ./coverage.xml
```

#### 6. 完善 API 文档
在每个端点添加更详细的文档：
```python
@router.get(
    "/{device_id}",
    response_model=Device,
    summary="获取设备详情",
    description="根据设备ID获取设备的详细信息",
    responses={
        200: {
            "description": "成功返回设备信息",
            "content": {
                "application/json": {
                    "example": {
                        "id": 1,
                        "name": "变压器-01",
                        "sn": "TR-001",
                        "location": "A区-1号楼"
                    }
                }
            }
        },
        404: {"description": "设备不存在"}
    }
)
def get_device(device_id: int, session: Session = Depends(get_session)):
    """
    获取指定设备的详细信息。
    
    - **device_id**: 设备的唯一标识符
    
    返回设备的完整信息，包括名称、序列号、位置等。
    """
    return DeviceService.get_device_by_id(session, device_id)
```

---

### 低优先级（长期优化）

#### 7. 添加缓存层
```python
from functools import lru_cache
from app.core.redis import RedisClient

class CacheService:
    @staticmethod
    async def get_or_set(
        key: str,
        fetch_func,
        expire: int = 300
    ):
        redis = RedisClient.get_client()
        cached = await redis.get(key)
        
        if cached:
            return json.loads(cached)
        
        data = fetch_func()
        await redis.setex(key, expire, json.dumps(data))
        return data
```

#### 8. 添加消息队列
使用 Celery 处理异步任务：
```bash
./venv/bin/pip install celery redis

# 创建 celery_app.py
vim app/celery_app.py
```

#### 9. 添加前端单元测试
```bash
cd frontend
npm install -D @vue/test-utils vitest
```

---

## 🔒 安全检查清单

在生产部署前，请确保：

- [ ] 修改 `.env` 文件中的 `SECRET_KEY`（使用强随机字符串）
- [ ] 修改所有默认密码（数据库、Redis、MQTT）
- [ ] 启用 HTTPS（使用 Nginx + Let's Encrypt）
- [ ] 配置防火墙规则（只开放必要端口）
- [ ] 设置 CORS 白名单（不要使用 `*`）
- [ ] 启用 API 限流
- [ ] 定期备份数据库
- [ ] 配置日志轮转和清理
- [ ] 添加健康检查端点（`/health`）
- [ ] 使用环境变量而不是硬编码敏感信息

---

## 📊 性能优化建议

### 数据库优化
```sql
-- 为常用查询字段添加索引
CREATE INDEX idx_devicedata_device_timestamp 
ON devicedata(device_id, timestamp DESC);

CREATE INDEX idx_alarm_device_resolved 
ON alarm(device_id, is_resolved, timestamp DESC);

-- 启用 TimescaleDB 压缩（节省存储空间）
SELECT add_compression_policy('devicedata', INTERVAL '7 days');
```

### 代码优化
```python
# 使用批量操作而不是循环插入
devices = [Device(...) for _ in range(100)]
session.add_all(devices)
session.commit()

# 使用 joinedload 减少查询次数
from sqlmodel import select
from sqlalchemy.orm import joinedload

statement = (
    select(DeviceData)
    .options(joinedload(DeviceData.device))
    .where(DeviceData.device_id == device_id)
)
```

### 缓存优化
```python
# 缓存设备列表（5分钟）
@lru_cache(maxsize=128)
def get_all_devices_cached(cache_key: str):
    return DeviceService.get_all_devices(session)

# 每5分钟刷新一次缓存
cache_key = f"devices_{int(time.time() / 300)}"
devices = get_all_devices_cached(cache_key)
```

---

## 💡 常见问题排查

### 问题 1: 数据库连接失败
```bash
# 检查 PostgreSQL 是否运行
docker-compose ps postgres

# 查看日志
docker-compose logs postgres

# 测试连接
./venv/bin/python -c "
from app.core.database import engine
with engine.connect() as conn:
    print('数据库连接成功')
"
```

### 问题 2: Redis 连接失败
```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 测试连接
docker exec -it mineenergysystem-redis-1 redis-cli ping
```

### 问题 3: MQTT 消息未收到
```bash
# 检查 MQTT 服务
docker-compose ps mqtt

# 订阅测试主题
docker exec -it mineenergysystem-mqtt-1 mosquitto_sub -h localhost -t 'mine/data/#' -v

# 发布测试消息
docker exec -it mineenergysystem-mqtt-1 mosquitto_pub -h localhost -t 'mine/data/1' -m '{"voltage":220}'
```

### 问题 4: WebSocket 连接断开
```bash
# 检查后端日志
tail -f logs/ems_app_*.log | grep WebSocket

# 测试 WebSocket 连接
./venv/bin/python -c "
import asyncio
import websockets

async def test():
    async with websockets.connect('ws://localhost:8000/ws') as ws:
        print('WebSocket 连接成功')
        while True:
            msg = await ws.recv()
            print(f'收到消息: {msg}')

asyncio.run(test())
"
```

---

## 📞 获取帮助

- **代码问题**：查看 `CODE_STYLE_GUIDE.md`
- **API 使用**：访问 http://localhost:8000/docs
- **架构问题**：查看 `app/README.md`
- **部署问题**：查看 `README_SCRIPTS.md`

---

## 🎯 开发路线图

### 短期目标（1-2 个月）
- [ ] 添加完整的单元测试（覆盖率 > 80%）
- [ ] 实现 API 限流和安全加固
- [ ] 添加数据库迁移管理
- [ ] 完善 API 文档和示例

### 中期目标（3-6 个月）
- [ ] 添加性能监控和告警
- [ ] 实现 CI/CD 自动化部署
- [ ] 优化数据库查询性能
- [ ] 添加缓存层

### 长期目标（6-12 个月）
- [ ] 微服务拆分（如果规模扩大）
- [ ] 多租户支持
- [ ] 移动端 App 开发
- [ ] 大数据分析平台集成

---

**祝开发顺利！🚀**

如有问题，请参考项目文档或提交 Issue。

