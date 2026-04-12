"""
定时任务服务
使用 APScheduler 管理定时任务，并在多实例场景下做 owner 级互斥。
"""
from __future__ import annotations

import asyncio
import os
import socket
import threading
from typing import Any, Optional
from uuid import uuid4

from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.background import BackgroundScheduler

from app.core.logger import logger
from app.core.metrics import observe_scheduler_job
from app.core.notifications import notification_service
from app.core.redis import RedisClient
from app.core.runtime_state import runtime_state
from app.core.settings import settings
from app.services.scheduler_registry import register_default_jobs

# 全局调度器实例
_scheduler: Optional[BackgroundScheduler] = None
_scheduler_lock = threading.Lock()
_lease_owner_token: Optional[str] = None
_lease_renew_task: Optional[asyncio.Task] = None
_instance_id = f"{socket.gethostname()}:{os.getpid()}:{uuid4().hex[:8]}"


def _scheduler_listener(event: JobExecutionEvent) -> None:
    job_id = getattr(event, "job_id", "unknown")
    if event.exception:
        runtime_state.increment("scheduler_job_failures_total")
        runtime_state.mark_service(
            "scheduler",
            "degraded",
            f"job failed: {job_id}",
            meta=_build_scheduler_meta(
                owner=bool(_lease_owner_token),
                scheduler_state="owner" if _lease_owner_token else "stopped",
            ),
        )
        observe_scheduler_job(job_id, "failed")
        logger.warning(f"定时任务执行失败: {job_id} - {event.exception}")
        notification_service.notify(
            event_key=f"scheduler:{job_id}",
            severity="warning",
            title=f"Scheduler job failed: {job_id}",
            message="定时任务执行失败",
            details={"job_id": job_id, "error": str(event.exception)},
        )
    else:
        runtime_state.mark_service(
            "scheduler",
            "healthy",
            f"job executed: {job_id}",
            meta=_build_scheduler_meta(
                owner=bool(_lease_owner_token),
                scheduler_state="owner" if _lease_owner_token else "stopped",
            ),
        )
        observe_scheduler_job(job_id, "success")


def _resolve_scheduler_mode() -> str:
    return settings.scheduler_effective_mode


def _build_scheduler_meta(
    owner: bool,
    scheduler_state: str = "unknown",
    owner_token: Optional[str] = None,
    lease_holder: Optional[str] = None,
    renew_task_active: Optional[bool] = None,
) -> dict[str, Any]:
    task = _lease_renew_task
    return {
        "enabled": bool(settings.scheduler_enabled),
        "mode": _resolve_scheduler_mode(),
        "instance_id": _instance_id,
        "scheduler_state": scheduler_state,
        "owner": owner,
        "owner_token": owner_token or _lease_owner_token,
        "lease_key": settings.scheduler_lease_key,
        "lease_holder": lease_holder,
        "lease_ttl_seconds": int(settings.scheduler_lease_ttl_seconds),
        "lease_renew_interval_seconds": int(settings.scheduler_lease_renew_interval_seconds),
        "renew_task_active": (
            renew_task_active
            if renew_task_active is not None
            else bool(task is not None and not task.done())
        ),
        "scheduler_running": bool(_scheduler is not None and _scheduler.running),
        "jobs_count": len(_scheduler.get_jobs()) if _scheduler is not None and _scheduler.running else 0,
    }


def _start_scheduler_process() -> None:
    global _scheduler

    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.warning("调度器已在运行")
            runtime_state.mark_service(
                "scheduler",
                "healthy",
                "already running",
                meta=_build_scheduler_meta(
                    owner=bool(_lease_owner_token),
                    scheduler_state="owner" if _lease_owner_token else "local",
                ),
            )
            return

        _scheduler = BackgroundScheduler()
        _scheduler.add_listener(_scheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)
        register_default_jobs(_scheduler)

        try:
            _scheduler.start()
            runtime_state.mark_service(
                "scheduler",
                "healthy",
                "running",
                meta=_build_scheduler_meta(
                    owner=bool(_lease_owner_token),
                    scheduler_state="owner" if _lease_owner_token else "local",
                ),
            )
            logger.info("定时任务调度器已启动")
        except Exception as exc:
            runtime_state.mark_service(
                "scheduler",
                "unhealthy",
                str(exc),
                meta=_build_scheduler_meta(
                    owner=bool(_lease_owner_token),
                    scheduler_state="failed-closed",
                ),
            )
            runtime_state.increment("scheduler_job_failures_total")
            raise


