"""
独立的预测和深度学习模块
提供LSTM深度学习预测、数据生成、预测工具等功能，与后端主程序解耦
"""

__version__ = "1.0.0"

# 数据生成器（无依赖）
from lstm_forecast.data_generator import DataGenerator

# 预测工具（无依赖）
from lstm_forecast.forecast_utils import ForecastUtils

# 尝试导入LSTM服务（需要TensorFlow）
try:
    from lstm_forecast.service import LSTMForecastService
    from lstm_forecast.version_manager import ModelVersionService
    LSTM_AVAILABLE = True
except ImportError as e:
    LSTM_AVAILABLE = False
    LSTMForecastService = None
    ModelVersionService = None

__all__ = [
    "DataGenerator",
    "ForecastUtils",
    "LSTMForecastService",
    "ModelVersionService",
    "LSTM_AVAILABLE"
]
