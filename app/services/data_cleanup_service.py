"""
数据清理服务
自动清理过期的时序数据和历史记录
"""
from datetime import datetime, timedelta
from typing import Any, Dict, Iterable, Optional

from sqlmodel import Session, text
from app.core.database import engine
from app.core.logger import logger
from app.core.settings import settings


CLEANUP_RESULT_KEYS = (
    "energy_data",
    "alarm_data",
    "carbon_emission",
    "statistics",
    "mqtt_ingestion",
    "audit_event",
    "svg_telemetry",
    "capacitor_bank_telemetry",
)

MANUAL_CLEANUP_TARGETS = (
    ("energy_data", "energydata", "timestamp", None),
    ("alarm_data", "alarm", "timestamp", "is_resolved = true"),
    ("carbon_emission", "carbon_emission", "timestamp", None),
    ("mqtt_ingestion", "mqtt_ingestion_record", "received_at", None),
    ("audit_event", "audit_event", "created_at", None),
    ("svg_telemetry", "svg_telemetry", "timestamp", None),
    ("capacitor_bank_telemetry", "capacitor_bank_telemetry", "timestamp", None),
)

ALL_RUNTIME_TARGETS = MANUAL_CLEANUP_TARGETS + (
    ("statistics", "energy_statistics", "stat_time", None),
)


def cleanup_old_data() -> Dict[str, Any]:
    """
    清理过期数据（定时任务）
    
    返回清理统计信息
    """
    if not settings.enable_auto_cleanup:
        logger.info("自动数据清理已禁用，跳过清理")
        return {"status": "disabled"}
    
    results = _new_cleanup_result()
    
    try:
        with Session(engine) as session:
            if settings.data_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.data_retention_days)
                _merge_cleanup_results(
                    results,
                    cleanup_targets_before(
                        session,
                        cutoff_date,
                        (
                            ("energy_data", "energydata", "timestamp", None),
                            ("carbon_emission", "carbon_emission", "timestamp", None),
                            ("svg_telemetry", "svg_telemetry", "timestamp", None),
                            ("capacitor_bank_telemetry", "capacitor_bank_telemetry", "timestamp", None),
                        ),
                    ),
                )
            
            if settings.alarm_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.alarm_retention_days)
                _merge_cleanup_results(
                    results,
                    cleanup_targets_before(session, cutoff_date, (("alarm_data", "alarm", "timestamp", "is_resolved = true"),)),
                )
            
            if settings.statistics_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.statistics_retention_days)
                _merge_cleanup_results(
                    results,
                    cleanup_targets_before(session, cutoff_date, (("statistics", "energy_statistics", "stat_time", None),)),
                )
            
            if settings.mqtt_ingestion_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.mqtt_ingestion_retention_days)
                _merge_cleanup_results(
                    results,
                    cleanup_targets_before(
                        session,
                        cutoff_date,
                        (("mqtt_ingestion", "mqtt_ingestion_record", "received_at", None),),
                    ),
                )

            if settings.audit_event_retention_days > 0:
                cutoff_date = datetime.now() - timedelta(days=settings.audit_event_retention_days)
                _merge_cleanup_results(
                    results,
                    cleanup_targets_before(session, cutoff_date, (("audit_event", "audit_event", "created_at", None),)),
                )

        _run_vacuum_analyze()
        
        total_deleted = _total_deleted(results)
        
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


def cleanup_runtime_data_before(session: Session, cutoff_time: datetime, *, hours: Optional[int] = None) -> Dict[str, Any]:
    """清理指定时间前的运行/历史数据，供手动清理接口复用。"""
    results = _new_cleanup_result(cutoff_time=cutoff_time, hours=hours)
    _merge_cleanup_results(results, cleanup_targets_before(session, cutoff_time, MANUAL_CLEANUP_TARGETS))
    results["total_deleted"] = _total_deleted(results)
    results["status"] = "success" if not results["errors"] else "partial"
    return results


def cleanup_all_runtime_data(session: Session) -> Dict[str, Any]:
    """清空运行/历史数据，不删除设备、用户、位置和参数档案等主数据。"""
    results = _new_cleanup_result()
    for key, table_name, _time_column, where_clause in ALL_RUNTIME_TARGETS:
        try:
            results[key] = _clear_table(session, table_name, where_clause)
            session.commit()
        except Exception as exc:
            session.rollback()
            error_msg = f"清空 {table_name} 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
    results["total_deleted"] = _total_deleted(results)
    results["status"] = "success" if not results["errors"] else "partial"
    return results


def cleanup_targets_before(
    session: Session,
    cutoff_time: datetime,
    targets: Iterable[tuple[str, str, str, Optional[str]]],
) -> Dict[str, Any]:
    """按统一口径删除指定时间前的目标表记录。"""
    results = _new_cleanup_result(cutoff_time=cutoff_time)
    for key, table_name, time_column, where_clause in targets:
        try:
            results[key] = _delete_rows_before(session, table_name, time_column, cutoff_time, where_clause)
            session.commit()
        except Exception as exc:
            session.rollback()
            error_msg = f"清理 {table_name} 失败: {exc}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
    results["total_deleted"] = _total_deleted(results)
    results["status"] = "success" if not results["errors"] else "partial"
    return results


