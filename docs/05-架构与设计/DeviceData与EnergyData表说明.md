# DeviceData 与 EnergyData 表使用说明

## 📊 表格对比

### DeviceData 表（旧表）

```python
class DeviceData(SQLModel, table=True):
    """设备遥测数据（时序表）- 电力数据。"""
    __tablename__ = "devicedata"
    
    device_id: int
    timestamp: datetime
    voltage: float      # 电压(V)
    current: float      # 电流(A)
    power: float        # 功率(kW)
    energy: float       # 电能(kWh)
```

**特点：**
- ⚡ 专门用于**电力设备**
- 📌 字段固定（电压、电流、功率、电能）
- 🏢 **旧版本遗留**的表
- ✅ 目前**仍在使用中**

### EnergyData 表（新表）

```python
class EnergyData(SQLModel, table=True):
    """通用能源数据表（时序表）- 支持多种能源类型。"""
    __tablename__ = "energydata"
    
    device_id: int
    timestamp: datetime
    energy_type: str           # 能源类型（电/水/气/热/冷/蒸汽）
    
    # 通用字段
    consumption: float         # 消耗量
    flow_rate: Optional[float] # 瞬时流量/功率
    
    # 电力专用字段
    voltage: Optional[float]
    current: Optional[float]
    power_factor: Optional[float]
    
    # 水/气专用字段
    pressure: Optional[float]
    temperature: Optional[float]
    
    # 热力专用字段
    supply_temp: Optional[float]
    return_temp: Optional[float]
    heat_flow: Optional[float]
    
    # 质量指标
    quality_index: Optional[float]
```

**特点：**
- 🌐 支持**所有能源类型**（电/水/气/热/冷/蒸汽）
- 📊 字段灵活（根据能源类型使用不同字段）
- 🆕 **v2.x 版本新增**
- ✅ **推荐使用**

---

## ❓ DeviceData 是否已废弃？

### 答案：❌ 没有废弃，仍在使用！

**当前状态（v2.2.0）：**

```
┌─────────────────────────────────────────┐
│       DeviceData (旧表)                  │
│  ✅ 保留使用                             │
│  ✅ 用于电力设备数据                     │
│  ✅ 向后兼容                             │
│  ⚠️  不推荐新项目使用                    │
└─────────────────────────────────────────┘
              +
┌─────────────────────────────────────────┐
│       EnergyData (新表)                  │
│  ✅ 推荐使用                             │
│  ✅ 支持所有能源类型                     │
│  ✅ 未来的主要数据表                     │
└─────────────────────────────────────────┘
```

---

## 🔍 哪些地方还在使用 DeviceData？

### 1. API 端点

#### `/telemetry` - 遥测数据端点

```python
# app/api/endpoints/telemetry.py

@router.post("/", response_model=DeviceData)
def upload_telemetry(data: DeviceData, session: Session = Depends(get_session)):
    """接收设备上传的遥测数据"""
    return process_device_data(
        session=session,
        device_id=data.device_id,
        voltage=data.voltage,
        current=data.current,
        power=data.power,
        energy=data.energy,
        timestamp=data.timestamp
    )

@router.get("/{device_id}", response_model=List[DeviceData])
def get_device_history(device_id: int, limit: int = 50, ...):
    """获取设备历史数据"""
```

### 2. 数据处理服务

#### `data_processor.py`

```python
# app/services/data_processor.py

def process_device_data(...) -> DeviceData:
    """处理电力设备数据并生成报警"""
    new_record = DeviceData(
        device_id=device_id,
        voltage=voltage,
        current=current,
        power=power,
        energy=energy,
        timestamp=timestamp,
    )
    session.add(new_record)
    # ... 报警逻辑
    return new_record
```

### 3. 分析服务

#### `analysis_service.py`

```python
# app/services/analysis_service.py

def get_energy_statistics(...):
    """能源统计分析（使用 DeviceData）"""
    statement = (
        select(
            func.date_trunc('hour', DeviceData.timestamp).label('hour'),
            func.sum(DeviceData.energy).label('total_energy'),
            func.avg(DeviceData.power).label('avg_power')
        )
        .where(DeviceData.device_id == device_id)
        # ...
    )
```

### 4. 故障诊断

#### `fdd_service.py`

```python
# app/services/fdd_service.py

class FDDService:
    def analyze_device_health(...):
        """设备健康度分析（使用 DeviceData）"""
        statement = select(DeviceData).where(
            DeviceData.device_id == device_id
        )
```

### 5. 预测功能

#### `forecast_adapter.py`

```python
# app/services/forecast_adapter.py

def forecast_load(...):
    """负荷预测（使用 DeviceData）"""
    # 从 DeviceData 读取历史电力数据
    statement = select(DeviceData).where(...)
```

### 6. 报表导出

#### `reports.py`

```python
# app/api/endpoints/reports.py

@router.get("/energy/csv")
def export_energy_csv(...):
    """导出能源数据（使用 DeviceData）"""
    statement = select(DeviceData).where(...)
```

### 7. 数据生成器

#### `data_generator.py`

```python
# app/api/endpoints/data_generator.py

@router.get("/stats")
def get_generation_stats():
    """查询数据生成统计（统计 DeviceData）"""
    from app.models.tables import DeviceData
    total = session.exec(select(func.count(DeviceData.device_id))).one()
```

---

## 🎯 使用建议

### 旧项目（已有数据）

如果你的项目已经在使用 DeviceData：

✅ **继续使用 DeviceData**
- 保持向后兼容
- 不需要迁移数据
- 现有代码继续工作

⚠️ **可选：逐步迁移到 EnergyData**
- 新功能使用 EnergyData
- 逐步替换旧代码
- 数据双写过渡期

