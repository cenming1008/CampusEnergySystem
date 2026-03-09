# 后端应用目录说明

## 📁 目录结构

```
app/
├── __init__.py           # Python 包初始化
├── main.py               # FastAPI 应用入口，生命周期与路由注册
│
├── api/                  # API 层：处理 HTTP 请求
│   ├── deps.py           # 依赖注入（认证、数据库会话）
│   └── endpoints/        # API 端点模块
│       ├── auth.py       # 认证接口
│       ├── devices.py    # 设备管理接口
│       ├── alarms.py    # 报警管理接口
│       ├── analysis.py   # 数据分析接口
│       ├── fdd.py        # 故障诊断接口
│       ├── reports.py    # 报表导出接口
│       ├── health.py     # 健康检查（无需认证）
│       ├── forecast.py   # 预测功能
│       ├── data_generator.py  # 数据生成
│       ├── energy.py     # 多能源管理
│       ├── maintenance.py    # 设备维护
│       ├── locations.py  # 位置管理
│       ├── device_groups.py   # 设备分组
│       ├── data_cleanup.py    # 数据清理
│       └── inspection.py # 巡检运维
│
├── core/                 # 核心基础设施层
│   ├── database.py      # 数据库连接与初始化（get_session）
│   ├── error_handlers.py # 全局异常处理器
│   ├── exceptions.py     # 自定义异常类
│   ├── logger.py         # 日志配置（Loguru）
│   ├── redis.py          # Redis 客户端（单例）
│   ├── response.py       # 统一响应格式
│   ├── security.py       # JWT 认证与密码哈希
│   ├── settings.py       # 统一配置（Pydantic，含环境变量）
│   ├── socket_manager.py # WebSocket 连接管理
│   └── device_registry.py # 设备类型注册表（类别、能源类型、必填字段等）
│
├── services/             # 服务层：业务逻辑封装
│   ├── device_service.py      # 设备与设备数据上报
│   ├── energy_service.py      # 能源数据、碳排放、电价与统计
│   ├── alarm_service.py       # 报警业务与阈值检测
│   ├── analysis_service.py    # 单设备分析、今日能耗/费用
│   ├── fdd_service.py         # 故障诊断与健康分
│   ├── device_group_service.py # 设备分组
│   ├── location_service.py    # 位置层级与统计
│   ├── maintenance_service.py # 维护计划与记录
│   ├── inspection_service.py  # 巡检路线/计划/任务/记录
│   ├── forecast_adapter.py    # 预测适配（LSTM/简单算法、数据生成）
│   ├── scheduler_service.py   # 定时任务（LSTM 训练、预测更新、数据清理）
│   ├── data_cleanup_service.py # 过期数据清理
│   ├── mqtt_worker.py         # MQTT 消息接收、落库、报警、WebSocket 回调
│   └── mqtt_publisher.py      # MQTT 控制指令下发
│
└── models/               # 数据模型层
    └── tables.py         # SQLModel 表定义
```

---

## 🎯 架构分层说明

### 1. API层 (`api/`)
**职责**：
- 处理HTTP请求和响应
- 参数验证（通过Pydantic模型）
- 调用Service层执行业务逻辑
- 返回标准化响应

**规范**：
- 每个端点函数都应有简洁的docstring
- 使用类型提示标注参数和返回值
- 通过依赖注入获取数据库会话和当前用户
- 不要在API层写业务逻辑

**示例**：
```python
@router.get("/", response_model=List[Device])
def get_devices(session: Session = Depends(get_session)):
    """获取所有设备列表"""
    return DeviceService.get_all_devices(session)
```

---

### 2. Service层 (`services/`)
**职责**：
- 封装业务逻辑
- 数据处理和转换
- 调用数据库进行CRUD操作
- 抛出业务异常

**规范**：
- 使用静态方法组织业务逻辑
- 类名统一为 `XXXService`
- 所有方法都应有完整的类型提示和docstring
- 使用自定义异常（不使用HTTPException）
- 使用 `logger` 记录关键操作

**示例**：
```python
class DeviceService:
    """设备服务类"""
    
    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Device:
        """根据ID获取设备"""
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        return device
```

---

