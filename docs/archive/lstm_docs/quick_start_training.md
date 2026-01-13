# LSTM模型训练快速开始指南

## 🚀 5分钟快速开始

### 前提条件

1. ✅ 系统已启动（数据库、后端服务运行中）
2. ✅ 至少有一个设备（如果没有，先创建）
3. ✅ 已安装依赖：`pip install tensorflow scikit-learn`

### 步骤1：创建设备（如果还没有）

```bash
POST /devices/
{
  "name": "测试设备1",
  "sn": "DEV001",
  "device_type": "load",
  "location": "测试区域",
  "is_active": true
}
```

### 步骤2：生成训练数据

#### 方法A：使用API（推荐）

```bash
# 为设备1生成60天数据（每小时一个点）
POST /data-generator/generate/device/1
{
  "days": 60,
  "interval_minutes": 60,
  "data_type": "load",
  "clear_existing": false
}
```

#### 方法B：使用命令行脚本

```bash
python scripts/generate_training_data.py --device-id 1 --days 60 --type load
```

#### 方法C：为所有设备生成

```bash
POST /data-generator/generate/all
{
  "days": 60,
  "interval_minutes": 60
}
```

### 步骤3：验证数据

```bash
# 查看数据统计
GET /data-generator/stats/1

# 查看最新数据
GET /telemetry/1?limit=10
```

**预期结果：**
- 总数据量：约 1440 条（60天 × 24小时）
- 时间范围：最近60天
- 数据完整：电压、电流、功率、能耗都有值

### 步骤4：训练LSTM模型

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60,
  "use_multivariate": false,
  "version": "v1.0.0"
}
```

**训练时间：** 约2-5分钟（取决于数据量和硬件）

**预期响应：**
```json
{
  "success": true,
  "data": {
    "status": "success",
    "model_path": "models/lstm/load_device_1.h5",
    "train_loss": 0.0023,
    "val_loss": 0.0031,
    "epochs_trained": 42
  }
}
```

### 步骤5：评估模型

```bash
GET /forecast/lstm/evaluate/load?device_id=1&test_days=7
```

**预期结果：**
- MAE: 5-15 kW（取决于数据特征）
- MAPE: 5-15%
- RMSE: 8-20 kW

### 步骤6：使用模型预测

```bash
POST /forecast/load?device_id=1&hours=24&algorithm=lstm
```

**预期响应：**
```json
{
  "success": true,
  "data": {
    "predictions": [
      {
        "forecast_time": "2024-01-08T11:00:00",
        "predicted_value": 125.5,
        "confidence": 0.85
      },
      ...
    ],
    "count": 24
  }
}
```

## 📊 完整示例流程

### Python完整示例

```python
import requests

BASE_URL = "http://localhost:8088"
TOKEN = "your_jwt_token"  # 先登录获取token

headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. 检查设备
devices = requests.get(f"{BASE_URL}/devices/", headers=headers).json()
print(f"设备列表: {devices}")

if not devices:
    # 创建设备
    device = requests.post(
        f"{BASE_URL}/devices/",
        json={
            "name": "测试设备",
            "sn": "TEST001",
            "device_type": "load",
            "is_active": True
        },
        headers=headers
    ).json()
    device_id = device["id"]
else:
    device_id = devices[0]["id"]

# 2. 生成数据
print("生成训练数据...")
result = requests.post(
    f"{BASE_URL}/data-generator/generate/device/{device_id}",
    json={
        "days": 60,
        "interval_minutes": 60,
        "data_type": "load"
    },
    headers=headers
).json()
print(f"数据生成: {result['message']}")

# 3. 训练模型
print("训练LSTM模型...")
train_result = requests.post(
    f"{BASE_URL}/forecast/lstm/train",
    json={
        "prediction_type": "load",
        "device_id": device_id,
        "days": 60,
        "version": "v1.0.0"
    },
    headers=headers
).json()
print(f"训练结果: {train_result['data']['status']}")

# 4. 评估模型
print("评估模型...")
eval_result = requests.get(
    f"{BASE_URL}/forecast/lstm/evaluate/load",
    params={"device_id": device_id},
    headers=headers
).json()
print(f"MAE: {eval_result['data']['mae']} kW")
print(f"MAPE: {eval_result['data']['mape']}%")