def _stop_scheduler_process(detail: str) -> None:
    global _scheduler
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=True)
            logger.info("定时任务调度器已停止")
        _scheduler = None
    runtime_state.mark_service(
        "scheduler",
        "stopped",
        detail,
        meta=_build_scheduler_meta(owner=False, scheduler_state="stopped", owner_token=None),
    )


async def _scheduler_lease_renew_loop(owner_token: str) -> None:
    global _lease_owner_token
    while _lease_owner_token == owner_token:
        try:
            await asyncio.sleep(max(1, int(settings.scheduler_lease_renew_interval_seconds)))
            renewed = await RedisClient.renew_lease(
                settings.scheduler_lease_key,
                owner_token,
                int(settings.scheduler_lease_ttl_seconds),
            )
            if renewed:
                runtime_state.mark_service(
                    "scheduler",
                    "healthy",
                    "lease renewed",
                    meta=_build_scheduler_meta(
                        owner=True,
                        scheduler_state="owner",
                        owner_token=owner_token,
                        renew_task_active=True,
                    ),
                )
                continue

            logger.error("scheduler owner lease 已丢失，停止本地调度器")
            _lease_owner_token = None
            _stop_scheduler_process("lease lost")
            runtime_state.mark_service(
                "scheduler",
                "unhealthy",
                "scheduler lease lost",
                meta=_build_scheduler_meta(
                    owner=False,
                    scheduler_state="failed-closed",
                    owner_token=None,
                    renew_task_active=False,
                ),
            )
            return
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.error(f"scheduler owner lease 续租失败: {exc}")
            _lease_owner_token = None
            _stop_scheduler_process("lease renew failed")
            runtime_state.mark_service(
                "scheduler",
                "unhealthy",
                f"lease renew failed: {exc}",
                meta=_build_scheduler_meta(
                    owner=False,
                    scheduler_state="failed-closed",
                    owner_token=None,
                    renew_task_active=False,
                ),
            )
            return


async def start_scheduler() -> dict[str, Any]:
    """启动定时任务调度器。"""
    global _lease_owner_token, _lease_renew_task

    if not settings.scheduler_enabled:
        runtime_state.mark_service(
            "scheduler",
            "healthy",
            "scheduler disabled by configuration",
            meta=_build_scheduler_meta(
                owner=False,
                scheduler_state="skipped",
                renew_task_active=False,
            ),
        )
        return {"status": "skipped", "owner": False}

    mode = _resolve_scheduler_mode()
    if mode == "local":
        _start_scheduler_process()
        runtime_state.mark_service(
            "scheduler",
            "healthy",
            "running in local mode",
            meta=_build_scheduler_meta(
                owner=True,
                scheduler_state="owner",
                renew_task_active=False,
            ),
        )
        return {"status": "owner", "owner": True}

    try:
        acquired = await RedisClient.acquire_lease(
            settings.scheduler_lease_key,
            _instance_id,
            int(settings.scheduler_lease_ttl_seconds),
        )
    except Exception as exc:
        runtime_state.mark_service(
            "scheduler",
            "unhealthy",
            f"lease acquire failed: {exc}",
            meta=_build_scheduler_meta(
                owner=False,
                scheduler_state="failed-closed",
                renew_task_active=False,
            ),
        )
        logger.warning(f"⚠️ scheduler owner 竞争失败，按 fail-closed 跳过启动: {exc}")
        return {"status": "failed-closed", "owner": False, "detail": str(exc)}

    if not acquired:
        lease_holder = None
        try:
            lease_holder = await RedisClient.get_value(settings.scheduler_lease_key)
        except Exception:
            lease_holder = None
        runtime_state.mark_service(
            "scheduler",
            "healthy",
            "scheduler lease held by another instance",
            meta=_build_scheduler_meta(
                owner=False,
                scheduler_state="standby",
                owner_token=None,
                lease_holder=lease_holder,
                renew_task_active=False,
            ),
        )
        logger.info(f"当前实例未取得 scheduler owner，进入 standby: holder={lease_holder}")
        return {"status": "standby", "owner": False, "lease_holder": lease_holder}

    _lease_owner_token = _instance_id
    _start_scheduler_process()
    if _lease_renew_task is not None and not _lease_renew_task.done():
        _lease_renew_task.cancel()
    _lease_renew_task = asyncio.create_task(_scheduler_lease_renew_loop(_instance_id))
    runtime_state.mark_service(
        "scheduler",
        "healthy",
        "running with redis owner lease",
        meta=_build_scheduler_meta(
            owner=True,
            scheduler_state="owner",
            owner_token=_instance_id,
            renew_task_active=True,
        ),
    )
    logger.info(f"当前实例取得 scheduler owner: {_instance_id}")
    return {"status": "owner", "owner": True, "owner_token": _instance_id}


