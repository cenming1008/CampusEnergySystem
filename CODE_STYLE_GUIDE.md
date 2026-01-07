# 代码规范指南

## 📋 目录

1. [项目架构原则](#项目架构原则)
2. [代码风格规范](#代码风格规范)
3. [命名规范](#命名规范)
4. [文档规范](#文档规范)
5. [错误处理规范](#错误处理规范)
6. [最佳实践](#最佳实践)

---

## 🏗️ 项目架构原则

### 分层架构

项目采用**四层架构**，各层职责清晰：

```
API层 (endpoints/) → Service层 (services/) → Core层 (core/) → Model层 (models/)
```

**职责划分：**

1. **API层** (`app/api/endpoints/`)
   - 处理HTTP请求和响应
   - 参数验证
   - 调用Service层
   - 返回标准化响应

2. **Service层** (`app/services/`)
   - 封装业务逻辑
   - 数据处理和转换
   - 调用Core层和Model层

3. **Core层** (`app/core/`)
   - 基础设施（数据库、安全、配置）
   - 通用工具函数
   - 异常处理

4. **Model层** (`app/models/`)
   - 数据模型定义
   - ORM映射

---

## 🎨 代码风格规范

### Python代码风格

遵循 **PEP 8** 规范：

```python
# ✅ 正确示例
from typing import List, Optional
from fastapi import APIRouter, Depends

def get_devices(session: Session) -> List[Device]:
    """获取所有设备列表"""
    return DeviceService.get_all_devices(session)


# ❌ 错误示例
def getDevices(s):  # 缺少类型提示和文档字符串
    return s.exec(select(Device)).all()  # 业务逻辑直接写在API层
```

### 代码组织

```python
"""
模块文档字符串：简要说明模块功能
"""
# 1. 标准库导入
from typing import List, Optional
from datetime import datetime

# 2. 第三方库导入
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

# 3. 项目内部导入
from app.core.database import get_session
from app.models.tables import Device
from app.services.device_service import DeviceService

# 4. 常量定义
MAX_LIMIT = 100

# 5. 类和函数定义
router = APIRouter()

@router.get("/")
def get_devices(...):
    pass
```

---

## 📝 命名规范

### 文件命名

- 使用**小写+下划线**：`device_service.py`
- 一个文件一个类或一组相关函数

### 变量和函数命名

```python
# ✅ 正确
device_id = 1
user_name = "admin"
def get_device_by_id(device_id: int) -> Device:
    pass

# ❌ 错误
deviceId = 1  # 不使用驼峰命名
def GetDevice(id):  # 函数名应该小写
    pass
```

### 类命名

```python
# ✅ 正确 - 使用大驼峰
class DeviceService:
    pass

class AlarmService:
    pass

# ❌ 错误
class device_service:  # 应该用大驼峰
    pass
```

### 常量命名

```python
# ✅ 正确 - 全大写+下划线
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30

# ❌ 错误
maxRetryCount = 3  # 应该全大写
```

---

## 📖 文档规范

### 模块文档

每个Python文件开头应有文档字符串：

```python
"""
设备管理服务层
封装设备相关的业务逻辑
"""
```

### 函数文档

```python
def get_device_by_id(session: Session, device_id: int) -> Device:
    """
    根据ID获取设备
    
    Args:
        session: 数据库会话
        device_id: 设备ID
        
    Returns:
        Device: 设备对象
        
    Raises:
        ResourceNotFoundException: 设备不存在时抛出
    """
    device = session.get(Device, device_id)
    if not device:
        raise ResourceNotFoundException("设备", device_id)
    return device
```

### 类文档

```python
class DeviceService:
    """
    设备服务类
    
    提供设备的CRUD操作和状态管理功能
    """
    
    @staticmethod
    def create_device(session: Session, device: Device) -> Device:
        """创建新设备"""
        pass
```

---

## ⚠️ 错误处理规范

### 使用自定义异常

```python
# ✅ 正确 - 使用自定义异常
from app.core.exceptions import ResourceNotFoundException

def get_device(device_id: int) -> Device:
    device = session.get(Device, device_id)
    if not device:
        raise ResourceNotFoundException("设备", device_id)
    return device


# ❌ 错误 - 使用HTTPException
from fastapi import HTTPException

def get_device(device_id: int):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    return device
```

### 异常类型

项目定义的异常类型：

| 异常类 | 状态码 | 使用场景 |
|--------|--------|----------|
| `ResourceNotFoundException` | 404 | 资源不存在 |
| `AuthenticationException` | 401 | 认证失败 |
| `ValidationException` | 422 | 数据验证失败 |
| `DatabaseException` | 500 | 数据库操作失败 |

---

## 🎯 最佳实践

### 1. API端点设计

```python
# ✅ 正确 - 简洁清晰
@router.get("/devices/")
def get_devices(session: Session = Depends(get_session)):
    """获取所有设备列表"""
    return DeviceService.get_all_devices(session)


# ❌ 错误 - 业务逻辑写在API层
@router.get("/devices/")
def get_devices(session: Session = Depends(get_session)):
    statement = select(Device).order_by(Device.id)
    devices = session.exec(statement).all()
    # ... 更多业务逻辑
    return devices
```

### 2. Service层设计

```python
# ✅ 正确 - 使用静态方法封装业务逻辑
class DeviceService:
    @staticmethod
    def get_all_devices(session: Session) -> List[Device]:
        """获取所有设备列表"""
        statement = select(Device).order_by(Device.id)
        return list(session.exec(statement).all())


# ❌ 错误 - 直接在API层写数据库查询
def get_devices(session: Session):
    return session.exec(select(Device)).all()
```

### 3. 类型提示

```python
# ✅ 正确 - 完整的类型提示
from typing import List, Optional

def get_devices(
    session: Session,
    limit: int = 10
) -> List[Device]:
    pass

def find_device(device_id: int) -> Optional[Device]:
    pass


# ❌ 错误 - 缺少类型提示
def get_devices(session, limit=10):
    pass
```

### 4. 数据库会话管理

```python
# ✅ 正确 - 使用依赖注入
@router.get("/devices/")
def get_devices(session: Session = Depends(get_session)):
    return DeviceService.get_all_devices(session)


# ❌ 错误 - 手动管理会话
@router.get("/devices/")
def get_devices():
    with Session(engine) as session:
        return session.exec(select(Device)).all()
```

### 5. 响应格式

```python
# ✅ 正确 - 使用统一响应格式
from app.core.response import success_response

@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    DeviceService.delete_device(session, device_id)
    return success_response(message="设备已删除")


# ❌ 错误 - 自定义响应格式
@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    DeviceService.delete_device(session, device_id)
    return {"ok": True, "msg": "deleted"}  # 格式不统一
```

### 6. 代码注释

```python
# ✅ 正确 - 关键逻辑注释，简洁明了
def calculate_health_score(alarm_count: int) -> int:
    """计算设备健康分数"""
    # 每次报警扣5分，最低0分
    return max(0, 100 - alarm_count * 5)


# ❌ 错误 - 过度注释或无意义注释
def calculate_health_score(alarm_count: int) -> int:
    # 这是一个函数
    # 它计算健康分数
    # 参数是报警次数
    score = 100  # 设置score为100
    score = score - alarm_count * 5  # 用100减去报警次数乘以5
    if score < 0:  # 如果score小于0
        score = 0  # 就把score设为0
    return score  # 返回score
```

### 7. 导入顺序

```python
# ✅ 正确 - 按类别分组，每组内按字母排序
# 标准库
from datetime import datetime
from typing import List, Optional

# 第三方库
from fastapi import APIRouter, Depends
from sqlmodel import Session, select

# 项目内部
from app.core.database import get_session
from app.models.tables import Device
from app.services.device_service import DeviceService


# ❌ 错误 - 混乱的导入顺序
from app.models.tables import Device
from typing import List
from fastapi import APIRouter
from datetime import datetime
```

---

## 🔧 代码示例对比

### 重构前（不规范）

```python
# devices.py
from fastapi import APIRouter, HTTPException
from sqlmodel import Session, select

router = APIRouter()

@router.get("/")
def read_devices(session: Session = Depends(get_session)):
    return session.exec(select(Device).order_by(Device.id)).all()

@router.delete("/{device_id}")
def delete_device(device_id: int, session: Session = Depends(get_session)):
    device = session.get(Device, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="设备不存在")
    session.delete(device)
    session.commit()
    return {"ok": True, "message": f"设备 {device.name} 已删除"}
```

### 重构后（规范）

```python
# devices.py - API层
"""
设备管理API端点
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.core.database import get_session
from app.core.response import success_response
from app.models.tables import Device
from app.services.device_service import DeviceService

router = APIRouter()


@router.get("/", response_model=List[Device])
def get_devices(session: Session = Depends(get_session)):
    """获取所有设备列表"""
    return DeviceService.get_all_devices(session)


@router.delete("/{device_id}")
def delete_device(
    device_id: int,
    session: Session = Depends(get_session)
):
    """删除设备"""
    device = DeviceService.get_device_by_id(session, device_id)
    DeviceService.delete_device(session, device_id)
    return success_response(message=f"设备 {device.name} 已删除")


# device_service.py - Service层
"""
设备管理服务层
封装设备相关的业务逻辑
"""
from typing import List
from sqlmodel import Session, select

from app.models.tables import Device
from app.core.exceptions import ResourceNotFoundException


class DeviceService:
    """设备服务类"""
    
    @staticmethod
    def get_all_devices(session: Session) -> List[Device]:
        """获取所有设备列表"""
        statement = select(Device).order_by(Device.id)
        return list(session.exec(statement).all())
    
    @staticmethod
    def get_device_by_id(session: Session, device_id: int) -> Device:
        """根据ID获取设备"""
        device = session.get(Device, device_id)
        if not device:
            raise ResourceNotFoundException("设备", device_id)
        return device
    
    @staticmethod
    def delete_device(session: Session, device_id: int) -> None:
        """删除设备"""
        device = DeviceService.get_device_by_id(session, device_id)
        session.delete(device)
        session.commit()
```

---

## 📊 总结

遵循以上规范可以确保：

✅ **代码一致性**：所有模块风格统一  
✅ **可维护性**：职责清晰，易于理解和修改  
✅ **可扩展性**：分层架构便于添加新功能  
✅ **可测试性**：业务逻辑独立，便于单元测试  
✅ **专业性**：符合工业级项目标准  

---

## 🔗 相关文档

- [项目架构文档](./ARCHITECTURE.md)
- [项目架构分析](./项目架构分析.md)
- [配置指南](./CONFIG_GUIDE.md)

