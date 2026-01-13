# LSTM模块独立化说明

## 📋 概述

LSTM预测功能已从后端主程序中分离，成为独立的模块 `lstm_forecast/`。这样可以：

- ✅ **解耦**：LSTM模块不依赖后端主程序
- ✅ **独立**：可以单独使用、测试、部署
- ✅ **灵活**：后端通过适配器使用，LSTM不可用时不影响其他功能

## 📁 新的目录结构

```
MineEnergySystem/
├── lstm_forecast/              # 独立的LSTM模块（新增）
│   ├── __init__.py
│   ├── service.py             # LSTM核心服务
│   ├── version_manager.py     # 模型版本管理
│   └── README.md
├── app/
│   ├── services/
│   │   ├── lstm_adapter.py    # LSTM适配器（新增）
│   │   ├── forecast_service.py # 已更新：使用适配器
│   │   └── scheduler_service.py # 已更新：使用适配器
│   └── api/endpoints/
│       └── forecast.py        # 已更新：使用适配器
```

## 🔄 变更说明

### 1. 新增独立模块

**`lstm_forecast/`** - 独立的LSTM预测模块
- `service.py`: LSTM核心服务，不依赖后端
- `version_manager.py`: 模型版本管理
- 数据通过参数传入，不直接访问数据库

### 2. 新增适配器

**`app/services/lstm_adapter.py`** - LSTM适配器
- 连接后端主程序和独立的LSTM模块
- 负责从数据库获取数据，调用LSTM模块
- 提供与原来兼容的接口

### 3. 更新的文件

- `app/services/forecast_service.py`: 使用 `LSTMAdapter` 替代 `LSTMForecastService`
- `app/api/endpoints/forecast.py`: 所有LSTM相关API使用适配器
- `app/services/scheduler_service.py`: 定时任务使用适配器
- `app/services/__init__.py`: 导出 `LSTMAdapter` 替代 `LSTMForecastService`

### 4. 已删除的旧文件

- `app/services/lstm_forecast_service.py`: **已删除** - 功能已迁移到 `lstm_forecast/service.py`
- `app/services/model_version_service.py`: **已删除** - 功能已迁移到 `lstm_forecast/version_manager.py`

这些文件已被删除，所有功能已迁移到独立的 `lstm_forecast/` 模块中。

## 🚀 使用方法

### 后端代码使用（推荐）

```python
from app.services.lstm_adapter import LSTMAdapter

# 初始化适配器
adapter = LSTMAdapter()

# 训练模型（自动从数据库获取数据）
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

### 直接使用独立模块

```python
from lstm_forecast import LSTMForecastService

# 初始化服务
service = LSTMForecastService(config={
    "sequence_length": 24,
    "lstm_units": [64, 32],
    "epochs": 50
})

# 准备数据（需要从外部提供）
data = [...]  # 数据列表

# 训练
result = service.train_model(
    data=data,
    prediction_type="load",
    device_id=1
)

# 预测
predictions = service.predict(
    recent_data=data[-24:],
    prediction_type="load",
    hours=24
)
```

## ✅ 优势

1. **解耦**：LSTM模块独立，不依赖后端框架
2. **可测试**：可以单独测试LSTM功能
3. **可复用**：LSTM模块可以在其他项目中使用
4. **向后兼容**：旧代码仍可使用（通过适配器）
5. **灵活部署**：LSTM模块可以单独部署或更新

## ⚠️ 注意事项

1. **导入路径**：新代码应使用 `from app.services.lstm_adapter import LSTMAdapter`
2. **旧文件已删除**：`lstm_forecast_service.py` 和 `model_version_service.py` 已删除，请使用适配器
3. **配置**：LSTM模块通过适配器自动从后端配置读取参数
4. **数据访问**：适配器负责从数据库获取数据，LSTM模块只处理数据

## 📝 迁移指南

### 从旧代码迁移

**旧代码（已删除，不再可用）：**
```python
from app.services.lstm_forecast_service import LSTMForecastService  # ❌ 文件已删除

lstm_service = LSTMForecastService()
result = lstm_service.train_model(session, ...)
```

**新代码（使用适配器）：**
```python
from app.services.lstm_adapter import LSTMAdapter  # ✅ 推荐方式

lstm_adapter = LSTMAdapter()
result = lstm_adapter.train_model(session, ...)
```

接口基本一致，只需替换类名即可。

## 🔍 验证

验证独立化是否成功：

```bash
# 1. 检查独立模块
python -c "from lstm_forecast import LSTMForecastService; print('✓ 独立模块可用')"

# 2. 检查适配器
python -c "from app.services.lstm_adapter import LSTMAdapter; print('✓ 适配器可用')"

# 3. 检查后端集成
python -c "from app.services import LSTMAdapter; print('✓ 后端集成正常')"
```

## 📚 相关文档

- [LSTM完整使用指南.md](./LSTM完整使用指南.md) - LSTM功能使用指南
- [lstm_forecast/README.md](../lstm_forecast/README.md) - 独立模块文档

---

**最后更新**: 2024-01-08
