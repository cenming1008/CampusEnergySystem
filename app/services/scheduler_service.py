"""
定时任务服务
使用APScheduler管理定时任务，包括LSTM模型自动训练
"""
from __future__ import annotations

import threading
from apscheduler.schedulers.background import BackgroundScheduler
from typing import Optional
from app.core.logger import logger
from app.services.scheduler_registry import register_default_jobs

# 全局调度器实例
_scheduler: Optional[BackgroundScheduler] = None
_scheduler_lock = threading.Lock()


def get_scheduler() -> Optional[BackgroundScheduler]:
    """获取调度器实例"""
    return _scheduler


def start_scheduler():
    """启动定时任务调度器"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            logger.warning("调度器已在运行")
            return
        
        _scheduler = BackgroundScheduler()

        register_default_jobs(_scheduler)
        
        _scheduler.start()
        logger.info("定时任务调度器已启动")


def stop_scheduler():
    """停止定时任务调度器"""
    global _scheduler
    
    with _scheduler_lock:
        if _scheduler is not None and _scheduler.running:
            _scheduler.shutdown(wait=True)
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
    logger.info(f"已添加自定义任务: {job_id}")


def remove_job(job_id: str):
    """移除定时任务"""
    global _scheduler
    
    if _scheduler is None or not _scheduler.running:
        return False
    
    try:
        _scheduler.remove_job(job_id)
        logger.info(f"已移除任务: {job_id}")
        return True
    except Exception:
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
