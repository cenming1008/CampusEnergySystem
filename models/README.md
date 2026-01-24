# LSTM 模型存储目录

此目录用于存储 LSTM 能源预测模型的训练产物。

## 📁 目录结构

```
models/
├── lstm/          # LSTM 模型文件（.h5, .keras）
├── scalers/       # 数据标准化器（.pkl）
├── versions/      # 模型版本元数据（.json）
└── README.md      # 本文件
```

## 🎯 用途说明

### 1. lstm/ 目录

存储训练好的 LSTM 神经网络模型文件。

**文件格式**：
- `{prediction_type}_{device_id}.h5` - Keras HDF5 格式
- `{prediction_type}_{device_id}.keras` - Keras 原生格式

**示例**：
```
lstm/
├── load_device_1.h5        # 设备1的负载预测模型
├── solar_device_2.h5       # 设备2的光伏预测模型
└── consumption_total.h5    # 总体能耗预测模型
```

### 2. scalers/ 目录

存储数据预处理使用的标准化器对象。

**文件格式**：
- `{prediction_type}_{device_id}.pkl` - Pickle 序列化的 Scaler 对象

**说明**：
- 用于训练前的数据标准化
- 预测时必须使用相同的 Scaler 进行数据转换

**示例**：
```
scalers/
├── load_device_1.pkl       # 对应设备1的标准化器
├── solar_device_2.pkl      # 对应设备2的标准化器
└── consumption_total.pkl   # 对应总体的标准化器
```

### 3. versions/ 目录

存储模型版本信息和元数据。

**文件**：
- `versions_metadata.json` - 所有模型的版本信息

**内容示例**：
```json
{
  "load_device_1": {
    "version": "v1.0.0",
    "trained_at": "2026-01-24T12:00:00",
    "accuracy": 0.95,
    "epochs": 100,
    "batch_size": 32
  }
}
```

## 🔧 模型训练

### 自动训练

系统会自动定期训练模型（通过调度器）：

```python
# app/services/scheduler_service.py
def auto_train_lstm_models():
    """自动训练 LSTM 模型"""
    # 每天凌晨2点自动执行
```

### 手动训练

使用脚本手动训练：

```bash
# 生成训练数据
python scripts/python/generate_training_data.py

# 通过 API 触发训练
curl -X POST http://localhost:8000/api/forecast/train \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "device_1",
    "prediction_type": "load",
    "epochs": 100
  }'
```

## 📊 模型使用

### 加载模型进行预测

```python
from lstm_forecast.service import LSTMForecastService

service = LSTMForecastService()

# 预测未来24小时
predictions = await service.predict(
    device_id="device_1",
    prediction_type="load",
    forecast_hours=24
)
```

## ⚠️ 重要说明

### 1. Git 版本控制

**这些文件不应提交到 Git**：
- ✅ 目录结构会被保留（通过 .gitkeep）
- ❌ 模型文件不会被提交（在 .gitignore 中）
- ❌ Scaler 文件不会被提交（在 .gitignore 中）
- ❌ 元数据文件不会被提交（在 .gitignore 中）

**原因**：
- 模型文件通常很大（几 MB 到几百 MB）
- 这些是训练产物，不是源代码
- 不同环境应该独立训练
- 频繁训练会污染 Git 历史

### 2. 初次部署

首次部署时，此目录是空的（只有 .gitkeep）：

1. **系统会自动创建必要的文件**
2. **无需手动创建模型文件**
3. **训练完成后文件会自动生成**

### 3. 备份策略

虽然不提交到 Git，但应该定期备份模型：

```bash
# 备份模型文件
tar -czf models_backup_$(date +%Y%m%d).tar.gz models/

# 恢复模型
tar -xzf models_backup_20260124.tar.gz
```

## 🔍 故障排查

### 模型文件不存在

**症状**：预测时报错"模型文件不存在"

**解决**：
1. 检查是否已训练模型
2. 运行训练脚本
3. 查看日志确认训练成功

### 模型预测不准确

**可能原因**：
1. 训练数据不足（需要至少30天数据）
2. 数据质量问题（异常值、缺失值）
3. 模型参数需要调优

**解决**：
1. 增加训练数据量
2. 清理异常数据
3. 调整训练参数（epochs、batch_size 等）

### 内存不足

**症状**：训练时内存溢出

**解决**：
1. 减小 batch_size
2. 减少 LSTM 层数或单元数
3. 增加服务器内存

## 📚 相关文档

- [LSTM 预测完整指南](../docs/02-功能使用/LSTM预测完整指南.md)
- [LSTM 服务代码](../lstm_forecast/service.py)
- [模型版本管理](../lstm_forecast/version_manager.py)
- [调度服务](../app/services/scheduler_service.py)

## 🔗 相关资源

- [TensorFlow/Keras 文档](https://www.tensorflow.org/guide/keras)
- [LSTM 网络介绍](https://colah.github.io/posts/2015-08-Understanding-LSTMs/)
- [时间序列预测](https://www.tensorflow.org/tutorials/structured_data/time_series)

---

**创建日期**: 2026-01-24  
**最后更新**: 2026-01-24  
**维护者**: MineEnergySystem Team
