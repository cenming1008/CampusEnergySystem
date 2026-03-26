"""
数据清理管理接口
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, text

from app.api.deps import ADMIN_ONLY
from app.core.audit import audit_log
from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response

router = APIRouter()


@router.post("/cleanup-all")
def cleanup_all_data(
    session: Session = Depends(get_session),
    current_user=Depends(ADMIN_ONLY),
) -> Dict[str, Any]:
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "energy_data": 0,
            "alarm_data": 0,
            "carbon_emission": 0,
            "errors": [],
        }

        try:
            count_result = session.exec(text("SELECT COUNT(*) FROM energydata")).scalar_one_or_none()
            total_count = int(count_result) if count_result else 0
            session.exec(text("TRUNCATE TABLE energydata CASCADE"))
            session.commit()
            results["energy_data"] = total_count
            logger.warning(f"⚠️ 清除了所有 EnergyData 记录：{total_count} 条")
        except Exception as exc:
            error_msg = f"清理所有 EnergyData 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        try:
            deleted_stmt = text(
                """
                WITH deleted AS (
                    DELETE FROM alarm
                    WHERE is_resolved = true
                    RETURNING id
                )
                SELECT COUNT(*) FROM deleted
            """
            )
            deleted_count = session.exec(deleted_stmt).scalar_one_or_none()
            session.commit()
            deleted_count = int(deleted_count) if deleted_count else 0
            if deleted_count > 0:
                results["alarm_data"] = deleted_count
                logger.warning(f"⚠️ 清除了所有已解决的报警记录：{deleted_count} 条")
        except Exception as exc:
            error_msg = f"清理所有 Alarm 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        try:
            count_result = session.exec(text("SELECT COUNT(*) FROM carbon_emission")).scalar_one_or_none()
            total_count = int(count_result) if count_result else 0
            session.exec(text("TRUNCATE TABLE carbon_emission CASCADE"))
            session.commit()
            results["carbon_emission"] = total_count
            logger.warning(f"⚠️ 清除了所有 CarbonEmission 记录：{total_count} 条")
        except Exception as exc:
            error_msg = f"清理所有 CarbonEmission 失败: {exc}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        total_deleted = results["energy_data"] + results["alarm_data"] + results["carbon_emission"]
        results["total_deleted"] = total_deleted
        results["status"] = "success" if len(results["errors"]) == 0 else "partial"
        audit_log(
            "data_cleanup.cleanup_all",
            current_user.username,
            "all:data",
            total_deleted=total_deleted,
            status=results["status"],
        )
        logger.warning(f"⚠️ 清除所有数据完成：共清除 {total_deleted} 条记录")
        return success_response(data=results, message=f"清除完成：共删除 {total_deleted} 条记录")
    except Exception as exc:
        logger.error(f"清除所有数据失败: {exc}")
        raise HTTPException(status_code=500, detail="清除所有数据失败")


@router.get("/stats")
def get_cleanup_stats(
    session: Session = Depends(get_session),
    current_user=Depends(ADMIN_ONLY),
) -> Dict[str, Any]:
    from app.services.data_cleanup_service import get_data_statistics

    try:
        stats = get_data_statistics()
        return success_response(data=stats)
    except Exception as exc:
        logger.error(f"获取数据统计失败: {exc}")
        raise HTTPException(status_code=500, detail="获取统计失败")