async def stop_scheduler() -> dict[str, Any]:
    """停止定时任务调度器并释放 owner lease。"""
    global _lease_owner_token, _lease_renew_task

    owner_token = _lease_owner_token
    if _lease_renew_task is not None:
        _lease_renew_task.cancel()
        try:
            await _lease_renew_task
        except asyncio.CancelledError:
            pass
        finally:
            _lease_renew_task = None

    _stop_scheduler_process("shutdown complete")

    released = False
    if owner_token:
        try:
            released = await RedisClient.release_lease(settings.scheduler_lease_key, owner_token)
        except Exception as exc:
            runtime_state.mark_service(
                "scheduler",
                "degraded",
                f"lease release failed: {exc}",
                meta=_build_scheduler_meta(
                    owner=False,
                    scheduler_state="failed-release",
                    owner_token=None,
                    renew_task_active=False,
                ),
            )
            logger.warning(f"⚠️ scheduler owner lease 释放失败: {exc}")
        finally:
            _lease_owner_token = None
    else:
        _lease_owner_token = None

    runtime_state.mark_service(
        "scheduler",
        "stopped",
        "shutdown complete",
        meta=_build_scheduler_meta(
            owner=False,
            scheduler_state="stopped",
            owner_token=None,
            renew_task_active=False,
        ),
    )
    return {"status": "stopped", "owner": False, "lease_released": released}


def get_scheduler() -> Optional[BackgroundScheduler]:
    """获取调度器实例。"""
    return _scheduler


def get_scheduler_status() -> dict[str, Any]:
    """返回 scheduler 当前运行状态。"""
    payload = runtime_state.get_service("scheduler")
    return {
        "status": payload.get("meta", {}).get("scheduler_state", payload.get("status", "unknown")),
        "health": payload.get("status", "unknown"),
        "detail": payload.get("detail"),
        "updated_at": payload.get("updated_at"),
        "meta": payload.get("meta", {}),
        "jobs_count": len(get_jobs()),
    }


def add_custom_job(func, trigger, job_id: str, **kwargs):
    """添加自定义定时任务。"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        raise RuntimeError("调度器未运行")

    _scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        **kwargs,
    )
    runtime_state.mark_service(
        "scheduler",
        "healthy",
        f"job added: {job_id}",
        meta=_build_scheduler_meta(
            owner=bool(_lease_owner_token),
            scheduler_state="owner" if _lease_owner_token else "local",
        ),
    )
    logger.info(f"已添加自定义任务: {job_id}")


def remove_job(job_id: str):
    """移除定时任务。"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        return False

    try:
        _scheduler.remove_job(job_id)
        runtime_state.mark_service(
            "scheduler",
            "healthy",
            f"job removed: {job_id}",
            meta=_build_scheduler_meta(
                owner=bool(_lease_owner_token),
                scheduler_state="owner" if _lease_owner_token else "local",
            ),
        )
        logger.info(f"已移除任务: {job_id}")
        return True
    except Exception as exc:
        logger.warning(f"移除任务失败: job_id={job_id}, err={exc}")
        runtime_state.increment("scheduler_job_failures_total")
        return False


def get_jobs():
    """获取所有定时任务。"""
    global _scheduler

    if _scheduler is None or not _scheduler.running:
        return []

    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append(
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger),
            }
        )

    return jobs
