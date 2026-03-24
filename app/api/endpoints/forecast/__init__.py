"""
预测API聚合入口
"""

from fastapi import APIRouter

from .admin import get_scheduler_jobs, router as admin_router
from .basic import (
    forecast_load,
    forecast_renewable,
    get_latest_predictions,
    get_prediction_accuracy,
    get_prediction_history,
    router as basic_router,
)
from .lstm import (
    activate_model_version,
    compare_model_versions,
    evaluate_lstm_model,
    hyperparameter_search,
    list_model_versions,
    train_lstm_model,
    router as lstm_router,
)
from .shared import (
    FORECAST_AVAILABLE,
    LSTM_AVAILABLE,
    get_forecast_adapter_or_503,
    validate_prediction_type,
)
from app.application.forecasting import evaluate_prediction_accuracy_use_case

router = APIRouter()
router.include_router(basic_router)
router.include_router(lstm_router)
router.include_router(admin_router)


def _validate_prediction_type(prediction_type: str, allowed_types=None):
    return validate_prediction_type(prediction_type, allowed_types or {"load", "solar", "wind"})


def _get_forecast_adapter():
    return get_forecast_adapter_or_503()
