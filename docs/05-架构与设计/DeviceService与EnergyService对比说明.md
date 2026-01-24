# DeviceService vs EnergyService 对比说明

> **版本**: v2.2.0 统一架构  
> **更新**: 2026-01-24

---

## 🎯 核心区别

### DeviceService（设备服务）
**职责**: 管理设备本身 + 整合能源数据操作

### EnergyService（能源服务）
**职责**: 处理能源数据的底层操作 + 碳排放计算

---

## 📊 架构关系

```
┌─────────────────────────────────────┐
│      API 层 (devices.py)            │
│  - POST /devices/                   │
│  - POST /devices/{id}/data          │
│  - GET  /devices/{id}/data          │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      DeviceService                  │
│  ┌───────────────────────────────┐  │
│  │ 设备管理功能                   │  │
│  │ - 创建/查询/更新/删除设备      │  │
│  │ - 智能设备创建                 │  │
│  └───────────────────────────────┘  │
│                                     │
│  ┌───────────────────────────────┐  │
│  │ 能源数据整合功能（调用EnergyService）│
│  │ - report_device_data()        │  │
│  │ - get_device_data()           │  │
│  │ - get_device_statistics()     │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────┐
│      EnergyService                  │
│  - save_energy_data()               │
│  - calculate_carbon_emission()      │
│  - get_energy_data()                │
│  - calculate_statistics()           │
│  - get_carbon_summary()             │
└─────────────────────────────────────┘
```

**关系**: DeviceService 是**上层服务**，调用 EnergyService 来处理能源数据。

---

## 📋 功能对比

### DeviceService（13个方法）

#### 1. 设备管理功能（7个）

| 方法 | 功能 | 用途 |
|-----|------|------|
| `get_all_devices()` | 获取设备列表 | 支持筛选（能源类型、类别、状态） |
| `get_device_by_id()` | 根据ID获取设备 | 获取单个设备详情 |
| `get_device_by_sn()` | 根据序列号获取设备 | 通过序列号查询 |
| `create_device_smart()` | **智能创建设备** | 🆕 自动配置字段 |
| `create_device()` | 传统创建设备 | 向后兼容 |
| `update_device()` | 更新设备信息 | 修改设备属性 |
| `delete_device()` | 删除设备 | 移除设备 |
| `toggle_device_status()` | 切换设备状态 | 启用/禁用设备 |

#### 2. 能源数据整合功能（3个）

| 方法 | 功能 | 说明 |
|-----|------|------|
| `report_device_data()` | **统一数据上报** | 🆕 调用 EnergyService.save_energy_data() |
| `get_device_data()` | 查询设备数据 | 调用 EnergyService.get_energy_data() |
| `get_device_statistics()` | 设备统计分析 | 调用 EnergyService.calculate_statistics() |

#### 3. 设备类型信息（2个）

| 方法 | 功能 | 说明 |
|-----|------|------|
| `get_device_types()` | 获取所有设备类型 | 从 device_registry 获取 |
| `get_device_type_info()` | 获取单个设备类型信息 | 查询设备类型配置 |

---

### EnergyService（7个方法）

#### 1. 能源数据操作（2个）

| 方法 | 功能 | 说明 |
|-----|------|------|
| `save_energy_data()` | **保存能源数据** | 底层保存，自动触发碳排放计算 |
| `get_energy_data()` | 查询能源数据 | 支持时间范围、能源类型筛选 |

#### 2. 碳排放功能（2个）

| 方法 | 功能 | 说明 |
|-----|------|------|
| `calculate_carbon_emission()` | **计算碳排放** | 根据能源消耗自动计算 |
| `get_carbon_emissions()` | 查询碳排放记录 | 支持多维度查询 |
| `get_carbon_summary()` | 碳排放汇总 | 按能源类型统计 |

#### 3. 统计分析（2个）

| 方法 | 功能 | 说明 |
|-----|------|------|
| `calculate_statistics()` | 计算能源统计 | 总消耗、平均值、峰值等 |
| `save_statistics()` | 保存统计结果 | 持久化统计数据 |

---

## 🔑 关键区别

### 1. 职责层次不同

