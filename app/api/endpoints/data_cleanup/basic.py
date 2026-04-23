"""
数据清理基础接口
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session

from app.api.deps import ADMIN_ONLY
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response
from app.services.data_cleanup_service import cleanup_runtime_data_before

router = APIRouter()


@router.get("/test")
def test_cleanup_endpoint():
    return {"status": "ok", "message": "数据清理API端点正常工作"}


@router.post("/cleanup")
def cleanup_data(
    hours: int = Query(1, ge=1, le=24, description="清理多少小时之前的数据"),
    session: Session = Depends(get_session),
    current_user=Depends(ADMIN_ONLY),
) -> Dict[str, Any]:
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = cleanup_runtime_data_before(session, cutoff_time, hours=hours)
        audit_log(
            "data_cleanup.cleanup",
            current_user.username,
            "retention:data",
            hours=hours,
            total_deleted=results["total_deleted"],
            status=results["status"],
        )
        logger.info(f"✅ 数据清理完成：共清理 {results['total_deleted']} 条记录（{hours}小时前）")
        return success_response(data=results, message=f"清理完成：共删除 {results['total_deleted']} 条记录")
    except Exception as exc:
        logger.error(f"数据清理失败: {exc}")
        raise HTTPException(status_code=500, detail="数据清理失败")
