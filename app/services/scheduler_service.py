"""
定时任务服务
使用APScheduler管理定时任务，包括LSTM模型自动训练
"""
from __future__ import annotations

import threading
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED, JobExecutionEvent
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from app.core.logger import logger
from app.core.metrics import observe_scheduler_job
from app.core.notifications import notification_service
from app.core.runtime_state import runtime_state
from app.services.scheduler_registry import register_default_jobs

# 全局调度器实例
_scheduler: Optional[BackgroundScheduler] = None
_scheduler_lock = threading.Lock()


def _scheduler_listener(event: JobExecutionEvent) -> None:
    job_id = getattr(event, "job_id", "unknown")
    if event.exception:
        runtime_state.increment("scheduler_job_failures_total")
        runtime_state.mark_service("scheduler", "degraded", f"job failed: {job_id}")
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
        runtime_state.mark_service("scheduler", "healthy", f"job executed: {job_id}")
        observe_scheduler_job(job_id, "success")


def get_scheduler() -> Optional[BackgroundScheduler]:
    """获取调度器实例"""
    return _scheduler


def start_scheduler():
    """启动定时任务调度器"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.warning("调度器已在运行")
            runtime_state.mark_service("scheduler", "healthy", "already running")
            return
        
        _scheduler = BackgroundScheduler()
        _scheduler.add_listener(_scheduler_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

        register_default_jobs(_scheduler)
        
        try:
            _scheduler.start()
            runtime_state.mark_service("scheduler", "healthy", "running")
            logger.info("定时任务调度器已启动")
        except Exception as exc:
            runtime_state.mark_service("scheduler", "unhealthy", str(exc))
            runtime_state.increment("scheduler_job_failures_total")
            raise


def stop_scheduler():
    """停止定时任务调度器"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=True)
            runtime_state.mark_service("scheduler", "stopped", "shutdown complete")
            logger.info("定时任务调度器已停止")
        _scheduler = None

def add_custom_job(func, trigger, job_id: str, **kwargs):
    """添加自定义定时任务"""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        raise RuntimeError("调度器未运行")
    
    _scheduler.add_job(
        func,
        trigger=trigger,
        id=job_id,
        replace_existing=True,
        **kwargs
    )
    runtime_state.mark_service("scheduler", "healthy", f"job added: {job_id}")
    logger.info(f"已添加自定义任务: {job_id}")


def remove_job(job_id: str):
    """移除定时任务"""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        return False
    
    try:
        _scheduler.remove_job(job_id)
        runtime_state.mark_service("scheduler", "healthy", f"job removed: {job_id}")
        logger.info(f"已移除任务: {job_id}")
        return True
    except Exception as exc:
        logger.warning(f"移除任务失败: job_id={job_id}, err={exc}")
        runtime_state.increment("scheduler_job_failures_total")
        return False


def get_jobs():
    """获取所有定时任务"""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        return []
    
    jobs = []
    for job in _scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
            "trigger": str(job.trigger)
        })
    
    return jobs
