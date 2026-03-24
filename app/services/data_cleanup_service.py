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
                    count = _count_rows_before_delete(
                        session=session,
                        count_statement=select(EnergyData).where(EnergyData.timestamp < cutoff_date),
                    )

                    if count > 0:
                        try:
                            session.exec(
                                text(f"""
                                    SELECT drop_chunks(
                                        'energydata',
                                        INTERVAL '{settings.data_retention_days} days'
                                    );
                                """)
                            )
                        except Exception:
                            session.exec(
                                text("""
                                    DELETE FROM energydata
                                    WHERE timestamp < :cutoff_date
                                """),
                                {"cutoff_date": cutoff_date},
                            )

                        session.commit()
                        results["energy_data"] = count
                        logger.info(f"清理了 {count} 条 EnergyData 记录（超过 {settings.data_retention_days} 天）")
                except Exception as e:
                    session.rollback()
                    error_msg = f"清理 EnergyData 失败: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # 2. 清理报警记录
            if settings.alarm_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.alarm_retention_days)
                try:
                    deleted_count = _count_unresolved_alarms_to_delete(session, cutoff_date)

                    if deleted_count > 0:
                        session.exec(
                            text("""
                                DELETE FROM alarm
                                WHERE timestamp < :cutoff_date
                                AND is_resolved = true
                            """),
                            {"cutoff_date": cutoff_date},
                        )
                        session.commit()
                        results["alarm_data"] = deleted_count
                        logger.info(f"清理了 {deleted_count} 条已解决的报警记录（超过 {settings.alarm_retention_days} 天）")
                except Exception as e:
                    session.rollback()
                    error_msg = f"清理 Alarm 失败: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
            
            # 3. 清理碳排放记录
            if settings.data_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.data_retention_days)
                try:
                    count = _count_carbon_rows_to_delete(session, cutoff_date)

                    if count > 0:
                        try:
                            session.exec(
                                text(f"""
                                    SELECT drop_chunks(
                                        'carbon_emission',
                                        INTERVAL '{settings.data_retention_days} days'
                                    );
                                """)
                            )
                        except Exception:
                            session.exec(
                                text("""
                                    DELETE FROM carbon_emission
                                    WHERE timestamp < :cutoff_date
                                """),
                                {"cutoff_date": cutoff_date},
                            )
                        session.commit()
                        results["carbon_emission"] = count
                        logger.info(f"清理了 {count} 条 CarbonEmission 记录（超过 {settings.data_retention_days} 天）")
                except Exception as e:
                    session.rollback()
                    error_msg = f"清理 CarbonEmission 失败: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # 4. 清理统计数据（保留时间更长）
            if settings.statistics_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.statistics_retention_days)
                try:
                    count_result = session.exec(
                        text("""
                            SELECT COUNT(*) FROM energy_statistics
                            WHERE stat_time < :cutoff_date
                        """),
                        {"cutoff_date": cutoff_date},
                    )
                    deleted_count = count_result.one()
                    deleted_count = deleted_count[0] if isinstance(deleted_count, tuple) else deleted_count

                    if deleted_count > 0:
                        session.exec(
                            text("""
                                DELETE FROM energy_statistics
                                WHERE stat_time < :cutoff_date
                            """),
                            {"cutoff_date": cutoff_date},
                        )
                        session.commit()
                        results["statistics"] = deleted_count
                        logger.info(f"清理了 {deleted_count} 条 EnergyStatistics 记录（超过 {settings.statistics_retention_days} 天）")
                except Exception as e:
                    session.rollback()
                    error_msg = f"清理 EnergyStatistics 失败: {e}"
                    logger.warning(error_msg)
                    results["errors"].append(error_msg)
            
            # 5. 执行 VACUUM 优化（可选，在非高峰时段）
        _run_vacuum_analyze()
        
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


def _count_rows_before_delete(session: Session, count_statement) -> int:
    """统计 SQLModel 查询结果条数。"""
    return len(session.exec(count_statement).all())


def _count_unresolved_alarms_to_delete(session: Session, cutoff_date: datetime) -> int:
    """统计待删除的已解决报警数量。"""
    return _count_scalar_result(
        session=session,
        query=text("""
            SELECT COUNT(*) FROM alarm
            WHERE timestamp < :cutoff_date
            AND is_resolved = true
        """),
        params={"cutoff_date": cutoff_date},
    )


def _count_carbon_rows_to_delete(session: Session, cutoff_date: datetime) -> int:
    """统计待删除的碳排放记录数量。"""
    return _count_scalar_result(
        session=session,
        query=text("""
            SELECT COUNT(*) FROM carbon_emission
            WHERE timestamp < :cutoff_date
        """),
        params={"cutoff_date": cutoff_date},
    )


def _count_scalar_result(session: Session, query, params: dict) -> int:
    """执行 count 查询并兼容 tuple / scalar 返回。"""
    result = session.exec(query, params)
    count = result.one()
    return count[0] if isinstance(count, tuple) else count


def _run_vacuum_analyze() -> None:
    """在事务外执行 VACUUM ANALYZE。"""
    try:
        with engine.connect().execution_options(isolation_level="AUTOCOMMIT") as connection:
            connection.execute(text("VACUUM ANALYZE"))
        logger.debug("执行了 VACUUM ANALYZE 优化")
    except Exception as e:
        logger.warning(f"VACUUM 失败: {e}")


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
