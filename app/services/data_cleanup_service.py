"""
数据清理服务
自动清理过期的时序数据和历史记录
"""
from datetime import datetime, timedelta
from typing import Dict, Any

from sqlmodel import Session, text, select
from app.core.database import engine
from app.core.logger import logger
from app.core.settings import settings
from app.models.tables import EnergyData, Alarm, CarbonEmission


def cleanup_old_data() -> Dict[str, Any]:
    """
    清理过期数据（定时任务）
    
    返回清理统计信息
    """
    if not settings.enable_auto_cleanup:
        logger.info("自动数据清理已禁用，跳过清理")
        return {"status": "disabled"}
    
    results = {
        "timestamp": datetime.now().isoformat(),
        "energy_data": 0,
        "alarm_data": 0,
        "carbon_emission": 0,
        "statistics": 0,
        "errors": []
    }
    
    try:
        with Session(engine) as session:
            # 1. 清理时序数据（EnergyData）
            if settings.data_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.data_retention_days)
                try:
                    # 使用 TimescaleDB 的 drop_chunks 函数（如果可用）
                    # 否则使用 DELETE
                    try:
                        # 尝试使用 TimescaleDB 的 drop_chunks（更高效）
                        result = session.exec(
                            text(f"""
                                SELECT drop_chunks(
                                    'energydata',
                                    INTERVAL '{settings.data_retention_days} days'
                                );
                            """)
                        )
                        logger.info(f"使用 TimescaleDB drop_chunks 清理 energydata")
                    except Exception:
                        # 回退到普通 DELETE
                        stmt = select(EnergyData).where(
                            EnergyData.timestamp < cutoff_date
                        )
                        old_data = session.exec(stmt).all()
                        count = len(old_data)
                        
                        if count > 0:
                            session.exec(
                                text(f"""
                                    DELETE FROM energydata 
                                    WHERE timestamp < :cutoff_date
                                """),
                                {"cutoff_date": cutoff_date}
                            )
                            session.commit()
                            results["energy_data"] = count
                            logger.info(f"清理了 {count} 条 EnergyData 记录（超过 {settings.data_retention_days} 天）")
                except Exception as e:
                    error_msg = f"清理 EnergyData 失败: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # 2. 清理报警记录
            if settings.alarm_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.alarm_retention_days)
                try:
                    # 只清理已解决的报警，使用 RETURNING 获取删除的行数
                    stmt = text("""
                        WITH deleted AS (
                            DELETE FROM alarm 
                            WHERE timestamp < :cutoff_date 
                            AND is_resolved = true
                            RETURNING id
                        )
                        SELECT COUNT(*) FROM deleted
                    """)
                    result = session.exec(stmt, {"cutoff_date": cutoff_date})
                    deleted_count = result.first()
                    
                    if deleted_count and deleted_count > 0:
                        session.commit()
                        results["alarm_data"] = deleted_count
                        logger.info(f"清理了 {deleted_count} 条已解决的报警记录（超过 {settings.alarm_retention_days} 天）")
                    else:
                        session.rollback()
                except Exception as e:
                    session.rollback()
                    error_msg = f"清理 Alarm 失败: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # 3. 清理碳排放记录
            if settings.data_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.data_retention_days)
                try:
                    try:
                        # 尝试使用 TimescaleDB 的 drop_chunks
                        session.exec(
                            text(f"""
                                SELECT drop_chunks(
                                    'carbon_emission',
                                    INTERVAL '{settings.data_retention_days} days'
                                );
                            """)
                        )
                        logger.info(f"使用 TimescaleDB drop_chunks 清理 carbon_emission")
                    except Exception:
                        # 回退到普通 DELETE
                        stmt = text("""
                            DELETE FROM carbon_emission 
                            WHERE timestamp < :cutoff_date
                        """)
                        session.exec(stmt, {"cutoff_date": cutoff_date})
                        session.commit()
                        logger.info(f"清理了 CarbonEmission 记录（超过 {settings.data_retention_days} 天）")
                except Exception as e:
                    error_msg = f"清理 CarbonEmission 失败: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # 4. 清理统计数据（保留时间更长）
            if settings.statistics_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.statistics_retention_days)
                try:
                    stmt = text("""
                        DELETE FROM energy_statistics 
                        WHERE stat_time < :cutoff_date
                    """)
                    session.exec(stmt, {"cutoff_date": cutoff_date})
                    session.commit()
                    logger.info(f"清理了 EnergyStatistics 记录（超过 {settings.statistics_retention_days} 天）")
                except Exception as e:
                    error_msg = f"清理 EnergyStatistics 失败: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # 5. 执行 VACUUM 优化（可选，在非高峰时段）
            try:
                session.exec(text("VACUUM ANALYZE"))
                logger.debug("执行了 VACUUM ANALYZE 优化")
            except Exception as e:
                logger.warning(f"VACUUM 失败: {e}")
        
        total_deleted = (
            results["energy_data"] + 
            results["alarm_data"] + 
            results["carbon_emission"] + 
            results["statistics"]
        )
        
        if total_deleted > 0:
            logger.info(f"✅ 数据清理完成：共清理 {total_deleted} 条记录")
        else:
            logger.debug("数据清理完成：没有需要清理的数据")
        
        results["status"] = "success"
        results["total_deleted"] = total_deleted
        
    except Exception as e:
        error_msg = f"数据清理过程中发生错误: {e}"
        logger.error(error_msg)
        results["status"] = "error"
        results["errors"].append(error_msg)
    
    return results


def get_data_statistics() -> Dict[str, Any]:
    """
    获取数据统计信息（用于监控）
    """
    stats = {
        "timestamp": datetime.now().isoformat(),
        "energy_data": {},
        "alarm_data": {},
        "carbon_emission": {},
        "statistics": {}
    }
    
    try:
        with Session(engine) as session:
            # EnergyData 统计
            result = session.exec(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        MIN(timestamp) as oldest,
                        MAX(timestamp) as newest
                    FROM energydata
                """)
            ).first()
            if result:
                stats["energy_data"] = {
                    "total": result[0] if isinstance(result, tuple) else result.total,
                    "oldest": str(result[1]) if isinstance(result, tuple) else str(result.oldest),
                    "newest": str(result[2]) if isinstance(result, tuple) else str(result.newest)
                }
            
            # Alarm 统计
            result = session.exec(
                text("""
                    SELECT 
                        COUNT(*) as total,
                        COUNT(*) FILTER (WHERE is_resolved = false) as unresolved,
                        MIN(timestamp) as oldest,
                        MAX(timestamp) as newest
                    FROM alarm
                """)
            ).first()
            if result:
                stats["alarm_data"] = {
                    "total": result[0] if isinstance(result, tuple) else result.total,
                    "unresolved": result[1] if isinstance(result, tuple) else result.unresolved,
                    "oldest": str(result[2]) if isinstance(result, tuple) else str(result.oldest),
                    "newest": str(result[3]) if isinstance(result, tuple) else str(result.newest)
                }
    
    except Exception as e:
        logger.error(f"获取数据统计失败: {e}")
        stats["error"] = str(e)
    
    return stats
