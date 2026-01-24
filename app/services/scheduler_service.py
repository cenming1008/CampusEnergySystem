"""
定时任务服务
使用APScheduler管理定时任务，包括LSTM模型自动训练
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from typing import Optional
import threading

from sqlmodel import Session
from app.core.database import engine
from app.core.logger import logger
from app.core.settings import settings
from app.services.data_cleanup_service import cleanup_old_data

# 尝试导入预测适配器
try:
    from app.services.forecast_adapter import ForecastAdapter
    from lstm_forecast import LSTM_AVAILABLE
    FORECAST_AVAILABLE = True
except ImportError:
    FORECAST_AVAILABLE = False
    LSTM_AVAILABLE = False

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
        
        # 添加LSTM模型自动训练任务（如果启用）
        if settings.forecast_auto_update and LSTM_AVAILABLE:
            # 每天凌晨2点自动训练模型
            _scheduler.add_job(
                auto_train_lstm_models,
                trigger=CronTrigger(hour=2, minute=0),
                id='auto_train_lstm',
                name='自动训练LSTM模型',
                replace_existing=True
            )
            logger.info("已添加LSTM自动训练任务：每天凌晨2点执行")
        
        # 每小时更新预测（如果启用）
        if settings.forecast_auto_update:
            _scheduler.add_job(
                auto_update_forecasts,
                trigger=IntervalTrigger(hours=1),
                id='auto_update_forecasts',
                name='自动更新预测',
                replace_existing=True
            )
            logger.info("已添加自动更新预测任务：每小时执行")
        
        # 每天凌晨3点自动清理过期数据（如果启用）
        if settings.enable_auto_cleanup:
            _scheduler.add_job(
                auto_cleanup_data,
                trigger=CronTrigger(hour=3, minute=0),
                id='auto_cleanup_data',
                name='自动清理过期数据',
                replace_existing=True
            )
            logger.info("已添加自动数据清理任务：每天凌晨3点执行")
        
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


def auto_train_lstm_models():
    """自动训练LSTM模型（定时任务）"""
    if not LSTM_AVAILABLE:
        logger.warning("LSTM服务不可用，跳过自动训练")
        return
    
    logger.info("开始自动训练LSTM模型...")
    
    try:
        with Session(engine) as session:
            adapter = ForecastAdapter()
            
            # 训练负荷预测模型（系统级）
            try:
                result = adapter.train_model(
                    session=session,
                    prediction_type="load",
                    device_id=None,
                    days=60,
                    retrain=False  # 如果模型已存在，不强制重训
                )
                logger.info(f"系统负荷预测模型训练完成: {result.get('status')}")
            except Exception as e:
                logger.error(f"系统负荷预测模型训练失败: {e}")
            
            # 训练各设备的负荷预测模型
            from app.models.tables import Device
            from sqlmodel import select
            
            devices = session.exec(select(Device).where(Device.is_active == True)).all()
            for device in devices:
                try:
                    result = adapter.train_model(
                        session=session,
                        prediction_type="load",
                        device_id=device.id,
                        days=60,
                        retrain=False
                    )
                    logger.info(f"设备 {device.id} 负荷预测模型训练完成: {result.get('status')}")
                except Exception as e:
                    logger.error(f"设备 {device.id} 负荷预测模型训练失败: {e}")
            
            # 训练风光预测模型（如果有相关设备）
            for pred_type in ["solar", "wind"]:
                try:
                    result = adapter.train_model(
                        session=session,
                        prediction_type=pred_type,
                        device_id=None,
                        days=60,
                        retrain=False
                    )
                    logger.info(f"{pred_type}预测模型训练完成: {result.get('status')}")
                except Exception as e:
                    logger.warning(f"{pred_type}预测模型训练失败（可能无相关数据）: {e}")
        
        logger.info("LSTM模型自动训练完成")
    except Exception as e:
        logger.error(f"自动训练LSTM模型时发生错误: {e}")


def auto_update_forecasts():
    """自动更新预测（定时任务）"""
    logger.debug("自动更新预测任务执行中...")
    
    try:
        if not FORECAST_AVAILABLE:
            logger.warning("预测模块不可用，跳过自动更新")
            return
        
        with Session(engine) as session:
            adapter = ForecastAdapter()
            
            # 更新系统负荷预测
            try:
                adapter.forecast_load(
                    session=session,
                    device_id=None,
                    hours=24,
                    algorithm="lstm" if LSTM_AVAILABLE and settings.forecast_lstm_enabled else "moving_average"
                )
            except Exception as e:
                logger.warning(f"更新系统负荷预测失败: {e}")
            
            # 更新各设备预测
            from app.models.tables import Device
            from sqlmodel import select
            
            devices = session.exec(select(Device).where(Device.is_active == True)).all()
            for device in devices:
                try:
                    adapter.forecast_load(
                        session=session,
                        device_id=device.id,
                        hours=24,
                        algorithm="lstm" if LSTM_AVAILABLE and settings.forecast_lstm_enabled else "moving_average"
                    )
                except Exception as e:
                    logger.debug(f"更新设备 {device.id} 预测失败: {e}")
        
        logger.debug("自动更新预测完成")
    except Exception as e:
        logger.error(f"自动更新预测时发生错误: {e}")


def auto_cleanup_data():
    """自动清理过期数据（定时任务）"""
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
    
    except Exception as e:
        logger.error(f"自动清理数据时发生错误: {e}")


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