| 特性 | DeviceService | EnergyService |
|-----|--------------|---------------|
| **层次** | 上层（业务层） | 底层（数据层） |
| **职责** | 设备管理 + 数据整合 | 能源数据处理 + 碳排放 |
| **依赖** | 依赖 EnergyService | 不依赖其他服务 |
| **暴露** | 直接被 API 调用 | 通过 DeviceService 间接调用 |

### 2. 数据处理流程

#### DeviceService 的数据上报流程：

```python
# API 调用
POST /devices/1/data
{
  "consumption": 10.5,
  "flow_rate": 2.3
}
    ↓
# DeviceService 处理
def report_device_data(session, device_id, data):
    # 1. 获取设备信息
    device = get_device_by_id(session, device_id)
    
    # 2. 获取设备类型配置
    config = device_registry.get(device.device_type)
    
    # 3. 验证必需字段
    validate_required_fields(config, data)
    
    # 4. 调用 EnergyService 保存数据
    return EnergyService.save_energy_data(
        session, device_id, device.energy_type, 
        consumption, flow_rate, **optional_fields
    )
```

#### EnergyService 的数据保存流程：

```python
# EnergyService 处理
def save_energy_data(session, device_id, energy_type, consumption, ...):
    # 1. 验证设备存在
    device = session.get(Device, device_id)
    
    # 2. 创建 EnergyData 记录
    energy_data = EnergyData(...)
    session.add(energy_data)
    session.commit()
    
    # 3. 自动计算碳排放
    calculate_carbon_emission(session, device_id, energy_type, consumption)
    
    return energy_data
```

### 3. 核心类常量

#### DeviceService
- **无内置常量** - 从 `device_registry` 获取配置

#### EnergyService
- `CARBON_FACTORS` - 碳排放因子字典
- `ENERGY_UNITS` - 能源单位映射

---

## 💡 使用场景

### 何时使用 DeviceService？

#### ✅ 场景 1: 设备管理操作

```python
# 创建设备
device = DeviceService.create_device_smart(
    session,
    name="1号水表",
    sn="WATER001",
    device_type="water_meter"
)

# 查询设备
devices = DeviceService.get_all_devices(
    session,
    energy_type="water",
    is_active=True
)

# 更新设备
DeviceService.update_device(
    session,
    device_id=1,
    name="新名称"
)
```

#### ✅ 场景 2: 统一数据上报（推荐）

```python
# 使用 DeviceService 上报数据（推荐）
DeviceService.report_device_data(
    session,
    device_id=1,
    data={
        "consumption": 10.5,
        "flow_rate": 2.3,
        "pressure": 0.3
    }
)
# 优势：自动验证字段、自动处理能源类型
```

#### ✅ 场景 3: 获取设备相关数据

```python
# 获取设备的历史数据
data = DeviceService.get_device_data(
    session,
    device_id=1,
    start_time=start,
    end_time=end
)

# 获取设备统计
stats = DeviceService.get_device_statistics(
    session,
    device_id=1,
    start_time=start,
    end_time=end
)
```

---

### 何时直接使用 EnergyService？

#### ✅ 场景 1: 跨设备的能源统计

```python
# 查询所有设备的能源数据
all_energy_data = EnergyService.get_energy_data(
    session,
    device_id=None,  # None 表示所有设备
    energy_type="water",
    start_time=start,
    end_time=end
)
```

#### ✅ 场景 2: 碳排放分析

```python
# 获取碳排放汇总
carbon_summary = EnergyService.get_carbon_summary(
    session,
    start_time=start,
    end_time=end,
    device_id=None  # 系统级统计
)

# 查询碳排放记录
emissions = EnergyService.get_carbon_emissions(
    session,
    energy_type="electricity",
    start_time=start,
    end_time=end
)
```

#### ✅ 场景 3: 批量数据处理

```python
# 批量保存能源数据（绕过设备验证）
for record in batch_data:
    EnergyService.save_energy_data(
        session,
        device_id=record['device_id'],
        energy_type=record['energy_type'],
        consumption=record['consumption']
    )
```

---

## 🎯 最佳实践

### 推荐方式（90% 的情况）

```python
# ✅ 通过 DeviceService 操作
# 优势：统一、安全、自动验证

# 创建设备
device = DeviceService.create_device_smart(...)

# 上报数据
DeviceService.report_device_data(session, device_id, data)

# 查询数据
data = DeviceService.get_device_data(session, device_id)
```

