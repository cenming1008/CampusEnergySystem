# LSTM预测功能完整使用指南

## 📋 目录

1. [快速开始](#快速开始)
2. [环境准备](#环境准备)
3. [数据准备](#数据准备)
4. [模型训练](#模型训练)
5. [模型使用](#模型使用)
6. [高级功能](#高级功能)
7. [最佳实践](#最佳实践)
8. [故障排查](#故障排查)

---

## 🚀 快速开始

### 5分钟快速上手

```bash
# 1. 确保虚拟环境已激活
source venv/bin/activate

# 2. 安装依赖（如果还没安装）
python -m pip install -r requirements.txt

# 3. 生成训练数据（为设备1生成60天数据）
curl -X POST "http://localhost:8088/data-generator/generate/device/1" \
  -H "Content-Type: application/json" \
  -d '{"days": 60, "interval_minutes": 60, "data_type": "load"}'

# 4. 训练LSTM模型
curl -X POST "http://localhost:8088/forecast/lstm/train" \
  -H "Content-Type: application/json" \
  -d '{"prediction_type": "load", "device_id": 1, "days": 60}'

# 5. 使用LSTM进行预测
curl -X POST "http://localhost:8088/forecast/load?device_id=1&hours=24&algorithm=lstm"
```

---

## 🔧 环境准备

### 1. 检查Python环境

```bash
# 检查Python版本（需要3.8+）
python3 --version

# 检查虚拟环境
cd /Users/todo/MineEnergySystem
source venv/bin/activate
```

### 2. 修复虚拟环境（如果pip不可用）

如果虚拟环境中的pip不可用，重新创建虚拟环境：

```bash
# 方法1：使用修复脚本
./scripts/fix_venv.sh

# 方法2：手动重新创建
rm -rf venv
python3 -m venv venv
source venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 3. 安装依赖

```bash
# 激活虚拟环境
source venv/bin/activate

# 安装所有依赖（包括TensorFlow）
python -m pip install -r requirements.txt

# 或单独安装LSTM相关依赖
python -m pip install tensorflow>=2.13.0 scikit-learn>=1.3.0 numpy>=1.24.0 apscheduler>=3.10.0
```

### 4. 验证安装

```bash
python -c "import tensorflow; print('TensorFlow版本:', tensorflow.__version__)"
python -c "import sklearn; print('scikit-learn已安装')"
python -c "import numpy; print('NumPy已安装')"
```

---

## 📊 数据准备

### 1. 检查设备

```bash
# 查看所有设备
GET /devices/

# 如果没有设备，先创建一个
POST /devices/
{
  "name": "测试设备1",
  "sn": "DEV001",
  "device_type": "load",
  "location": "测试区域",
  "is_active": true
}
```

### 2. 生成训练数据

#### 方法A：使用API（推荐）

```bash
# 为指定设备生成数据
POST /data-generator/generate/device/{device_id}
{
  "days": 60,              # 生成60天数据
  "interval_minutes": 60,   # 每小时一个数据点
  "data_type": "load",      # 数据类型：load/solar/wind
  "clear_existing": false   # 是否清除现有数据
}

# 为所有设备生成数据
POST /data-generator/generate/all
{
  "days": 60,
  "interval_minutes": 60
}
```

#### 方法B：使用命令行脚本

```bash
# 为设备1生成60天负荷数据
python scripts/generate_training_data.py --device-id 1 --days 60 --type load

# 为所有设备生成数据
python scripts/generate_training_data.py --all --days 60
```

### 3. 验证数据

```bash
# 查看数据统计
GET /data-generator/stats/{device_id}

# 查看最新数据
GET /telemetry/{device_id}?limit=10
```

**预期结果：**
- 总数据量：约 1440 条（60天 × 24小时）
- 时间范围：最近60天
- 数据完整：电压、电流、功率、能耗都有值

### 4. 数据类型说明

| 类型 | 特点 | 适用场景 |
|------|------|----------|
| **load** | 日周期（白天高、夜间低）、周周期（工作日高、周末低） | 一般用电设备 |
| **solar** | 强日周期（白天有功率、夜间为0）、中午最高 | 光伏发电设备 |
| **wind** | 相对稳定但有较大波动（±30%） | 风力发电设备 |

### 5. 推荐配置

| 场景 | 数据天数 | 数据间隔 | 数据点数 | 训练时间 |
|------|---------|---------|---------|---------|
| **快速测试** | 30天 | 60分钟 | 720个 | 1-2分钟 |
| **标准配置** | 60天 | 60分钟 | 1440个 | 2-5分钟 |
| **生产环境** | 90天 | 60分钟 | 2160个 | 5-10分钟 |

---

## 🧠 模型训练

### 1. 基础训练

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",    # 预测类型：load/solar/wind
  "device_id": 1,                # 设备ID（可选，None表示系统级）
  "days": 60,                    # 使用最近60天数据
  "use_multivariate": false,     # 是否使用多变量（默认false）
  "version": "v1.0.0",           # 版本号（可选）
  "retrain": false               # 是否强制重新训练
}
```

**响应示例：**
```json
{
  "success": true,
  "message": "LSTM模型训练完成",
  "data": {
    "status": "success",
    "model_path": "models/lstm/load_device_1.h5",
    "train_loss": 0.0023,
    "val_loss": 0.0031,
    "epochs_trained": 42,
    "params": {
      "sequence_length": 24,
      "lstm_units": [64, 32],
      "dropout_rate": 0.2,
      "epochs": 50
    }
  }
}
```

### 2. 自定义超参数

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60,
  "params": {
    "sequence_length": 48,      # 使用48小时序列
    "lstm_units": [128, 64, 32], # 三层LSTM
    "dropout_rate": 0.3,         # 更高的dropout
    "epochs": 100,               # 更多训练轮数
    "batch_size": 64             # 更大的批次
  }
}
```

### 3. 多变量训练

使用电压、电流、功率三个特征进行预测，通常能提升5-15%的准确性：

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60,
  "use_multivariate": true,     # 启用多变量
  "version": "v1.0.0"
}
```

**优势：**
- ✅ 考虑电压和电流对功率的影响
- ✅ 捕捉特征间的相关性
- ✅ 提高预测准确性（通常提升5-15%）

**注意事项：**
- ⚠️ 需要更多计算资源
- ⚠️ 训练时间稍长
- ⚠️ 需要确保所有特征数据完整

### 4. 模型评估

训练完成后，评估模型性能：

```bash
GET /forecast/lstm/evaluate/load?device_id=1&test_days=7
```

**响应示例：**
```json
{
  "success": true,
  "data": {
    "mae": 5.2,      // 平均绝对误差（kW）
    "mape": 4.5,     // 平均绝对百分比误差（%）
    "rmse": 6.8,     // 均方根误差（kW）
    "test_samples": 168
  }
}
```

**性能指标说明：**
- **MAE**：平均绝对误差，越小越好（理想值：< 10% 平均值）
- **MAPE**：平均绝对百分比误差，越小越好（理想值：< 15%）
- **RMSE**：均方根误差，越小越好

---

## 🎯 模型使用

### 1. 基础预测

```bash
POST /forecast/load?device_id=1&hours=24&algorithm=lstm
```

**参数说明：**
- `device_id`: 设备ID
- `hours`: 预测未来多少小时（1-168）
- `algorithm`: 预测算法（`lstm` 或 `moving_average`）

**响应示例：**
```json
{
  "success": true,
  "data": {
    "device_id": 1,
    "predictions": [
      {
        "forecast_time": "2024-01-08T10:00:00",
        "predicted_value": 125.5,
        "confidence": 0.85
      },
      ...
    ],
    "algorithm": "lstm",
    "count": 24
  }
}
```

### 2. Python代码示例

```python
import requests

BASE_URL = "http://localhost:8088"
TOKEN = "your_jwt_token"

headers = {"Authorization": f"Bearer {TOKEN}"}

# 1. 训练模型
response = requests.post(
    f"{BASE_URL}/forecast/lstm/train",
    json={
        "prediction_type": "load",
        "device_id": 1,
        "days": 60
    },
    headers=headers
)
print(response.json())

# 2. 使用LSTM预测
response = requests.post(
    f"{BASE_URL}/forecast/load",
    params={
        "device_id": 1,
        "hours": 24,
        "algorithm": "lstm"
    },
    headers=headers
)
predictions = response.json()["data"]["predictions"]

# 3. 评估模型
response = requests.get(
    f"{BASE_URL}/forecast/lstm/evaluate/load",
    params={"device_id": 1, "test_days": 7},
    headers=headers
)
evaluation = response.json()["data"]
print(f"MAE: {evaluation['mae']} kW")
print(f"MAPE: {evaluation['mape']}%")
```

### 3. TypeScript/JavaScript示例

```typescript
// 训练LSTM模型
const trainLSTM = async (deviceId: number) => {
  const response = await fetch('/forecast/lstm/train', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      prediction_type: 'load',
      device_id: deviceId,
      days: 60
    })
  });
  return await response.json();
};

// 使用LSTM预测
const forecastWithLSTM = async (deviceId: number, hours: number = 24) => {
  const response = await fetch(
    `/forecast/load?device_id=${deviceId}&hours=${hours}&algorithm=lstm`,
    {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      }
    }
  );
  return await response.json();
};
```

---

## 🚀 高级功能

### 1. 定时训练任务

系统可以自动在指定时间训练和更新模型，无需手动操作。

#### 配置

在 `app/core/settings.py` 中：
```python
forecast_auto_update: bool = True  # 启用自动更新
```

#### 默认任务

- **LSTM模型自动训练**：每天凌晨2点执行
  - 训练系统级负荷预测模型
  - 训练各设备的负荷预测模型
  - 训练风光预测模型（如果有数据）

- **预测自动更新**：每小时执行
  - 更新所有预测结果

#### 查看定时任务

```bash
GET /forecast/scheduler/jobs
```

**响应：**
```json
{
  "success": true,
  "data": {
    "jobs": [
      {
        "id": "auto_train_lstm",
        "name": "自动训练LSTM模型",
        "next_run_time": "2024-01-09T02:00:00",
        "trigger": "cron[hour='2', minute='0']"
      },
      {
        "id": "auto_update_forecasts",
        "name": "自动更新预测",
        "next_run_time": "2024-01-08T11:00:00",
        "trigger": "interval[0:60:0]"
      }
    ],
    "count": 2
  }
}
```

### 2. 模型版本管理

支持保存和管理多个版本的模型，可以对比性能并切换版本。

#### 列出所有版本

```bash
GET /forecast/lstm/versions/load?device_id=1
```

**响应：**
```json
{
  "success": true,
  "data": {
    "versions": [
      {
        "version": "v1.0.0",
        "prediction_type": "load",
        "device_id": 1,
        "metrics": {
          "mae": 5.2,
          "mape": 4.5,
          "rmse": 6.8
        },
        "created_at": "2024-01-08T14:30:00",
        "is_active": true
      }
    ],
    "count": 1
  }
}
```

#### 激活指定版本

```bash
POST /forecast/lstm/versions/load/activate
{
  "version": "v1.0.0",
  "device_id": 1
}
```

#### 对比两个版本

```bash
GET /forecast/lstm/versions/load/compare?version1=v1.0.0&version2=v1.1.0&device_id=1
```

**响应：**
```json
{
  "success": true,
  "data": {
    "version1": {...},
    "version2": {...},
    "improvements": {
      "mae": -12.5,    // v2比v1的MAE降低了12.5%
      "mape": -8.3,    // v2比v1的MAPE降低了8.3%
      "rmse": -10.2    // v2比v1的RMSE降低了10.2%
    }
  }
}
```

**使用场景：**
- A/B测试：对比不同算法或超参数的效果
- 模型回滚：如果新版本性能下降，可以回滚到旧版本
- 版本追踪：记录模型演进历史

### 3. 超参数搜索

自动尝试不同的超参数组合，找到最佳配置。

```bash
POST /forecast/lstm/hyperparameter-search
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60
}
```

**搜索空间：**
- `sequence_length`: [24, 48]
- `lstm_units`: [[64, 32], [128, 64]]
- `dropout_rate`: [0.2, 0.3]
- `epochs`: [30, 50]

总共 2 × 2 × 2 × 2 = 16 种组合

**响应示例：**
```json
{
  "success": true,
  "data": {
    "best_params": {
      "sequence_length": 48,
      "lstm_units": [128, 64],
      "dropout_rate": 0.2,
      "epochs": 50,
      "batch_size": 32
    },
    "best_score": 0.0023,
    "all_results": [...],
    "total_tested": 16
  }
}
```

**注意事项：**
- ⚠️ 搜索过程耗时较长（可能需要数小时）
- ⚠️ 会创建多个模型版本
- 💡 建议在非高峰期执行
- 💡 可以先在小数据集上测试

### 4. 完整工作流程

#### 步骤1：初始训练

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "days": 60
}
```

#### 步骤2：超参数优化

```bash
POST /forecast/lstm/hyperparameter-search
{
  "prediction_type": "load",
  "device_id": 1
}
```

#### 步骤3：使用最佳参数训练

```bash
POST /forecast/lstm/train
{
  "prediction_type": "load",
  "device_id": 1,
  "params": {
    "sequence_length": 48,
    "lstm_units": [128, 64],
    ...
  },
  "version": "v1.0.0"
}
```

#### 步骤4：评估和对比

```bash
GET /forecast/lstm/evaluate/load?device_id=1
GET /forecast/lstm/versions/load/compare?version1=v1.0.0&version2=v1.1.0
```

#### 步骤5：激活最佳版本

```bash
POST /forecast/lstm/versions/load/activate
{
  "version": "v1.0.0",
  "device_id": 1
}
```

---

## 💡 最佳实践

### 1. 数据准备策略

- **数据量**：至少30-60天，推荐90天
- **数据质量**：确保数据完整，缺失值会影响训练效果
- **数据频率**：建议每小时一个数据点
- **数据验证**：生成后检查数据统计和趋势

### 2. 模型训练策略

- **首次训练**：使用60-90天数据，默认参数
- **优化训练**：使用超参数搜索找到最佳配置
- **定期重训**：每月重新训练，使用最新数据
- **版本管理**：每次训练保存为新版本

### 3. 单变量 vs 多变量

| 特性 | 单变量 | 多变量 |
|------|--------|--------|
| **计算速度** | 快 | 慢 |
| **准确性** | 一般 | 高（提升5-15%） |
| **适用场景** | 快速迭代、测试 | 生产环境 |
| **建议** | 先用单变量快速验证 | 再用多变量优化 |

### 4. 版本管理策略

- **开发版本**：使用时间戳命名（`v20240108_143000`）
- **稳定版本**：使用语义版本（`v1.0.0`, `v1.1.0`）
- **保留策略**：保留最近10个版本，删除旧版本

### 5. 定时任务配置

- **训练频率**：每天1次（凌晨2点）
- **更新频率**：每小时1次
- **监控**：定期检查任务执行状态

### 6. 预测使用建议

- **短期预测**：1-24小时，LSTM效果最好
- **中期预测**：24-72小时，可结合其他方法
- **长期预测**：超过72小时，准确性会下降

---

## 🔧 故障排查

### 问题1：TensorFlow未安装

```
错误: TensorFlow未安装，无法使用LSTM预测功能
解决: 
  python -m pip install tensorflow scikit-learn
```

### 问题2：虚拟环境pip不可用

```
错误: zsh: command not found: pip
解决: 
  1. 重新创建虚拟环境：./scripts/fix_venv.sh
  2. 或使用：python -m pip install ...
```

### 问题3：历史数据不足

```
错误: 历史数据不足，至少需要100个数据点
解决: 
  1. 生成更多数据：POST /data-generator/generate/device/1
  2. 确保数据天数至少30天
```

### 问题4：模型不存在

```
错误: 模型不存在，请先训练模型
解决: 
  先调用 POST /forecast/lstm/train 训练模型
```

### 问题5：内存不足

```
错误: 训练时内存不足
解决: 
  1. 减少batch_size或sequence_length
  2. 使用更少的训练数据
  3. 关闭其他占用内存的程序
```

### 问题6：设备不存在

```
错误: 设备 1 不存在
解决: 
  1. 先创建设备：POST /devices/
  2. 或使用存在的设备ID
```

### 问题7：数据生成失败

```
错误: 生成数据失败
解决: 
  1. 检查设备是否存在且激活
  2. 检查数据库连接
  3. 查看日志了解详细错误
```

---

## 📊 性能对比

| 方法 | MAE (kW) | MAPE (%) | 训练时间 | 预测时间 |
|------|----------|----------|----------|----------|
| 移动平均 | 8.5 | 7.2 | <1s | <1ms |
| 线性回归 | 7.2 | 6.1 | <1s | <1ms |
| **LSTM（单变量）** | **5.2** | **4.5** | 2-5min | 10-50ms |
| **LSTM（多变量）** | **4.5** | **3.8** | 5-10min | 15-70ms |

*注：实际性能取决于数据特征和模型配置*

---

## ⚙️ 配置项

在 `app/core/settings.py` 中配置：

```python
# 预测配置
forecast_horizon_hours: int = 24
forecast_interval_minutes: int = 60
forecast_history_days: int = 30
forecast_algorithm: str = "moving_average"
forecast_auto_update: bool = True

# LSTM配置
forecast_lstm_enabled: bool = True
forecast_lstm_sequence_length: int = 24
forecast_lstm_units: str = "64,32"
forecast_lstm_epochs: int = 50
```

---

## 📁 文件结构

```
app/
├── services/
│   ├── lstm_adapter.py               # LSTM适配器（连接后端和独立模块）
│   ├── scheduler_service.py          # 定时任务服务
│   └── data_generator.py             # 数据生成服务

lstm_forecast/                         # 独立的LSTM模块
├── service.py                         # LSTM核心服务
├── version_manager.py                 # 模型版本管理
└── __init__.py
├── api/endpoints/
│   ├── forecast.py                   # 预测API端点
│   └── data_generator.py             # 数据生成API
└── models/
    └── tables.py                     # Prediction表

models/
├── lstm/                             # LSTM模型文件
│   └── {type}_device_{id}.h5
└── scalers/                          # 数据标准化器
    └── {type}_device_{id}.pkl

scripts/
├── generate_training_data.py         # 数据生成脚本
└── fix_venv.sh                       # 虚拟环境修复脚本
```

---

## 🎓 下一步

完成基础训练后，可以：

1. **优化模型**：使用超参数搜索
2. **版本管理**：保存多个版本进行对比
3. **定时训练**：设置自动训练任务
4. **前端集成**：在UI中展示预测结果
5. **生产部署**：配置定时任务和监控

---

## ⚠️ 注意事项

1. **计算资源**：LSTM训练需要较多计算资源，建议在GPU上训练
2. **数据质量**：数据质量直接影响模型效果
3. **过拟合**：注意监控验证集损失，避免过拟合
4. **模型更新**：定期重新训练以保持模型准确性
5. **回退机制**：系统会自动回退到简单算法，确保服务可用性
6. **磁盘空间**：模型文件较大，注意磁盘空间
7. **系统时间**：定时任务依赖系统时间，确保时间准确

---

## 📚 相关资源

- [TensorFlow官方文档](https://www.tensorflow.org/)
- [Keras LSTM指南](https://keras.io/api/layers/recurrent_layers/lstm/)
- [时间序列预测最佳实践](https://www.tensorflow.org/tutorials/structured_data/time_series)

---

## 💬 获取帮助

如果遇到问题：

1. 查看本文档的[故障排查](#故障排查)部分
2. 检查系统日志：`logs/`
3. 查看API响应中的错误信息
4. 验证数据质量和设备状态

---

**最后更新：** 2024-01-08
