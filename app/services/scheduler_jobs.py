"""
定时任务执行体
"""

from __future__ import annotations

from app.core.logger import logger
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
