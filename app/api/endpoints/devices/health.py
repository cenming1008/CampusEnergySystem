"""
设备接入健康接口
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from app.api.endpoint_utils import bad_request_from_value_error
from app.core.database import get_session
from app.core.response import success_response
from app.services.ingestion_health_service import IngestionHealthService

router = APIRouter()


@router.get("/{device_id}/ingestion-health")
def get_device_ingestion_health(
    device_id: int,
    session: Session = Depends(get_session),
):
    try:
        health = IngestionHealthService.get_device_health(session, device_id)
        return success_response(data=health)
    except ValueError as exc:
        raise bad_request_from_value_error(exc) from exc


@router.get("/ingestion-health/overview")
def list_device_ingestion_health(
    session: Session = Depends(get_session),
):
    return success_response(data={"items": IngestionHealthService.list_device_health(session)})
