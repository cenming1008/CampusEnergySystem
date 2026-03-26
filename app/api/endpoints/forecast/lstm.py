"""
预测 LSTM 与版本管理接口
"""

from __future__ import annotations

from itertools import product
from typing import Any, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY, MAINTAINER_OR_ADMIN
from app.application.forecasting import (
    evaluate_lstm_model_use_case,
    train_lstm_model_use_case,
)
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.logger import logger
from app.core.rate_limit import limit_requests
from app.core.response import success_response
from app.core.settings import settings
from app.models.tables import User

from .shared import (
    ensure_lstm_available,
    get_forecast_adapter_or_503,
    validate_prediction_type,
)

router = APIRouter()


@router.post("/lstm/train")
def train_lstm_model(
    prediction_type: str = Body(..., description="预测类型：load/solar/wind"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    days: int = Body(60, ge=30, le=365, description="训练数据天数"),
    params: Optional[Dict[str, Any]] = Body(None, description="LSTM超参数"),
    retrain: bool = Body(False, description="是否强制重新训练"),
    use_multivariate: bool = Body(False, description="是否使用多变量预测（电压、电流、功率）"),
    version: Optional[str] = Body(None, description="版本号（如v1.0.0），不提供则自动生成"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
    _: None = Depends(
        limit_requests(
            bucket="forecast-training",
            max_calls=settings.forecast_training_rate_limit_count,
            window_seconds=settings.forecast_training_rate_limit_window_seconds,
        )
    ),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        result = train_lstm_model_use_case(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            days=days,
            params=params,
            retrain=retrain,
            use_multivariate=use_multivariate,
            version=version,
        )
        audit_log("forecast.lstm.train", current_user.username, f"prediction:{prediction_type}", device_id=device_id, version=result.get("version"))
        return success_response(data=result, message="LSTM模型训练完成")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"LSTM模型训练失败: type={prediction_type}, device_id={device_id}, days={days}, version={version}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="LSTM模型训练失败")


@router.get("/lstm/evaluate/{prediction_type}")
def evaluate_lstm_model(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    test_days: int = Query(7, ge=1, le=30, description="测试数据天数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        evaluation = evaluate_lstm_model_use_case(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            test_days=test_days,
        )
        audit_log("forecast.lstm.evaluate", current_user.username, f"prediction:{prediction_type}", device_id=device_id)
        return success_response(data=evaluation, message="LSTM模型评估完成")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"LSTM模型评估失败: type={prediction_type}, device_id={device_id}, test_days={test_days}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="LSTM模型评估失败")


@router.get("/lstm/versions/{prediction_type}")
def list_model_versions(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        adapter = get_forecast_adapter_or_503()
        versions = adapter.list_versions(prediction_type, device_id)
        audit_log("forecast.lstm.list_versions", current_user.username, f"prediction:{prediction_type}", device_id=device_id)
        return success_response(data={"versions": versions, "count": len(versions)})
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"获取模型版本列表失败: type={prediction_type}, device_id={device_id}, err={exc}")
        raise HTTPException(status_code=500, detail="获取版本列表失败")


@router.post("/lstm/versions/{prediction_type}/activate")
def activate_model_version(
    prediction_type: str,
    version: str = Body(..., description="版本号"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        adapter = get_forecast_adapter_or_503()
        success = adapter.set_active_version(prediction_type, device_id, version)
        if not success:
            raise HTTPException(status_code=404, detail="版本不存在")
        audit_log("forecast.lstm.activate_version", current_user.username, f"prediction:{prediction_type}", device_id=device_id, version=version)
        return success_response(data={"version": version, "is_active": True}, message=f"已激活版本 {version}")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"激活模型版本失败: type={prediction_type}, device_id={device_id}, version={version}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="激活版本失败")


@router.get("/lstm/versions/{prediction_type}/compare")
def compare_model_versions(
    prediction_type: str,
    version1: str = Query(..., description="版本1"),
    version2: str = Query(..., description="版本2"),
    device_id: Optional[int] = Query(None, description="设备ID"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        adapter = get_forecast_adapter_or_503()
        comparison = adapter.compare_versions(prediction_type, device_id, version1, version2)
        audit_log("forecast.lstm.compare_versions", current_user.username, f"prediction:{prediction_type}", device_id=device_id)
        return success_response(data=comparison, message="版本对比完成")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"模型版本对比失败: type={prediction_type}, device_id={device_id}, version1={version1}, version2={version2}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="版本对比失败")


@router.post("/lstm/hyperparameter-search")
def hyperparameter_search(
    prediction_type: str = Body(..., description="预测类型"),
    device_id: Optional[int] = Body(None, description="设备ID"),
    days: int = Body(60, description="训练数据天数"),
    session: Session = Depends(get_session),
    current_user: User = Depends(ADMIN_ONLY),
    _: None = Depends(
        limit_requests(
            bucket="forecast-training",
            max_calls=settings.forecast_training_rate_limit_count,
            window_seconds=settings.forecast_training_rate_limit_window_seconds,
        )
    ),
):
    ensure_lstm_available()
    prediction_type = validate_prediction_type(prediction_type)
    try:
        adapter = get_forecast_adapter_or_503()
        best_params = None
        best_score = float("inf")
        results = []
        sequence_lengths = [24, 48]
        lstm_units_list = [[64, 32], [128, 64]]
        dropout_rates = [0.2, 0.3]
        epochs_list = [30, 50]
        total_combinations = len(sequence_lengths) * len(lstm_units_list) * len(dropout_rates) * len(epochs_list)
        logger.info(f"开始超参数搜索，共 {total_combinations} 种组合")
        for seq_len, units, dropout, epochs in product(
            sequence_lengths, lstm_units_list, dropout_rates, epochs_list
        ):
            params = {
                "sequence_length": seq_len,
                "lstm_units": units,
                "dropout_rate": dropout,
                "epochs": epochs,
                "batch_size": 32,
                "validation_split": 0.2,
                "patience": 10,
            }
            try:
                result = adapter.train_lstm_model(
                    session=session,
                    prediction_type=prediction_type,
                    device_id=device_id,
                    days=days,
                    params=params,
                    retrain=True,
                    version=f"search_{seq_len}_{units[0]}_{dropout}_{epochs}",
                )
                if result.get("status") == "success":
                    val_loss = result.get("val_loss", float("inf"))
                    results.append(
                        {
                            "params": params,
                            "val_loss": val_loss,
                            "train_loss": result.get("train_loss"),
                            "epochs_trained": result.get("epochs_trained"),
                        }
                    )
                    if val_loss < best_score:
                        best_score = val_loss
                        best_params = params
            except Exception as exc:
                logger.warning(f"超参数组合训练失败: {params}, 错误: {exc}")
                continue
        results.sort(key=lambda x: x.get("val_loss", float("inf")))
        audit_log("forecast.lstm.hyperparameter_search", current_user.username, f"prediction:{prediction_type}", device_id=device_id, total_tested=len(results))
        return success_response(
            data={
                "best_params": best_params,
                "best_score": best_score,
                "all_results": results[:10],
                "total_tested": len(results),
            },
            message="超参数搜索完成",
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"超参数搜索失败: type={prediction_type}, device_id={device_id}, days={days}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="超参数搜索失败")
