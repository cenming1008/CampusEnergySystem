"""
调度任务注册表
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

from app.core.logger import logger
from app.core.settings import settings
from app.services.scheduler_jobs import (
    LSTM_AVAILABLE,
    auto_cleanup_data,
    auto_train_lstm_models,
    auto_update_forecasts,
)


@dataclass(frozen=True)
class JobDefinition:
    id: str
    name: str
    trigger: object
    func: Callable[[], None]
    log_message: str


def get_enabled_job_definitions() -> Iterable[JobDefinition]:
    """返回当前配置下启用的调度任务定义。"""
    jobs: list[JobDefinition] = []

    if settings.forecast_auto_update and LSTM_AVAILABLE:
        jobs.append(
            JobDefinition(
                id="auto_train_lstm",
                name="自动训练LSTM模型",
                trigger=CronTrigger(hour=2, minute=0),
                func=auto_train_lstm_models,
                log_message="已添加LSTM自动训练任务：每天凌晨2点执行",
            )
        )

    if settings.forecast_auto_update:
        jobs.append(
            JobDefinition(
                id="auto_update_forecasts",
                name="自动更新预测",
                trigger=IntervalTrigger(hours=1),
                func=auto_update_forecasts,
                log_message="已添加自动更新预测任务：每小时执行",
            )
        )

    if settings.enable_auto_cleanup:
        jobs.append(
            JobDefinition(
                id="auto_cleanup_data",
                name="自动清理过期数据",
                trigger=CronTrigger(hour=3, minute=0),
                func=auto_cleanup_data,
                log_message="已添加自动数据清理任务：每天凌晨3点执行",
            )
        )

    return jobs


def register_default_jobs(scheduler) -> None:
    """向调度器注册默认任务。"""
    for job in get_enabled_job_definitions():
        scheduler.add_job(
            job.func,
            trigger=job.trigger,
            id=job.id,
            name=job.name,
            replace_existing=True,
        )
        logger.info(job.log_message)
