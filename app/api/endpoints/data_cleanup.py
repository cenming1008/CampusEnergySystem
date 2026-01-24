"""
数据清理API端点
提供手动清理数据的功能
"""
from datetime import datetime, timedelta
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, text

from app.core.database import get_session
from app.core.response import success_response
from app.core.logger import logger
from app.api.deps import get_current_user

router = APIRouter()


@router.get("/test")
def test_cleanup_endpoint():
    """测试端点，用于验证路由是否正常工作"""
    return {"status": "ok", "message": "数据清理API端点正常工作"}


@router.post("/cleanup")
def cleanup_data(
    hours: int = Query(1, ge=1, le=24, description="清理多少小时之前的数据"),
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    清理指定小时数之前的数据
    
    Args:
        hours: 清理多少小时之前的数据（1-24小时）
        
    Returns:
        清理结果统计
    """
    try:
        cutoff_time = datetime.now() - timedelta(hours=hours)
        results = {
            "timestamp": datetime.now().isoformat(),
            "cutoff_time": cutoff_time.isoformat(),
            "hours": hours,
            "energy_data": 0,
            "alarm_data": 0,
            "carbon_emission": 0,
            "errors": []
        }
        
        # 1. 清理时序数据（EnergyData）
        try:
            # 尝试使用 TimescaleDB 的 drop_chunks（如果可用）
            try:
                session.exec(
                    text(f"""
                        SELECT drop_chunks(
                            'energydata',
                            INTERVAL '{hours} hours'
                        );
                    """)
                )
                session.commit()
                logger.info(f"使用 TimescaleDB drop_chunks 清理 energydata（{hours}小时前）")
            except Exception:
                # 回退到普通 DELETE（单次执行并返回删除计数）
                deleted_stmt = text("""
                    WITH deleted AS (
                        DELETE FROM energydata 
                        WHERE timestamp < :cutoff_time
                        RETURNING device_id
                    )
                    SELECT COUNT(*) FROM deleted
                """)
                deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
                session.commit()
                
                deleted_count = int(deleted_count) if deleted_count else 0
                
                if deleted_count > 0:
                    results["energy_data"] = deleted_count
                    logger.info(f"清理了 {deleted_count} 条 EnergyData 记录（{hours}小时前）")
        except Exception as e:
            error_msg = f"清理 EnergyData 失败: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        # 2. 清理已解决的报警记录
        try:
            deleted_stmt = text("""
                WITH deleted AS (
                    DELETE FROM alarm 
                    WHERE timestamp < :cutoff_time 
                    AND is_resolved = true
                    RETURNING id
                )
                SELECT COUNT(*) FROM deleted
            """)
            deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
            session.commit()
            
            deleted_count = int(deleted_count) if deleted_count else 0
            
            if deleted_count > 0:
                results["alarm_data"] = deleted_count
                logger.info(f"清理了 {deleted_count} 条已解决的报警记录（{hours}小时前）")
        except Exception as e:
            error_msg = f"清理 Alarm 失败: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        # 3. 清理碳排放记录
        try:
            try:
                session.exec(
                    text(f"""
                        SELECT drop_chunks(
                            'carbon_emission',
                            INTERVAL '{hours} hours'
                        );
                    """)
                )
                session.commit()
                logger.info(f"使用 TimescaleDB drop_chunks 清理 carbon_emission（{hours}小时前）")
            except Exception:
                deleted_stmt = text("""
                    WITH deleted AS (
                        DELETE FROM carbon_emission 
                        WHERE timestamp < :cutoff_time
                        RETURNING device_id
                    )
                    SELECT COUNT(*) FROM deleted
                """)
                deleted_count = session.exec(deleted_stmt, {"cutoff_time": cutoff_time}).scalar_one_or_none()
                session.commit()
                
                deleted_count = int(deleted_count) if deleted_count else 0
                
                if deleted_count > 0:
                    results["carbon_emission"] = deleted_count
                    logger.info(f"清理了 {deleted_count} 条 CarbonEmission 记录（{hours}小时前）")
        except Exception as e:
            error_msg = f"清理 CarbonEmission 失败: {e}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        total_deleted = (
            results["energy_data"] + 
            results["alarm_data"] + 
            results["carbon_emission"]
        )
        
        results["total_deleted"] = total_deleted
        results["status"] = "success" if total_deleted > 0 or len(results["errors"]) == 0 else "partial"
        
        logger.info(f"✅ 数据清理完成：共清理 {total_deleted} 条记录（{hours}小时前）")
        
        return success_response(
            data=results,
            message=f"清理完成：共删除 {total_deleted} 条记录"
        )
        
    except Exception as e:
        logger.error(f"数据清理失败: {e}")
        raise HTTPException(status_code=500, detail=f"数据清理失败: {str(e)}")


@router.post("/cleanup-all")
def cleanup_all_data(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    清除所有数据（危险操作）
    
    清除所有时序数据、已解决的报警记录和碳排放记录
    
    Returns:
        清理结果统计
    """
    try:
        results = {
            "timestamp": datetime.now().isoformat(),
            "energy_data": 0,
            "alarm_data": 0,
            "carbon_emission": 0,
            "errors": []
        }
        
        # 1. 清除所有时序数据（EnergyData）
        try:
            # 先统计数量（使用标量查询）
            count_result = session.exec(
                text("SELECT COUNT(*) FROM energydata")
            ).scalar_one_or_none()
            total_count = int(count_result) if count_result else 0
            
            # 清除所有数据
            session.exec(text("TRUNCATE TABLE energydata CASCADE"))
            session.commit()
            
            results["energy_data"] = total_count
            logger.warning(f"⚠️ 清除了所有 EnergyData 记录：{total_count} 条")
        except Exception as e:
            error_msg = f"清理所有 EnergyData 失败: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        # 2. 清除所有已解决的报警记录
        try:
            deleted_stmt = text("""
                WITH deleted AS (
                    DELETE FROM alarm 
                    WHERE is_resolved = true
                    RETURNING id
                )
                SELECT COUNT(*) FROM deleted
            """)
            deleted_count = session.exec(deleted_stmt).scalar_one_or_none()
            session.commit()
            
            deleted_count = int(deleted_count) if deleted_count else 0
            
            if deleted_count > 0:
                results["alarm_data"] = deleted_count
                logger.warning(f"⚠️ 清除了所有已解决的报警记录：{deleted_count} 条")
        except Exception as e:
            error_msg = f"清理所有 Alarm 失败: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        # 3. 清除所有碳排放记录
        try:
            count_result = session.exec(
                text("SELECT COUNT(*) FROM carbon_emission")
            ).scalar_one_or_none()
            total_count = int(count_result) if count_result else 0
            
            session.exec(text("TRUNCATE TABLE carbon_emission CASCADE"))
            session.commit()
            
            results["carbon_emission"] = total_count
            logger.warning(f"⚠️ 清除了所有 CarbonEmission 记录：{total_count} 条")
        except Exception as e:
            error_msg = f"清理所有 CarbonEmission 失败: {e}"
            logger.warning(error_msg)
            results["errors"].append(error_msg)
            session.rollback()
        
        total_deleted = (
            results["energy_data"] + 
            results["alarm_data"] + 
            results["carbon_emission"]
        )
        
        results["total_deleted"] = total_deleted
        results["status"] = "success" if len(results["errors"]) == 0 else "partial"
        
        logger.warning(f"⚠️ 清除所有数据完成：共清除 {total_deleted} 条记录")
        
        return success_response(
            data=results,
            message=f"清除完成：共删除 {total_deleted} 条记录"
        )
        
    except Exception as e:
        logger.error(f"清除所有数据失败: {e}")
        raise HTTPException(status_code=500, detail=f"清除所有数据失败: {str(e)}")


@router.get("/stats")
def get_cleanup_stats(
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    获取数据统计信息（用于显示清理前的数据量）
    """
    from app.services.data_cleanup_service import get_data_statistics
    
    try:
        stats = get_data_statistics()
        return success_response(data=stats)
    except Exception as e:
        logger.error(f"获取数据统计失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取统计失败: {str(e)}")
