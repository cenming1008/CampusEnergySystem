"""
定时任务执行体
"""

from __future__ import annotations

from sqlmodel import Session

from app.core.database import engine
from app.core.logger import logger
from app.services.devices.compensation.capacitor_bank.service import CapacitorBankService
from app.services.data_cleanup_service import cleanup_old_data


def auto_cleanup_data() -> None:
    """自动清理过期数据。"""
    logger.info("开始自动清理过期数据...")

    try:
        result = cleanup_old_data()

        if result.get("status") == "success":
            total = result.get("total_deleted", 0)
            if total > 0:
                logger.info(f"✅ 自动清理完成：共清理 {total} 条记录")
            else:
                logger.debug("自动清理完成：没有需要清理的数据")
        elif result.get("status") == "disabled":
            logger.debug("自动数据清理已禁用")
        else:
            logger.warning(f"自动清理过程中出现错误: {result.get('errors', [])}")
    except Exception as exc:
        logger.error(f"自动清理数据时发生错误: {exc}")


def expire_compensation_control_timeouts() -> None:
    """主动收口补偿类待定控制日志，避免参数写入长期停留在 accepted/running。"""
    logger.info("开始扫描补偿控制待定日志超时状态...")

    try:
        with Session(engine) as session:
            expired_logs = CapacitorBankService.expire_pending_control_logs(
                session,
                control_event_notifier=CapacitorBankService.publish_control_log_update_event,
            )

        if expired_logs:
            logger.info(f"✅ 补偿控制超时收口完成：共更新 {len(expired_logs)} 条控制日志")
        else:
            logger.debug("补偿控制超时收口完成：没有需要更新的待定日志")
    except Exception as exc:
        logger.error(f"补偿控制超时收口执行失败: {exc}")