### 新项目（从零开始）

如果你是新项目或新设备：

✅ **推荐使用 EnergyData**
- 支持所有能源类型
- 更灵活的字段设计
- 未来的主力表

✅ **使用统一 API**
```bash
# 使用新的统一接口
POST /devices/{id}/data

# 而不是
POST /telemetry/
```

---

## 🔄 迁移策略

### 策略 1：保持双轨制（推荐）

**适合：** 有历史数据的项目

```python
# 电力设备继续使用 DeviceData
if device.energy_type == EnergyType.ELECTRICITY:
    save_to_devicedata(data)

# 其他能源使用 EnergyData
else:
    save_to_energydata(data)
```

**优点：**
- ✅ 无需迁移历史数据
- ✅ 向后兼容
- ✅ 现有功能不受影响

**缺点：**
- ⚠️ 维护两套表
- ⚠️ 查询需要考虑两个表

### 策略 2：全面迁移到 EnergyData

**适合：** 新项目或愿意迁移的项目

**步骤：**

1. 数据迁移脚本
```python
# 将 DeviceData 数据迁移到 EnergyData
def migrate_devicedata_to_energydata():
    with Session(engine) as session:
        # 读取所有 DeviceData
        old_data = session.exec(select(DeviceData)).all()
        
        # 转换为 EnergyData
        for record in old_data:
            new_record = EnergyData(
                device_id=record.device_id,
                timestamp=record.timestamp,
                energy_type=EnergyType.ELECTRICITY,
                consumption=record.energy,
                flow_rate=record.power,
                voltage=record.voltage,
                current=record.current
            )
            session.add(new_record)
        
        session.commit()
```

2. 更新所有引用
```python
# 替换所有
from app.models.tables import DeviceData
# 为
from app.models.tables import EnergyData
```

3. 移除 DeviceData 表定义（可选）

**优点：**
- ✅ 统一数据结构
- ✅ 简化维护
- ✅ 面向未来

**缺点：**
- ⚠️ 需要迁移历史数据
- ⚠️ 代码改动较大
- ⚠️ 测试工作量大

### 策略 3：仅新功能用 EnergyData

**适合：** 渐进式升级

```python
# 旧功能保持不变
@router.post("/telemetry/")  # 继续使用 DeviceData

# 新功能使用新表
@router.post("/devices/{id}/data")  # 使用 EnergyData
```

**优点：**
- ✅ 风险最低
- ✅ 逐步升级
- ✅ 新旧并存

**缺点：**
- ⚠️ 长期维护两套系统

---

## 📈 未来规划

### 短期（v2.x）

```
✅ DeviceData：保留，向后兼容
✅ EnergyData：推荐，新功能使用
✅ 两者并存
```

### 中期（v3.x）

```
⚠️ DeviceData：标记为 deprecated
✅ EnergyData：主力表
📝 提供迁移工具和文档
```

### 长期（v4.x）

```
❌ DeviceData：可能移除
✅ EnergyData：唯一数据表
🔧 完全统一的架构
```

---

## 🎓 常见问题

### Q1: 我应该删除 DeviceData 吗？

**A:** ❌ 不建议！

原因：
- 很多功能仍在使用
- 删除会导致系统崩溃
- 需要大量代码修改

### Q2: 新设备应该用哪个表？

**A:** ✅ 推荐使用 EnergyData

```python
# 推荐：使用统一接口（自动路由到 EnergyData）
device = DeviceService.create_device_smart(...)
DeviceService.report_device_data(...)
```

### Q3: 两个表的数据能一起查询吗？

**A:** 可以，但需要分别查询

```python
# 方案1：分别查询后合并
electricity_data = session.exec(
    select(DeviceData).where(...)
).all()

other_energy_data = session.exec(
    select(EnergyData).where(...)
).all()

# 方案2：使用统一的查询接口（推荐）
all_data = DeviceService.get_device_data_history(
    session, device_id, start_time, end_time
)
```

### Q4: 数据会重复存储吗？

**A:** ❌ 不会

系统设计：
- 电力设备数据 → DeviceData
- 其他能源数据 → EnergyData
- 不会同时存两个表

### Q5: 未来会删除 DeviceData 吗？

**A:** 🤔 可能，但不是近期

时间表：
- v2.x：保留（当前）
- v3.x：标记为废弃
- v4.x：可能移除（2-3年后）

---

## 📚 总结

### DeviceData 的现状

| 项目 | 状态 |
|------|------|
| 是否废弃 | ❌ 否，仍在使用 |
| 推荐使用 | ⚠️ 不推荐新项目使用 |
| 支持范围 | ⚡ 仅电力设备 |
| 向后兼容 | ✅ 是 |
| 使用场景 | 旧系统、电力设备 |

### 使用决策树

```
你是新项目吗？
├─ 是 → 使用 EnergyData + 统一 API ✅
└─ 否 → 已有 DeviceData 数据吗？
       ├─ 是 → 保持 DeviceData，新功能用 EnergyData ✅
       └─ 否 → 直接用 EnergyData ✅
```

### 核心建议

1. ✅ **不要删除 DeviceData** - 很多功能依赖它
2. ✅ **新项目用 EnergyData** - 更灵活、更强大
3. ✅ **旧项目保持现状** - 向后兼容优先
4. ✅ **逐步迁移** - 风险可控
5. ✅ **使用统一 API** - 自动处理数据路由

---

## 🔗 相关文档

- [统一架构重构说明](./统一架构重构说明.md)
- [版本更新日志 v2.2.0](../CHANGELOG_v2.2.0.md)
- [统一设备管理指南](./02-功能使用/统一设备管理指南.md)
- [数据库表定义](../app/models/tables.py)
