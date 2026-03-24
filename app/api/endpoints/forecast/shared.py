"""
预测接口共享工具
"""

from __future__ import annotations

from typing import Iterable

from fastapi import HTTPException

from app.application.forecasting import get_forecast_adapter
from app.core.logger import logger
from app.models.tables import Prediction

try:
    from app.integrations.forecasting import ForecastAdapter
    FORECAST_AVAILABLE = True
    from lstm_forecast import LSTM_AVAILABLE
except ImportError:
    ForecastAdapter = None
    FORECAST_AVAILABLE = False
    LSTM_AVAILABLE = False


VALID_PREDICTION_TYPES = {"load", "solar", "wind"}
RENEWABLE_PREDICTION_TYPES = {"solar", "wind"}


def ensure_forecast_available() -> None:
    if not FORECAST_AVAILABLE:
        raise HTTPException(status_code=503, detail="预测模块不可用")


def ensure_lstm_available() -> None:
    ensure_forecast_available()
    if not LSTM_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="LSTM功能不可用，请安装TensorFlow: pip install tensorflow scikit-learn"
        )


def validate_prediction_type(
    prediction_type: str,
    allowed_types: Iterable[str] = VALID_PREDICTION_TYPES,
) -> str:
    normalized_type = prediction_type.lower()
    allowed_types = tuple(allowed_types)
    if normalized_type not in allowed_types:
        allowed_values = "', '".join(allowed_types)
        raise HTTPException(
            status_code=400,
            detail=f"prediction_type 必须是 '{allowed_values}'"
        )
    return normalized_type


def get_forecast_adapter_or_503() -> "ForecastAdapter":
    ensure_forecast_available()
    try:
        return get_forecast_adapter()
    except ImportError as exc:
        logger.warning(f"预测适配器初始化失败: {exc}")
        raise HTTPException(status_code=503, detail="预测模块不可用") from exc


def serialize_prediction(
    prediction: Prediction,
    include_id: bool = False,
    include_actual: bool = False,
) -> dict:
    payload = {
        "forecast_time": prediction.forecast_time,
        "predicted_value": prediction.predicted_value,
        "confidence": prediction.confidence,
        "algorithm": prediction.algorithm,
        "created_at": prediction.created_at,
    }
    if include_id:
        payload["id"] = prediction.id
        payload["device_id"] = prediction.device_id
    if include_actual:
        payload["actual_value"] = prediction.actual_value
    return payload
