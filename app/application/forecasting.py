"""
预测用例
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from sqlmodel import Session, select

from app.models.tables import Prediction

try:
    from app.integrations.forecasting import ForecastAdapter
    FORECAST_AVAILABLE = True
except ImportError:
    ForecastAdapter = None
    FORECAST_AVAILABLE = False


def get_forecast_adapter() -> "ForecastAdapter":
    """创建预测适配器实例。"""
    if not FORECAST_AVAILABLE or ForecastAdapter is None:
        raise ImportError("预测模块不可用")
    return ForecastAdapter()


def forecast_load_use_case(
    session: Session,
    device_id: Optional[int] = None,
    hours: int = 24,
    algorithm: Optional[str] = None,
) -> Dict[str, Any]:
    """统一负荷预测入口。"""
    predictions = get_forecast_adapter().forecast_load(
        session=session,
        device_id=device_id,
        hours=hours,
        algorithm=algorithm,
    )
    return {
        "device_id": device_id,
        "predictions": predictions,
        "forecast_hours": hours,
        "algorithm": algorithm or "default",
        "count": len(predictions),
    }


def evaluate_prediction_accuracy_use_case(
    session: Session,
    prediction_type: str,
    device_id: Optional[int] = None,
    days: int = 7,
) -> Dict[str, Any]:
    """统一预测准确率评估入口。"""
    return get_forecast_adapter().evaluate_prediction_accuracy(
        session=session,
        prediction_type=prediction_type,
        device_id=device_id,
        days=days,
    )


def train_lstm_model_use_case(
    session: Session,
    prediction_type: str,
    device_id: Optional[int] = None,
    days: int = 60,
    params: Optional[Dict[str, Any]] = None,
    retrain: bool = False,
    use_multivariate: bool = False,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """统一 LSTM 训练入口。"""
    if not version:
        version = f"v{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    return get_forecast_adapter().train_lstm_model(
        session=session,
        prediction_type=prediction_type,
        device_id=device_id,
        days=days,
        params=params,
        retrain=retrain,
        use_multivariate=use_multivariate,
        version=version,
    )


def evaluate_lstm_model_use_case(
    session: Session,
    prediction_type: str,
    device_id: Optional[int] = None,
    test_days: int = 7,
) -> Dict[str, Any]:
    """统一 LSTM 评估入口。"""
    return get_forecast_adapter().evaluate_lstm_model(
        session=session,
        prediction_type=prediction_type,
        device_id=device_id,
        test_days=test_days,
    )


def list_latest_predictions_use_case(
    session: Session,
    prediction_type: str,
    device_id: Optional[int] = None,
    limit: int = 24,
) -> list[Prediction]:
    """统一最新预测查询入口。"""
    statement = select(Prediction).where(Prediction.prediction_type == prediction_type)
    if device_id is not None:
        statement = statement.where(Prediction.device_id == device_id)
    statement = statement.order_by(Prediction.created_at.desc()).limit(limit)
    return list(session.exec(statement).all())
