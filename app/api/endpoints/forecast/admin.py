"""
预测管理接口
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session

from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response

router = APIRouter()


@router.get("/scheduler/jobs")
def get_scheduler_jobs(session: Session = Depends(get_session)):
    try:
        from app.services.scheduler_service import get_jobs

        jobs = get_jobs()
        return success_response(
            data={"jobs": jobs, "count": len(jobs)},
            message="获取定时任务列表成功",
        )
    except Exception as exc:
        logger.exception(f"获取定时任务失败: {exc}")
        raise HTTPException(status_code=500, detail="获取定时任务失败")
