"""
数据清理基础接口
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, text

from app.api.deps import get_current_user
from app.core.database import get_session
from app.core.logger import logger
from app.core.response import success_response

router = APIRouter()


@router.get("/test")
def test_cleanup_endpoint():
    return {"status": "ok", "message": "数据清理API端点正常工作"}


@router.post("/cleanup")
def cleanup_data(
    hours: int = Query(1, ge=1, le=24, description="清理多少小时之前的数据"),
    session: Session = Depends(get_session),
    current_user=Depends(get_current_user),
) -> Dict[str, Any]:
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = {
            "timestamp": datetime.now().isoformat(),
            "cutoff_time": cutoff_time.isoformat(),
            "hours": hours,
            "energy_data": 0,
            "alarm_data": 0,
            "carbon_emission": 0,
            "errors": [],
        }

        try:
            try:
                session.exec(
                    text(
                        f"""
                        SELECT drop_chunks(
                            'energydata',
                            INTERVAL '{hours} hours'
                        );
                    """
                    )
                )
                session.commit()
                logger.info(f"使用 TimescaleDB drop_chunks 清理 energydata（{hours}小时前）")
            except Exception:
                deleted_stmt = text(
                    """
                    WITH deleted AS (
                        DELETE FROM energydata
                        WHERE timestamp < :cutoff_time
                        RETURNING device_id
                    )
                    SELECT COUNT(*) FROM deleted
                """
                )
                deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
                session.commit()
                deleted_count = int(deleted_count) if deleted_count else 0
                if deleted_count > 0:
                    results["energy_data"] = deleted_count
                    logger.info(f"清理了 {deleted_count} 条 EnergyData 记录（{hours}小时前）")
        except Exception as exc:
            error_msg = f"清理 EnergyData 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        try:
            deleted_stmt = text(
                """
                WITH deleted AS (
                    DELETE FROM alarm
                    WHERE timestamp < :cutoff_time
                    AND is_resolved = true
                    RETURNING id
                )
                SELECT COUNT(*) FROM deleted
            """
            )
            deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
            session.commit()
            deleted_count = int(deleted_count) if deleted_count else 0
            if deleted_count > 0:
                results["alarm_data"] = deleted_count
                logger.info(f"清理了 {deleted_count} 条已解决的报警记录（{hours}小时前）")
        except Exception as exc:
            error_msg = f"清理 Alarm 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        try:
            try:
                session.exec(
                    text(
                        f"""
                        SELECT drop_chunks(
                            'carbon_emission',
                            INTERVAL '{hours} hours'
                        );
                    """
                    )
                )
                session.commit()
                logger.info(f"使用 TimescaleDB drop_chunks 清理 carbon_emission（{hours}小时前）")
            except Exception:
                deleted_stmt = text(
                    """
                    WITH deleted AS (
                        DELETE FROM carbon_emission
                        WHERE timestamp < :cutoff_time
                        RETURNING device_id
                    )
                    SELECT COUNT(*) FROM deleted
                """
                )
                deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
                session.commit()
                deleted_count = int(deleted_count) if deleted_count else 0
                if deleted_count > 0:
                    results["carbon_emission"] = deleted_count
                    logger.info(f"清理了 {deleted_count} 条 CarbonEmission 记录（{hours}小时前）")
        except Exception as exc:
            error_msg = f"清理 CarbonEmission 失败: {exc}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
            session.rollback()

        total_deleted = results["energy_data"] + results["alarm_data"] + results["carbon_emission"]
        results["total_deleted"] = total_deleted
        results["status"] = "success" if total_deleted > 0 or len(results["errors"]) == 0 else "partial"
        logger.info(f"✅ 数据清理完成：共清理 {total_deleted} 条记录（{hours}小时前）")
        return success_response(data=results, message=f"清理完成：共删除 {total_deleted} 条记录")
    except Exception as exc:
        logger.error(f"数据清理失败: {exc}")
        raise HTTPException(status_code=500, detail="数据清理失败")
