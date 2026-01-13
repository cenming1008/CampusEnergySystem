# 预测功能使用指南

## 📋 功能概述

系统提供了负荷预测和风光预测（光伏/风电）功能，支持多种预测算法，帮助用户提前了解未来能源需求和生产情况。

## 🎯 功能特性

### 1. 负荷预测
- 基于历史数据预测未来负荷
- 支持单设备预测和系统总负荷预测
- 多种预测算法可选

### 2. 风光预测
- **光伏预测**：考虑日周期特征（白天高、夜间低）
- **风电预测**：考虑季节性波动
- 支持设备级和系统级预测

### 3. 预测算法
- **移动平均法**（moving_average）：简单稳定，适合短期预测
- **线性回归**（linear_regression）：考虑趋势，适合中期预测
- **自定义算法**：可根据需求扩展

## 📊 数据模型

### Prediction 表结构

```python
- id: 主键
- prediction_type: 预测类型（load/solar/wind）
- device_id: 设备ID（可选，None表示系统级）
- forecast_time: 预测时间点
- predicted_value: 预测值（kW）
- confidence: 置信度（0-1）
- actual_value: 实际值（用于评估）
- algorithm: 使用的算法
- created_at: 创建时间
- metadata: 元数据（JSON）
```

## 🔧 配置项

在 `settings.py` 中可配置：

```python
forecast_horizon_hours: int = 24        # 预测时间范围（小时）
forecast_interval_minutes: int = 60     # 预测时间间隔（分钟）
forecast_history_days: int = 30         # 历史数据天数
forecast_algorithm: str = "moving_average"  # 默认算法
forecast_auto_update: bool = True       # 是否自动更新
```

## 🚀 API 接口

### 1. 负荷预测

```http
POST /forecast/load?device_id=1&hours=24&algorithm=moving_average
```

**参数：**
- `device_id` (可选): 设备ID，不提供则预测系统总负荷
- `hours` (可选): 预测时间范围，默认24小时
- `algorithm` (可选): 预测算法，默认使用配置值

**响应：**
```json
{
  "success": true,
  "message": "成功生成 24 个预测点",
  "data": {
    "device_id": 1,
    "predictions": [
      {
        "forecast_time": "2024-01-08T10:00:00",
        "predicted_value": 125.5,
        "confidence": 0.85
      }
    ],
    "forecast_hours": 24,
    "count": 24
  }
}
```

### 2. 风光预测

```http
POST /forecast/renewable/solar?device_id=2&hours=48
POST /forecast/renewable/wind?hours=24
```

**参数：**
- `prediction_type`: 路径参数，solar 或 wind
- `device_id` (可选): 设备ID
- `hours` (可选): 预测时间范围
- `algorithm` (可选): 预测算法

### 3. 获取最新预测

```http
GET /forecast/latest/load?device_id=1&limit=24
```

**参数：**
- `prediction_type`: 路径参数（load/solar/wind）
- `device_id` (可选): 设备ID
- `limit` (可选): 返回数量，默认24

### 4. 预测准确性评估

```http
GET /forecast/accuracy/load?device_id=1&days=7
```

**响应：**
```json
{
  "success": true,
  "data": {
    "total_count": 168,
    "mae": 5.2,      // 平均绝对误差
    "mape": 4.5,     // 平均绝对百分比误差
    "rmse": 6.8      // 均方根误差
  }
}
```

### 5. 历史预测记录

```http
GET /forecast/history/load?device_id=1&limit=100
```

## 💡 使用示例

### Python 示例

```python
import requests

# 1. 进行负荷预测
response = requests.post(
    "http://localhost:8088/forecast/load",
    params={"device_id": 1, "hours": 24},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
predictions = response.json()["data"]["predictions"]

# 2. 获取最新预测结果
response = requests.get(
    "http://localhost:8088/forecast/latest/load",
    params={"device_id": 1, "limit": 24},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# 3. 评估预测准确性
response = requests.get(
    "http://localhost:8088/forecast/accuracy/load",
    params={"device_id": 1, "days": 7},
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
accuracy = response.json()["data"]
print(f"平均绝对误差: {accuracy['mae']} kW")
```

### JavaScript/TypeScript 示例

```typescript
// 负荷预测
const forecastLoad = async (deviceId: number, hours: number = 24) => {
  const response = await fetch(
    `/forecast/load?device_id=${deviceId}&hours=${hours}`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};

// 获取最新预测
const getLatestForecast = async (type: 'load' | 'solar' | 'wind') => {
  const response = await fetch(`/forecast/latest/${type}`);
  return await response.json();
};
```

## 🔄 定时任务（可选）

可以设置定时任务自动更新预测：

```python
from apscheduler.schedulers.background import BackgroundScheduler
from app.services.forecast_service import ForecastService
from app.core.database import SessionLocal

scheduler = BackgroundScheduler()

def update_forecasts():
    """每小时更新一次预测"""
    with SessionLocal() as session:
        # 更新负荷预测
        ForecastService.forecast_load(session, hours=24)
        # 更新风光预测
        ForecastService.forecast_renewable(session, "solar", hours=24)
        ForecastService.forecast_renewable(session, "wind", hours=24)

scheduler.add_job(update_forecasts, 'interval', hours=1)
scheduler.start()
```

## 📈 预测算法说明

### 移动平均法
- **优点**：简单稳定，计算快速
- **缺点**：不考虑趋势，对突变不敏感
- **适用场景**：短期预测（1-24小时）

### 线性回归
- **优点**：考虑趋势，适合中期预测
- **缺点**：假设线性关系，可能不准确
- **适用场景**：中期预测（24-72小时）

### 光伏预测特殊处理
- 考虑日周期：6:00-18:00 为白天，功率较高
- 正午（10:00-14:00）功率最高
- 夜间功率很低（约10%）

### 风电预测特殊处理
- 相对稳定，但有轻微波动
- 考虑季节性因素
- 使用随机种子保持一致性

## 🎯 最佳实践

1. **数据质量**：确保历史数据充足（建议至少30天）
2. **预测频率**：根据业务需求设置更新频率
3. **算法选择**：短期预测用移动平均，中期用线性回归
4. **准确性评估**：定期评估预测准确性，调整算法参数
5. **实际值更新**：及时更新实际值，用于模型优化

## 🔮 未来扩展

可以考虑添加：
- ARIMA 时间序列模型
- LSTM 神经网络模型
- Prophet 预测模型（Facebook）
- 机器学习模型训练和优化
- 多变量预测（考虑天气、节假日等因素）

## ⚠️ 注意事项

1. 预测结果仅供参考，实际值可能因多种因素变化
2. 历史数据不足时，预测准确性会降低
3. 建议定期评估和调整预测模型
4. 系统级预测需要聚合所有设备数据，计算量较大
