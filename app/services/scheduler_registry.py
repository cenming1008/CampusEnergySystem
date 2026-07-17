"""
调度任务注册表
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Iterable

from apscheduler.triggers.cron import CronTrigger

from app.core.logger import logger
from app.core.settings import settings
from app.services.scheduler_jobs import (
    auto_cleanup_data,
    evaluate_storage_ems_rules,
    expire_compensation_control_timeouts,
    expire_storage_control_timeouts,
    sync_platform_comm_alarms,
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

    jobs.append(
        JobDefinition(
            id="expire_compensation_control_timeouts",
            name="补偿控制超时收口",
            trigger=CronTrigger(minute="*"),
            func=expire_compensation_control_timeouts,
            log_message="已添加补偿控制超时收口任务：每分钟执行",
        )
    )

    if settings.storage_ems_enabled:
        jobs.append(
            JobDefinition(
                id="evaluate_storage_ems_rules",
                name="储能实时 EMS 规则",
                trigger=CronTrigger(minute="*"),
                func=evaluate_storage_ems_rules,
                log_message="已添加储能实时 EMS 规则任务：每分钟执行",
            )
        )

    jobs.append(
        JobDefinition(
            id="expire_storage_control_timeouts",
            name="储能控制超时收口",
            trigger=CronTrigger(minute="*"),
            func=expire_storage_control_timeouts,
            log_message="已添加储能控制超时收口任务：每分钟执行",
        )
    )

    jobs.append(
        JobDefinition(
            id="sync_platform_comm_alarms",
            name="平台通讯告警同步",
            trigger=CronTrigger(minute="*"),
            func=sync_platform_comm_alarms,
            log_message="已添加平台通讯告警同步任务：每分钟执行",
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
