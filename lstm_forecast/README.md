# 预测和深度学习模块

这是一个独立的预测和深度学习模块，包含LSTM预测、数据生成、预测工具等功能，与后端主程序完全解耦。

## 目录结构

```
lstm_forecast/
├── __init__.py          # 模块初始化
├── service.py           # LSTM核心服务
├── version_manager.py   # 模型版本管理
├── data_generator.py    # 数据生成器
├── forecast_utils.py    # 预测工具函数
└── README.md            # 本文档
```

## 功能特性

- ✅ 独立的LSTM预测服务，不依赖后端主程序
- ✅ 模型训练和预测
- ✅ 多变量预测支持
- ✅ 模型版本管理
- ✅ 模型评估

## 使用方法

### 直接使用（独立模块）

```python
from lstm_forecast import LSTMForecastService

# 初始化服务
config = {
    "sequence_length": 24,
    "lstm_units": [64, 32],
    "dropout_rate": 0.2,
    "epochs": 50
}
service = LSTMForecastService(config=config)

# 准备数据（需要提供数据列表）
data = [...]  # 数据列表，每个元素应有voltage, current, power属性

# 训练模型
X, y, scaler = service.prepare_data(data, use_multivariate=False)
result = service.train_model(
    data=data,
    prediction_type="load",
    device_id=1,
    days=60
)

# 预测
predictions = service.predict(
    recent_data=data[-24:],  # 最近24个数据点
    prediction_type="load",
    device_id=1,
    hours=24
)
```

### 通过适配器使用（后端集成）

后端代码通过 `app/services/lstm_adapter.py` 使用此模块：

```python
from app.services.lstm_adapter import LSTMAdapter

adapter = LSTMAdapter()

# 训练（自动从数据库获取数据）
result = adapter.train_model(
    session=session,
    prediction_type="load",
    device_id=1,
    days=60
)

# 预测（自动从数据库获取数据）
predictions = adapter.predict(
    session=session,
    prediction_type="load",
    device_id=1,
    hours=24
)
```

## 依赖

- TensorFlow >= 2.13.0
- scikit-learn >= 1.3.0
- NumPy >= 1.24.0

## 模型存储

- 模型文件: `models/lstm/{prediction_type}_{device_id}.h5`
- 标准化器: `models/scalers/{prediction_type}_{device_id}.pkl`
- 版本元数据: `models/versions_metadata.json`

## 注意事项

1. 此模块是独立的，不依赖 `app` 包
2. 数据需要从外部提供（数据库查询结果）
3. 配置通过字典传入，不依赖后端配置系统
4. 日志记录器可选传入