### 3. Core层 (`core/`)
**职责**：
- 提供基础设施服务
- 数据库连接管理
- 认证和安全
- 配置管理
- 日志管理
- WebSocket管理

**规范**：
- 这一层的代码应该是高度可复用的
- 不要包含具体的业务逻辑
- 使用单例模式管理全局资源（如Redis、MQTT客户端）
- 所有配置从 `settings.py` 统一读取

---

### 4. Model层 (`models/`)
**职责**：
- 定义数据库表结构
- ORM映射
- 数据验证

**规范**：
- 使用SQLModel定义表
- 每个模型类都应有docstring
- 字段使用合适的类型和约束
- 时间字段使用 `default_factory=datetime.now`

---

## 🔄 数据流转

### 1. 设备数据上报流程
```
MQTT Broker
    ↓
mqtt_worker.py（订阅主题、接收消息）
    ↓
process_data()（解析 payload，解析 device_id）
    ↓
DeviceService.report_device_data() → EnergyService.save_energy_data()（落库）
AlarmService.check_and_create_alarm()（阈值报警）
    ↓
main.py 中注册的 MQTT 回调（run_coroutine_threadsafe）
    ↓
socket_manager.broadcast() → WebSocket（实时推送给前端）
```

### 2. API请求流程
```
前端请求
    ↓
API端点 (参数验证)
    ↓
deps.py (依赖注入：认证 + 数据库会话)
    ↓
Service层 (业务逻辑)
    ↓
Database (数据操作)
    ↓
API端点 (返回响应)
```

---

## 🛠️ 开发规范

### 导入顺序
```python
# 1. 标准库
from datetime import datetime
from typing import List, Optional

# 2. 第三方库
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

# 3. 项目内部
from app.core.database import get_session
from app.models.tables import Device
from app.services.device_service import DeviceService
```

### 命名规范
- **文件名**：小写+下划线 (`device_service.py`)
- **类名**：大驼峰 (`DeviceService`)
- **函数/变量名**：小写+下划线 (`get_device_by_id`)
- **常量名**：全大写+下划线 (`MAX_RETRY_COUNT`)

### 日志使用
```python
from app.core.logger import logger

# 信息日志
logger.info(f"设备 {device_id} 创建成功")

# 警告日志
logger.warning(f"设备 {device_id} 数据异常")

# 错误日志
logger.error(f"数据库操作失败: {e}")

# 异常日志（包含堆栈）
logger.exception(f"未处理异常: {e}")
```

### 异常处理
```python
from app.core.exceptions import ResourceNotFoundException

# 抛出异常
if not device:
    raise ResourceNotFoundException("设备", device_id)

# 异常会被全局处理器自动捕获并转换为标准响应
```

---

## 🔐 安全规范

### 1. 认证保护
需要认证的端点必须添加依赖：
```python
from app.api.deps import get_current_user

@router.get("/")
def protected_endpoint(
    current_user: User = Depends(get_current_user)
):
    # 只有登录用户才能访问
    pass
```

### 2. 密码处理
```python
from app.core.security import get_password_hash, verify_password

# 生成密码哈希
hashed = get_password_hash("plain_password")

# 验证密码
is_valid = verify_password("plain_password", hashed)
```

### 3. JWT Token
```python
from app.core.security import create_access_token

# 生成Token
token = create_access_token(data={"sub": username})
```

---

## 📊 数据库操作

### 1. 使用依赖注入获取会话
```python
from app.core.database import get_session

@router.get("/")
def endpoint(session: Session = Depends(get_session)):
    # session会自动管理，无需手动关闭
    pass
```

### 2. 查询示例
```python
# 查询所有
devices = session.exec(select(Device)).all()

# 条件查询
device = session.exec(
    select(Device).where(Device.id == device_id)
).first()

# 排序和限制
devices = session.exec(
    select(Device)
    .order_by(Device.created_at.desc())
    .limit(10)
).all()
```

### 3. 增删改
```python
# 创建
new_device = Device(name="设备1", sn="SN001", ...)
session.add(new_device)
session.commit()
session.refresh(new_device)

# 更新
device = session.get(Device, device_id)
device.name = "新名称"
session.add(device)
session.commit()

# 删除
device = session.get(Device, device_id)
session.delete(device)
session.commit()
```

