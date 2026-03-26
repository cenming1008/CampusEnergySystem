"""
预测基础接口
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select

from app.api.deps import MAINTAINER_OR_ADMIN
from app.application.forecasting import (
    evaluate_prediction_accuracy_use_case,
    forecast_load_use_case,
    list_latest_predictions_use_case,
)
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response
from app.models.tables import Prediction, User

from .shared import (
    RENEWABLE_PREDICTION_TYPES,
    serialize_prediction,
    validate_prediction_type,
)

router = APIRouter()


@router.post("/load")
def forecast_load(
    device_id: Optional[int] = Query(None, description="设备ID，不提供则预测系统总负荷"),
    hours: int = Query(24, ge=1, le=168, description="预测时间范围（小时），1-168"),
    algorithm: Optional[str] = Query(None, description="预测算法：lstm, moving_average, linear_regression"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    try:
        payload = forecast_load_use_case(
            session=session,
            device_id=device_id,
            hours=hours,
            algorithm=algorithm,
        )
        audit_log("forecast.load", current_user.username, "prediction:load", device_id=device_id, hours=hours, algorithm=algorithm)
        return success_response(data=payload, message=f"成功生成 {payload['count']} 个预测点")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(f"负荷预测失败: device_id={device_id}, hours={hours}, algorithm={algorithm}, err={exc}")
        raise HTTPException(status_code=500, detail="负荷预测失败")


@router.post("/renewable/{prediction_type}")
def forecast_renewable(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID，不提供则预测系统总量"),
    hours: int = Query(24, ge=1, le=168, description="预测时间范围（小时）"),
    algorithm: Optional[str] = Query(None, description="预测算法"),
    session: Session = Depends(get_session),
    current_user: User = Depends(MAINTAINER_OR_ADMIN),
):
    prediction_type = validate_prediction_type(prediction_type, RENEWABLE_PREDICTION_TYPES)
    try:
        payload = forecast_load_use_case(
            session=session,
            device_id=device_id,
            hours=hours,
            algorithm=algorithm,
        )
        payload["prediction_type"] = prediction_type
        type_name = "光伏" if prediction_type == "solar" else "风电"
        audit_log("forecast.renewable", current_user.username, f"prediction:{prediction_type}", device_id=device_id, hours=hours, algorithm=algorithm)
        return success_response(data=payload, message=f"成功生成 {type_name} {payload['count']} 个预测点")
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"可再生能源预测失败: type={prediction_type}, device_id={device_id}, hours={hours}, algorithm={algorithm}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="预测失败")


@router.get("/latest/{prediction_type}")
def get_latest_predictions(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    limit: int = Query(24, ge=1, le=168, description="返回数量"),
    session: Session = Depends(get_session),
):
    prediction_type = validate_prediction_type(prediction_type)
    predictions = list_latest_predictions_use_case(
        session=session,
        prediction_type=prediction_type,
        device_id=device_id,
        limit=limit,
    )
    result = [serialize_prediction(p) for p in predictions]
    return success_response(data={"predictions": result, "count": len(result)})


@router.get("/accuracy/{prediction_type}")
def get_prediction_accuracy(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    days: int = Query(7, ge=1, le=30, description="评估天数"),
    session: Session = Depends(get_session),
):
    prediction_type = validate_prediction_type(prediction_type)
    try:
        accuracy = evaluate_prediction_accuracy_use_case(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            days=days,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception(
            f"预测准确性评估失败: type={prediction_type}, device_id={device_id}, days={days}, err={exc}"
        )
        raise HTTPException(status_code=500, detail="预测准确性评估失败")
    return success_response(data=accuracy, message="预测准确性评估")


@router.get("/history/{prediction_type}")
def get_prediction_history(
    prediction_type: str,
    device_id: Optional[int] = Query(None, description="设备ID"),
    start_time: Optional[datetime] = Query(None, description="开始时间"),
    end_time: Optional[datetime] = Query(None, description="结束时间"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量"),
    session: Session = Depends(get_session),
):
    prediction_type = validate_prediction_type(prediction_type)
    statement = select(Prediction).where(Prediction.prediction_type == prediction_type)
    if device_id is not None:
        statement = statement.where(Prediction.device_id == device_id)
    if start_time:
        statement = statement.where(Prediction.created_at >= start_time)
    if end_time:
        statement = statement.where(Prediction.created_at <= end_time)
    statement = statement.order_by(Prediction.created_at.desc()).limit(limit)
    predictions = list(session.exec(statement).all())
    return success_response(
        data={
            "predictions": [serialize_prediction(p, include_id=True, include_actual=True) for p in predictions],
            "count": len(predictions),
        }
    )