# 5. 进行预测
print("进行预测...")
forecast_result = requests.post(
    f"{BASE_URL}/forecast/load",
    params={
        "device_id": device_id,
        "hours": 24,
        "algorithm": "lstm"
    },
    headers=headers
).json()
print(f"预测完成: {forecast_result['data']['count']} 个预测点")
```

### curl命令示例

```bash
# 设置变量
BASE_URL="http://localhost:8088"
TOKEN="your_token"

# 1. 生成数据
curl -X POST "${BASE_URL}/data-generator/generate/device/1" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "days": 60,
    "interval_minutes": 60,
    "data_type": "load"
  }'

# 2. 训练模型
curl -X POST "${BASE_URL}/forecast/lstm/train" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{
    "prediction_type": "load",
    "device_id": 1,
    "days": 60
  }'

# 3. 预测
curl -X POST "${BASE_URL}/forecast/load?device_id=1&hours=24&algorithm=lstm" \
  -H "Authorization: Bearer ${TOKEN}"
```

## 🎯 推荐配置

### 最小配置（快速测试）

```json
{
  "days": 30,
  "interval_minutes": 60,
  "use_multivariate": false
}
```
- 数据量：720个点
- 训练时间：1-2分钟
- 适合：快速验证功能

### 标准配置（推荐）

```json
{
  "days": 60,
  "interval_minutes": 60,
  "use_multivariate": false
}
```
- 数据量：1440个点
- 训练时间：2-5分钟
- 适合：一般使用场景

### 最佳配置（生产环境）

```json
{
  "days": 90,
  "interval_minutes": 60,
  "use_multivariate": true
}
```
- 数据量：2160个点
- 训练时间：5-10分钟
- 适合：生产环境

## ⚡ 一键生成脚本

创建 `scripts/quick_train.sh`：

```bash
#!/bin/bash
# 一键生成数据并训练模型

DEVICE_ID=${1:-1}
DAYS=${2:-60}

echo "🚀 开始快速训练流程..."
echo "设备ID: ${DEVICE_ID}, 数据天数: ${DAYS}"

# 1. 生成数据
echo "📊 生成训练数据..."
curl -X POST "http://localhost:8088/data-generator/generate/device/${DEVICE_ID}" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"days\": ${DAYS}, \"interval_minutes\": 60, \"data_type\": \"load\"}"

# 2. 训练模型
echo "🧠 训练LSTM模型..."
curl -X POST "http://localhost:8088/forecast/lstm/train" \
  -H "Authorization: Bearer ${TOKEN}" \
  -H "Content-Type: application/json" \
  -d "{\"prediction_type\": \"load\", \"device_id\": ${DEVICE_ID}, \"days\": ${DAYS}}"

# 3. 评估模型
echo "📈 评估模型性能..."
curl -X GET "http://localhost:8088/forecast/lstm/evaluate/load?device_id=${DEVICE_ID}" \
  -H "Authorization: Bearer ${TOKEN}"

echo "✅ 完成！"
```

使用：
```bash
chmod +x scripts/quick_train.sh
./scripts/quick_train.sh 1 60
```

## 🔍 故障排查

### 问题1：设备不存在

```
错误: 设备 1 不存在
解决: 先创建设备或使用存在的设备ID
```

### 问题2：数据生成失败

```
错误: 生成数据失败
解决: 
1. 检查设备是否存在且激活
2. 检查数据库连接
3. 查看日志了解详细错误
```

### 问题3：训练失败 - 数据不足

```
错误: 历史数据不足，至少需要100个数据点
解决: 增加生成数据的天数（至少30天）
```

### 问题4：TensorFlow未安装

```
错误: TensorFlow未安装
解决: pip install tensorflow scikit-learn
```

## 📈 数据质量检查

生成数据后，建议检查：

1. **数据完整性**
   ```bash
   GET /data-generator/stats/1
   ```
   确保数据量符合预期

2. **数据合理性**
   ```bash
   GET /telemetry/1?limit=100
   ```
   检查电压、电流、功率是否在合理范围

3. **数据趋势**
   ```bash
   GET /analysis/1
   ```
   查看数据趋势是否符合预期（日周期、周周期等）

## 🎓 下一步

数据生成和模型训练完成后：

1. **优化模型**：使用超参数搜索
2. **版本管理**：保存多个版本进行对比
3. **定时训练**：设置自动训练任务
4. **前端集成**：在UI中展示预测结果

## 💡 提示

- 首次训练建议使用单变量（`use_multivariate: false`），训练更快
- 数据量足够后，可以尝试多变量预测提升准确性
- 定期重新训练模型，使用最新数据
- 保存好的模型版本，方便回滚