---

## 🧪 测试建议

### 单元测试结构
```
tests/
├── test_api/
│   ├── test_auth.py
│   ├── test_devices.py
│   └── ...
├── test_services/
│   ├── test_device_service.py
│   └── ...
└── test_core/
    ├── test_security.py
    └── ...
```

### 测试示例
```python
def test_get_device_by_id():
    # 准备测试数据
    session = TestSession()
    device = Device(name="测试设备", sn="TEST001", ...)
    session.add(device)
    session.commit()
    
    # 调用Service方法
    result = DeviceService.get_device_by_id(session, device.id)
    
    # 断言
    assert result.name == "测试设备"
```

---

## 📝 添加新功能指南

### 1. 添加新的API端点

#### Step 1: 在Service层添加业务逻辑
```python
# app/services/your_service.py
class YourService:
    @staticmethod
    def your_method(session: Session, param: Type) -> ReturnType:
        """方法说明"""
        # 业务逻辑
        pass
```

#### Step 2: 创建API端点
```python
# app/api/endpoints/your_endpoint.py
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.services.your_service import YourService

router = APIRouter()

@router.get("/")
def your_endpoint(session: Session = Depends(get_session)):
    """端点说明"""
    return YourService.your_method(session, param)
```

#### Step 3: 注册路由
在 `app/main.py` 的 `_ROUTERS` 列表中追加一项（需认证路由），或单独 `include_router`（无需认证）：
```python
# app/main.py
# 需认证：在 _ROUTERS 中添加
_ROUTERS = [
    ...
    (your_endpoint, "/your-prefix", "模块名称"),
]
# 无需认证：在“路由注册（无需认证）”区块单独 include_router
```

### 2. 添加新的数据模型

```python
# app/models/tables.py
class YourModel(SQLModel, table=True):
    """模型说明"""
    __tablename__ = "your_table"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    created_at: datetime = Field(default_factory=datetime.now)
```

### 3. 添加新的配置项

```python
# app/core/settings.py
class Settings(BaseSettings):
    # 添加新配置
    your_config: str = Field(
        default="default_value",
        env="YOUR_CONFIG",
        description="配置说明"
    )
```

---

## 🔍 常见问题

### Q1: 如何在Service层使用logger？
```python
from app.core.logger import logger

class YourService:
    @staticmethod
    def your_method():
        logger.info("操作开始")
        # 业务逻辑
        logger.info("操作完成")
```

### Q2: 如何处理业务异常？
```python
from app.core.exceptions import ResourceNotFoundException

# 抛出异常
raise ResourceNotFoundException("资源", resource_id)

# 异常会被自动转换为HTTP 404响应
```

### Q3: 如何添加WebSocket推送？
```python
from app.core.socket_manager import manager

# 广播消息给所有客户端
await manager.broadcast({
    "type": "notification",
    "data": {"message": "更新通知"}
})
```

### Q4: 如何使用Redis缓存？
```python
from app.core.redis import RedisClient

redis = RedisClient.get_client()
await redis.set("key", "value")
value = await redis.get("key")
```

---

## 📚 相关文档

- [文档中心](../docs/README.md)（新手入门、开发部署、架构与设计等）
- [快速启动指南](../docs/01-新手入门/快速启动指南.md)
- [后端功能实现详解](../docs/05-架构与设计/后端功能实现详解.md)
- [本地开发快速参考](../docs/07-快速参考/本地开发快速参考.md)

---

## 🎯 最佳实践总结

1. ✅ **职责分离**：API层不写业务逻辑，Service层不处理HTTP
2. ✅ **依赖注入**：通过FastAPI的Depends管理依赖
3. ✅ **异常处理**：使用自定义异常，由全局处理器统一处理
4. ✅ **日志记录**：关键操作使用logger记录
5. ✅ **类型提示**：所有函数都应有完整的类型提示
6. ✅ **文档字符串**：每个函数/类都应有docstring
7. ✅ **配置管理**：所有配置从settings统一读取
8. ✅ **代码复用**：相同逻辑封装到Service层或Core层

---

**维护者**：MineEnergySystem 团队  
**最后更新**：2026-03