### 高级用法（10% 的情况）

```python
# ✅ 直接使用 EnergyService
# 适用于：系统级统计、碳排放分析、批量处理

# 碳排放汇总
summary = EnergyService.get_carbon_summary(session, start, end)

# 跨设备统计
stats = EnergyService.calculate_statistics(
    session,
    device_id=None,  # 系统级
    energy_type="electricity",
    start_time=start,
    end_time=end
)
```

---

## 🔄 v2.2.0 的改进

### 之前（v2.1.0）

```
❌ 问题：两个服务职责不清晰
- DeviceService 只管设备 CRUD
- EnergyService 独立处理能源数据
- API 需要直接调用 EnergyService
```

### 现在（v2.2.0）

```
✅ 改进：DeviceService 成为统一入口
- DeviceService 整合设备管理 + 数据处理
- EnergyService 专注底层能源数据操作
- API 只需调用 DeviceService
```

### 新增功能

| 服务 | 新增方法 | 说明 |
|-----|---------|------|
| DeviceService | `create_device_smart()` | 智能创建，自动配置 |
| DeviceService | `report_device_data()` | 统一数据上报入口 |
| DeviceService | `get_device_data()` | 设备数据查询（整合） |
| DeviceService | `get_device_statistics()` | 设备统计（整合） |

---

## 📝 代码示例

### 完整的数据上报流程

```python
from sqlmodel import Session
from app.core.database import engine
from app.services.device_service import DeviceService

# 1. 创建设备
with Session(engine) as session:
    device = DeviceService.create_device_smart(
        session,
        name="1号水表",
        sn="WATER001",
        device_type="water_meter",
        location="A栋1层"
    )
    print(f"✅ 设备创建: {device.name}")

# 2. 上报数据（推荐方式）
with Session(engine) as session:
    energy_data = DeviceService.report_device_data(
        session,
        device_id=device.id,
        data={
            "consumption": 10.5,  # 消耗量
            "flow_rate": 2.3,     # 瞬时流量
            "pressure": 0.3,      # 压力
            "temperature": 18.5   # 温度
        }
    )
    print(f"✅ 数据上报成功")
    print(f"  - 消耗量: {energy_data.consumption}")
    print(f"  - 已自动计算碳排放")

# 3. 查询数据
with Session(engine) as session:
    data_list = DeviceService.get_device_data(
        session,
        device_id=device.id,
        limit=10
    )
    print(f"✅ 查询到 {len(data_list)} 条数据")

# 4. 统计分析
from datetime import datetime, timedelta
with Session(engine) as session:
    end_time = datetime.now()
    start_time = end_time - timedelta(days=1)
    
    stats = DeviceService.get_device_statistics(
        session,
        device_id=device.id,
        start_time=start_time,
        end_time=end_time
    )
    print(f"✅ 统计数据:")
    print(f"  - 总消耗: {stats['total_consumption']}")
    print(f"  - 平均流量: {stats['avg_flow_rate']}")
```

---

## 🎓 总结

### DeviceService（设备服务）

```
角色: 统一的业务入口
职责: 
  ✅ 设备管理（CRUD）
  ✅ 智能设备创建
  ✅ 数据上报整合
  ✅ 设备类型管理

特点:
  - 面向设备
  - 调用 EnergyService
  - API 直接使用
  - 统一入口
```

### EnergyService（能源服务）

```
角色: 底层数据处理
职责:
  ✅ 能源数据保存
  ✅ 碳排放计算
  ✅ 能源数据查询
  ✅ 统计分析

特点:
  - 面向能源数据
  - 独立服务
  - 通过 DeviceService 间接调用
  - 专注数据处理
```

### 使用建议

```
90% 的情况 → 使用 DeviceService
  - 创建设备
  - 上报数据
  - 查询设备数据
  - 设备统计

10% 的情况 → 直接使用 EnergyService
  - 系统级统计
  - 碳排放分析
  - 跨设备查询
  - 批量处理
```

---

**版本**: v2.2.0  
**更新**: 2026-01-24  
**建议**: 优先使用 DeviceService 作为统一入口