def _new_cleanup_result(*, cutoff_time: Optional[datetime] = None, hours: Optional[int] = None) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "timestamp": datetime.now().isoformat(),
        "errors": [],
    }
    for key in CLEANUP_RESULT_KEYS:
        result[key] = 0
    if cutoff_time is not None:
        result["cutoff_time"] = cutoff_time.isoformat()
    if hours is not None:
        result["hours"] = hours
    return result


def _merge_cleanup_results(target: Dict[str, Any], source: Dict[str, Any]) -> None:
    for key in CLEANUP_RESULT_KEYS:
        target[key] = int(target.get(key, 0)) + int(source.get(key, 0))
    target["errors"].extend(source.get("errors", []))


def _total_deleted(results: Dict[str, Any]) -> int:
    return sum(int(results.get(key, 0)) for key in CLEANUP_RESULT_KEYS)


def _delete_rows_before(
    session: Session,
    table_name: str,
    time_column: str,
    cutoff_time: datetime,
    where_clause: Optional[str] = None,
) -> int:
    extra_where = f" AND {where_clause}" if where_clause else ""
    deleted_stmt = text(
        f"""
        WITH deleted AS (
            DELETE FROM {table_name}
            WHERE {time_column} < :cutoff_time
            {extra_where}
            RETURNING 1
        )
        SELECT COUNT(*) FROM deleted
        """
    )
    return _execute_scalar_count(session, deleted_stmt, {"cutoff_time": cutoff_time})


def _clear_table(session: Session, table_name: str, where_clause: Optional[str] = None) -> int:
    if where_clause:
        deleted_stmt = text(
            f"""
            WITH deleted AS (
                DELETE FROM {table_name}
                WHERE {where_clause}
                RETURNING 1
            )
            SELECT COUNT(*) FROM deleted
            """
        )
        return _execute_scalar_count(session, deleted_stmt, {})

    total = _execute_scalar_count(session, text(f"SELECT COUNT(*) FROM {table_name}"), {})
    session.execute(text(f"TRUNCATE TABLE {table_name}"))
    return total


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
    return _execute_scalar_count(session, query, params)


def _execute_scalar_count(session: Session, query, params: dict) -> int:
    result = session.execute(query.bindparams(**params) if params else query)
    count = result.scalar()
    return int(count) if count is not None else 0


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
    stats: Dict[str, Any] = {"timestamp": datetime.now().isoformat()}
    
    try:
        with Session(engine) as session:
            stats["energy_data"] = _table_statistics(session, "energydata", "timestamp")
            stats["alarm_data"] = _alarm_statistics(session)
            stats["carbon_emission"] = _table_statistics(session, "carbon_emission", "timestamp")
            stats["statistics"] = _table_statistics(session, "energy_statistics", "stat_time")
            stats["mqtt_ingestion"] = _table_statistics(session, "mqtt_ingestion_record", "received_at")
            stats["audit_event"] = _table_statistics(session, "audit_event", "created_at")
            stats["svg_telemetry"] = _table_statistics(session, "svg_telemetry", "timestamp")
            stats["capacitor_bank_telemetry"] = _table_statistics(
                session,
                "capacitor_bank_telemetry",
                "timestamp",
            )
    
    except Exception as e:
        logger.error(f"获取数据统计失败: {e}")
        stats["error"] = str(e)
    
    return stats


def _table_statistics(session: Session, table_name: str, time_column: str) -> Dict[str, Any]:
    result = session.exec(
        text(
            f"""
            SELECT
                COUNT(*) as total,
                MIN({time_column}) as oldest,
                MAX({time_column}) as newest
            FROM {table_name}
            """
        )
    ).first()
    if not result:
        return {"total": 0, "oldest": None, "newest": None}
    total = result[0] if isinstance(result, tuple) else result.total
    oldest = result[1] if isinstance(result, tuple) else result.oldest
    newest = result[2] if isinstance(result, tuple) else result.newest
    return {
        "total": total,
        "oldest": str(oldest) if oldest else None,
        "newest": str(newest) if newest else None,
    }


def _alarm_statistics(session: Session) -> Dict[str, Any]:
    result = session.exec(
        text(
            """
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE is_resolved = false) as unresolved,
                MIN(timestamp) as oldest,
                MAX(timestamp) as newest
            FROM alarm
            """
        )
    ).first()
    if not result:
        return {"total": 0, "unresolved": 0, "oldest": None, "newest": None}
    total = result[0] if isinstance(result, tuple) else result.total
    unresolved = result[1] if isinstance(result, tuple) else result.unresolved
    oldest = result[2] if isinstance(result, tuple) else result.oldest
    newest = result[3] if isinstance(result, tuple) else result.newest
    return {
        "total": total,
        "unresolved": unresolved,
        "oldest": str(oldest) if oldest else None,
        "newest": str(newest) if newest else None,
    }
