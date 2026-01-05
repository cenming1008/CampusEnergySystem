# 项目架构优化建议

## 📋 目录
1. [配置管理优化](#1-配置管理优化)
2. [安全性增强](#2-安全性增强)
3. [错误处理机制](#3-错误处理机制)
4. [代码组织优化](#4-代码组织优化)
5. [性能优化](#5-性能优化)
6. [测试覆盖](#6-测试覆盖)
7. [监控与健康检查](#7-监控与健康检查)
8. [部署优化](#8-部署优化)
9. [代码质量提升](#9-代码质量提升)
10. [文档完善](#10-文档完善)

---

## 1. 配置管理优化

### 🔴 当前问题
- 配置分散在多个地方（环境变量、硬编码、JSON文件）
- 敏感信息（密码）硬编码在 `docker-compose.yml`
- 缺少配置验证机制
- 开发/生产环境配置混在一起

### ✅ 优化建议

#### 1.1 统一配置管理
```python
# app/core/config.py (优化后)
from pydantic import BaseSettings, Field
from typing import Optional

class Settings(BaseSettings):
    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")
    
    # Redis配置
    redis_url: str = Field(..., env="REDIS_URL")
    
    # MQTT配置
    mqtt_broker: str = Field(default="127.0.0.1", env="MQTT_BROKER")
    mqtt_port: int = Field(default=1883, env="MQTT_PORT")
    mqtt_username: Optional[str] = Field(default=None, env="MQTT_USERNAME")
    mqtt_password: Optional[str] = Field(default=None, env="MQTT_PASSWORD")
    
    # JWT配置
    secret_key: str = Field(..., env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # 应用配置
    app_name: str = Field(default="Mine Energy System", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    cors_origins: list[str] = Field(
        default=["http://localhost:5173"],
        env="CORS_ORIGINS"
    )
    
    # 日志配置
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

settings = Settings()
```

#### 1.2 使用 .env 文件管理配置
```bash
# .env.example (添加到版本控制)
DATABASE_URL=postgresql://admin:password123@db:5432/mine_energy
REDIS_URL=redis://redis:6379/0
MQTT_BROKER=mqtt
SECRET_KEY=your-secret-key-here-change-in-production
DEBUG=False
CORS_ORIGINS=["http://localhost:5173"]
```

#### 1.3 使用 secrets 管理敏感信息
```yaml
# docker-compose.yml (优化后)
services:
  backend:
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    secrets:
      - db_password
      - jwt_secret

secrets:
  db_password:
    file: ./secrets/db_password.txt
  jwt_secret:
    file: ./secrets/jwt_secret.txt
```

---

## 2. 安全性增强

### 🔴 当前问题
- CORS 配置过于宽松（`allow_origins=["*"]`）
- 密码硬编码在配置文件中
- 缺少请求限流
- WebSocket 没有认证机制
- 缺少输入验证

### ✅ 优化建议

#### 2.1 CORS 配置优化
```python
# app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # 从配置读取
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count"],
)
```

#### 2.2 添加请求限流
```python
# app/core/rate_limit.py
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 使用示例
@router.get("/devices")
@limiter.limit("10/minute")  # 每分钟10次请求
def get_devices(...):
    ...
```

#### 2.3 WebSocket 认证
```python
# app/main.py
@app.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),  # 从查询参数获取token
    session: Session = Depends(get_session)
):
    # 验证token
    try:
        user = await verify_websocket_token(token, session)
    except Exception:
        await websocket.close(code=1008, reason="Unauthorized")
        return
    
    await manager.connect(websocket, user_id=user.id)
    ...
```

#### 2.4 输入验证增强
```python
# 使用 Pydantic 模型进行严格验证
from pydantic import BaseModel, Field, validator

class DeviceCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    sn: str = Field(..., regex=r'^[A-Z0-9_-]+$')
    device_type: str = Field(..., regex=r'^(VENTILATOR|PUMP|COMPRESSOR)$')
    
    @validator('sn')
    def validate_sn(cls, v):
        if len(v) < 3:
            raise ValueError('设备序列号至少3个字符')
        return v.upper()
```

---

## 3. 错误处理机制

### 🔴 当前问题
- 缺少统一的错误处理
- 错误信息不够友好
- 缺少错误日志记录

### ✅ 优化建议

#### 3.1 统一异常类
```python
# app/core/exceptions.py
from fastapi import HTTPException, status

class BaseAPIException(HTTPException):
    """基础API异常"""
    def __init__(self, status_code: int, detail: str, error_code: str = None):
        super().__init__(status_code=status_code, detail=detail)
        self.error_code = error_code

class DeviceNotFoundError(BaseAPIException):
    def __init__(self, device_id: int):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"设备 {device_id} 不存在",
            error_code="DEVICE_NOT_FOUND"
        )

class ValidationError(BaseAPIException):
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
            error_code="VALIDATION_ERROR"
        )
```

#### 3.2 全局异常处理器
```python
# app/main.py
from app.core.exceptions import BaseAPIException
from app.core.logger import logger

@app.exception_handler(BaseAPIException)
async def api_exception_handler(request: Request, exc: BaseAPIException):
    logger.error(f"API异常: {exc.detail} (错误码: {exc.error_code})")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": True,
            "error_code": exc.error_code,
            "message": exc.detail,
            "path": str(request.url)
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "error_code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误",
            "path": str(request.url)
        }
    )
```

---

## 4. 代码组织优化

### 🔴 当前问题
- 业务逻辑和API路由耦合
- 缺少服务层抽象
- 数据库操作直接写在路由中

### ✅ 优化建议

#### 4.1 引入服务层
```python
# app/services/device_service.py
class DeviceService:
    def __init__(self, session: Session):
        self.session = session
    
    def create_device(self, device_data: DeviceCreate) -> Device:
        # 业务逻辑
        device = Device(**device_data.dict())
        self.session.add(device)
        self.session.commit()
        self.session.refresh(device)
        return device
    
    def get_device(self, device_id: int) -> Device:
        device = self.session.get(Device, device_id)
        if not device:
            raise DeviceNotFoundError(device_id)
        return device

# app/api/endpoints/devices.py
@router.post("/", response_model=Device)
def create_device(
    device_data: DeviceCreate,
    session: Session = Depends(get_session)
):
    service = DeviceService(session)
    return service.create_device(device_data)
```

#### 4.2 引入仓储模式（Repository Pattern）
```python
# app/repositories/device_repository.py
class DeviceRepository:
    def __init__(self, session: Session):
        self.session = session
    
    def find_by_id(self, device_id: int) -> Optional[Device]:
        return self.session.get(Device, device_id)
    
    def find_by_sn(self, sn: str) -> Optional[Device]:
        return self.session.exec(
            select(Device).where(Device.sn == sn)
        ).first()
    
    def save(self, device: Device) -> Device:
        self.session.add(device)
        self.session.commit()
        self.session.refresh(device)
        return device
```

---

## 5. 性能优化

### 🔴 当前问题
- 数据库连接池配置不明确
- 缺少查询优化
- 缓存使用不充分
- 没有数据库索引优化

### ✅ 优化建议

#### 5.1 数据库连接池优化
```python
# app/core/database.py
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,           # 连接池大小
    max_overflow=20,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前ping检查
    pool_recycle=3600,     # 连接回收时间（秒）
    echo=settings.debug     # 仅开发环境打印SQL
)
```

#### 5.2 查询优化
```python
# 使用 selectinload 避免 N+1 查询
from sqlmodel import select
from sqlalchemy.orm import selectinload

# 优化前：N+1 查询问题
devices = session.exec(select(Device)).all()
for device in devices:
    data = device.data  # 每次访问都会查询数据库

# 优化后：一次查询
devices = session.exec(
    select(Device).options(selectinload(Device.data))
).all()
```

#### 5.3 缓存策略
```python
# app/core/cache.py
from functools import wraps
from app.core.redis import RedisClient
import json

def cache_result(expire: int = 300):
    """缓存装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # 生成缓存key
            cache_key = f"{func.__name__}:{args}:{kwargs}"
            
            # 尝试从缓存获取
            redis = RedisClient.get_client()
            cached = await redis.get(cache_key)
            if cached:
                return json.loads(cached)
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await redis.setex(
                cache_key,
                expire,
                json.dumps(result, default=str)
            )
            return result
        return wrapper
    return decorator

# 使用示例
@cache_result(expire=600)  # 缓存10分钟
async def get_device_analysis(device_id: int):
    ...
```

#### 5.4 数据库索引优化
```python
# app/models/tables.py
class DeviceData(SQLModel, table=True):
    __tablename__ = "devicedata"
    
    device_id: int = Field(
        primary_key=True,
        foreign_key="device.id",
        index=True  # 添加索引
    )
    timestamp: datetime = Field(
        primary_key=True,
        index=True,  # 时间字段索引
        default_factory=datetime.now
    )
    
    # 创建复合索引（如果经常按device_id和时间查询）
    # 在迁移脚本中添加：
    # CREATE INDEX idx_device_timestamp ON devicedata(device_id, timestamp);
```

---

## 6. 测试覆盖

### 🔴 当前问题
- 完全没有测试代码
- 缺少单元测试、集成测试

### ✅ 优化建议

#### 6.1 测试目录结构
```
tests/
├── __init__.py
├── conftest.py          # pytest配置和fixtures
├── unit/                # 单元测试
│   ├── test_services/
│   ├── test_repositories/
│   └── test_utils/
├── integration/         # 集成测试
│   ├── test_api/
│   └── test_mqtt/
└── e2e/                 # 端到端测试
```

#### 6.2 测试示例
```python
# tests/conftest.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from app.main import app
from app.core.database import get_session

@pytest.fixture
def test_db():
    engine = create_engine("sqlite:///:memory:")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(test_db):
    def override_get_session():
        yield test_db
    app.dependency_overrides[get_session] = override_get_session
    return TestClient(app)

# tests/unit/test_device_service.py
def test_create_device(client):
    response = client.post(
        "/devices",
        json={"name": "测试设备", "sn": "TEST001", "device_type": "VENTILATOR"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == "测试设备"
```

---

## 7. 监控与健康检查

### 🔴 当前问题
- 缺少健康检查端点
- 没有监控指标
- 缺少性能追踪

### ✅ 优化建议

#### 7.1 健康检查端点
```python
# app/api/endpoints/health.py
from fastapi import APIRouter, status
from app.core.database import engine
from app.core.redis import RedisClient
from sqlmodel import text

router = APIRouter()

@router.get("/health")
async def health_check():
    """基础健康检查"""
    return {"status": "healthy"}

@router.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    health = {
        "status": "healthy",
        "checks": {
            "database": "unknown",
            "redis": "unknown",
            "mqtt": "unknown"
        }
    }
    
    # 检查数据库
    try:
        with Session(engine) as session:
            session.exec(text("SELECT 1"))
        health["checks"]["database"] = "healthy"
    except Exception as e:
        health["checks"]["database"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    # 检查Redis
    try:
        redis = RedisClient.get_client()
        await redis.ping()
        health["checks"]["redis"] = "healthy"
    except Exception as e:
        health["checks"]["redis"] = f"unhealthy: {str(e)}"
        health["status"] = "degraded"
    
    return health
```

#### 7.2 添加监控指标
```python
# 使用 Prometheus 客户端
from prometheus_client import Counter, Histogram, generate_latest

# 定义指标
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration')

# 中间件记录指标
@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    request_count.labels(method=request.method, endpoint=request.url.path).inc()
    request_duration.observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type="text/plain")
```

---

## 8. 部署优化

### 🔴 当前问题
- Docker镜像体积大
- 缺少多阶段构建
- 没有健康检查配置
- 缺少资源限制

### ✅ 优化建议

#### 8.1 Dockerfile 优化（多阶段构建）
```dockerfile
# 阶段1：构建依赖
FROM python:3.10-slim as builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# 阶段2：运行环境
FROM python:3.10-slim
WORKDIR /app

# 从构建阶段复制依赖
COPY --from=builder /root/.local /root/.local

# 复制应用代码
COPY . .

# 设置环境变量
ENV PATH=/root/.local/bin:$PATH

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD python -c "import requests; requests.get('http://localhost:8088/health')"

EXPOSE 8088
CMD ["python", "run.py"]
```

#### 8.2 docker-compose.yml 优化
```yaml
services:
  backend:
    build: .
    container_name: mine_backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8088/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.5'
          memory: 512M
    volumes:
      - ./logs:/app/logs  # 日志持久化
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy
```

---

## 9. 代码质量提升

### 🔴 当前问题
- 类型提示不完整
- 缺少文档字符串
- 代码格式不统一

### ✅ 优化建议

#### 9.1 添加类型提示
```python
# 使用 mypy 进行类型检查
# requirements-dev.txt
mypy>=1.0.0
types-redis>=4.5.0

# 所有函数添加类型提示
def process_data(
    payload_str: str,
    topic: str | None = None,
    broadcast_callback: Callable[[dict], None] | None = None
) -> None:
    ...
```

#### 9.2 添加文档字符串
```python
def process_data(
    payload_str: str,
    topic: str | None = None,
    broadcast_callback: Callable[[dict], None] | None = None
) -> None:
    """
    处理MQTT消息数据。
    
    Args:
        payload_str: MQTT消息的JSON字符串
        topic: MQTT主题，用于提取设备编码
        broadcast_callback: WebSocket广播回调函数
        
    Raises:
        json.JSONDecodeError: 当payload_str不是有效的JSON时
        ValueError: 当无法确定device_id时
        
    Example:
        >>> process_data('{"device_id": 1, "voltage": 380}', 
        ...             broadcast_callback=callback)
    """
    ...
```

#### 9.3 代码格式化工具
```bash
# 使用 black 格式化代码
pip install black isort flake8

# .pre-commit-config.yaml
repos:
  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
```

---

## 10. 文档完善

### 🔴 当前问题
- API文档可能不够详细
- 缺少架构图
- 缺少开发指南

### ✅ 优化建议

#### 10.1 API文档增强
```python
# 使用更详细的OpenAPI配置
app = FastAPI(
    title="煤矿综合能源管理系统",
    description="""
    ## 功能模块
    
    - 设备管理：设备的增删改查
    - 实时监控：通过WebSocket推送实时数据
    - 数据分析：能耗分析和报表
    - 故障诊断：FDD算法检测设备故障
    """,
    version="2.0.0",
    contact={
        "name": "技术支持",
        "email": "support@example.com"
    },
    license_info={
        "name": "MIT",
    },
)

# 路由文档
@router.post(
    "/devices",
    response_model=Device,
    summary="创建设备",
    description="创建一个新的设备记录",
    response_description="创建成功的设备信息",
    tags=["设备管理"]
)
```

#### 10.2 添加架构图
- 使用 Mermaid 或 PlantUML 绘制系统架构图
- 数据流图
- 部署架构图

---

## 📊 优化优先级

### 🔥 高优先级（立即实施）
1. ✅ 配置管理统一化（使用Pydantic Settings）
2. ✅ 安全性增强（CORS、限流、WebSocket认证）
3. ✅ 错误处理机制（统一异常处理）
4. ✅ 健康检查端点

### ⚡ 中优先级（近期实施）
5. ✅ 服务层抽象（解耦业务逻辑）
6. ✅ 性能优化（连接池、缓存、索引）
7. ✅ 测试覆盖（单元测试、集成测试）
8. ✅ Docker优化（多阶段构建）

### 📈 低优先级（长期优化）
9. ✅ 监控指标（Prometheus）
10. ✅ 代码质量工具（mypy、black）
11. ✅ 文档完善

---

## 🚀 实施建议

1. **分阶段实施**：不要一次性改动太多，按优先级逐步优化
2. **保持向后兼容**：优化时确保不影响现有功能
3. **充分测试**：每次优化后都要进行测试
4. **文档同步**：优化后及时更新文档

---

## 📝 总结

当前项目架构整体良好，但在配置管理、安全性、错误处理、测试覆盖等方面有较大优化空间。建议按照优先级逐步实施，重点关注安全性和稳定性。


