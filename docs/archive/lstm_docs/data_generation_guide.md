# 数据生成指南

## 📋 概述

在没有真实数据的情况下，系统提供了数据生成工具，可以生成模拟的时序数据用于LSTM模型训练和测试。

## 🎯 生成的数据类型

### 1. 负荷数据（Load）
- **特点**：
  - 日周期：白天（6:00-22:00）功率高，夜间低
  - 周周期：工作日高，周末低
  - 随机波动：±10%
- **适用场景**：一般用电设备

### 2. 光伏数据（Solar）
- **特点**：
  - 强日周期：白天有功率，夜间为0
  - 中午最高：10:00-14:00功率最高
  - 天气影响：随机模拟云层影响（50-100%）
- **适用场景**：光伏发电设备

### 3. 风电数据（Wind）
- **特点**：
  - 相对稳定但有较大波动（±30%）
  - 季节性变化：冬季略高
  - 随机波动较大
- **适用场景**：风力发电设备

## 🚀 使用方法

### 方法1：使用API接口

#### 为指定设备生成数据

```bash
POST /data-generator/generate/device/{device_id}
Content-Type: application/json

{
  "days": 60,
  "interval_minutes": 60,
  "data_type": "load",
  "clear_existing": false
}
```

**参数说明：**
- `days`: 生成数据的天数（1-365）
- `interval_minutes`: 数据间隔，分钟（1-1440）
- `data_type`: 数据类型（load/solar/wind）
- `clear_existing`: 是否清除现有数据

#### 为所有设备生成数据

```bash
POST /data-generator/generate/all
{
  "days": 60,
  "interval_minutes": 60,
  "clear_existing": false
}
```

系统会根据设备类型自动选择数据类型：
- 设备类型包含 "solar" 或 "光伏" → 生成光伏数据
- 设备类型包含 "wind" 或 "风电" → 生成风电数据
- 其他 → 生成负荷数据

#### 查看数据统计

```bash
GET /data-generator/stats/{device_id}
```

#### 清除数据

```bash
DELETE /data-generator/clear/{device_id}?days=30
```

### 方法2：使用命令行脚本

```bash
# 为所有设备生成60天数据
python scripts/generate_training_data.py --all --days 60

# 为指定设备生成数据
python scripts/generate_training_data.py --device-id 1 --days 60 --type load

# 清除现有数据并重新生成
python scripts/generate_training_data.py --device-id 1 --days 90 --clear
```

**参数：**
- `--days`: 生成数据天数
- `--interval`: 数据间隔（分钟）
- `--device-id`: 设备ID
- `--all`: 为所有设备生成
- `--type`: 数据类型（load/solar/wind）
- `--clear`: 清除现有数据

### 方法3：Python代码

```python
from app.core.database import SessionLocal
from app.services.data_generator import DataGenerator

with SessionLocal() as session:
    # 为设备1生成60天负荷数据
    count = DataGenerator.generate_device_data(
        session=session,
        device_id=1,
        days=60,
        interval_minutes=60,
        data_type="load"
    )
    print(f"生成了 {count} 条数据")
```

## 📊 数据特征

### 负荷数据示例

```
时间        电压(V)  电流(A)  功率(kW)
06:00       380      25       10.5
12:00       382      45       28.5
18:00       379      38       24.0
00:00       381      15       8.2
```

**特点：**
- 工作日功率：80-150 kW
- 周末功率：50-100 kW
- 夜间功率：40-80 kW

### 光伏数据示例

```
时间        电压(V)  电流(A)  功率(kW)
06:00       380      5        3.0
12:00       382      180      120.0
18:00       379      20       12.0
00:00       381      0        0.0
```

**特点：**
- 白天功率：0-200 kW（中午最高）
- 夜间功率：0 kW
- 受天气影响波动

### 风电数据示例

```
时间        电压(V)  电流(A)  功率(kW)
任意时间    380      65-85    105-135
```

**特点：**
- 功率相对稳定：100-160 kW
- 波动较大：±30%
- 季节性变化：冬季略高

## 🎯 推荐配置

### LSTM训练数据

**最小要求：**
- 数据天数：30天
- 数据间隔：60分钟
- 数据点数：30 × 24 = 720个

**推荐配置：**
- 数据天数：60-90天
- 数据间隔：60分钟
- 数据点数：1440-2160个

**最佳配置：**
- 数据天数：90-180天
- 数据间隔：30-60分钟
- 数据点数：4320-8640个

### 快速开始

```bash
# 1. 确保有设备（如果没有，先创建）
# 可以通过API或数据库直接创建

# 2. 生成60天数据（每小时一个点）
POST /data-generator/generate/all
{
  "days": 60,
  "interval_minutes": 60
}

# 3. 检查数据统计
GET /data-generator/stats/1

# 4. 开始训练LSTM模型
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60
}
```

## 💡 使用建议

### 1. 数据量建议

- **训练数据**：至少60天，推荐90天
- **测试数据**：7-14天（用于评估）
- **验证数据**：7-14天（训练时自动划分）

### 2. 数据间隔

- **60分钟**：适合大多数场景，数据量适中
- **30分钟**：更精细，但数据量翻倍
- **15分钟**：非常精细，但数据量大，训练慢

### 3. 数据类型选择

- **负荷预测**：使用 `load` 类型
- **光伏预测**：使用 `solar` 类型
- **风电预测**：使用 `wind` 类型

### 4. 多设备场景

如果系统有多个设备，建议：
- 为每个设备生成独立数据
- 使用不同的基础功率值（可通过修改代码实现）
- 保持数据特征一致

## 🔧 自定义数据生成

如果需要自定义数据特征，可以修改 `app/services/data_generator.py`：

```python
# 修改基础功率
base_power = 150.0  # 改为你需要的值

# 修改波动范围
random_factor = random.uniform(0.8, 1.2)  # 调整波动范围

# 修改日周期
day_factor = 1.5  # 调整白天功率倍数
```

## ⚠️ 注意事项

1. **数据覆盖**：如果设备已有数据，新数据会追加，不会覆盖
2. **使用 `clear_existing`**：需要重新生成时，设置此参数为 `true`
3. **数据真实性**：生成的是模拟数据，仅用于训练和测试
4. **数据量**：大量数据生成可能需要一些时间
5. **数据库空间**：确保有足够的数据库空间

## 📈 数据验证

生成数据后，可以通过以下方式验证：

```bash
# 1. 查看数据统计
GET /data-generator/stats/1

# 2. 查看最新数据
GET /telemetry/1?limit=10

# 3. 使用数据分析接口
GET /analysis/1
```

## 🎓 下一步

数据生成后，可以：

1. **训练LSTM模型**
   ```bash
   POST /forecast/lstm/train
   ```

2. **评估模型性能**
   ```bash
   GET /forecast/lstm/evaluate/load?device_id=1
   ```

3. **进行预测**
   ```bash
   POST /forecast/load?device_id=1&algorithm=lstm
   ```

## 🔮 真实数据迁移

当有真实数据后，可以：

1. **清除模拟数据**
   ```bash
   DELETE /data-generator/clear/1
   ```

2. **导入真实数据**
   - 通过MQTT接口
   - 通过数据库直接导入
   - 通过CSV导入脚本

3. **重新训练模型**
   ```bash
   POST /forecast/lstm/train
   {
     "prediction_type": "load",
     "device_id": 1,
     "days": 60,
     "retrain": true
   }
   ```
