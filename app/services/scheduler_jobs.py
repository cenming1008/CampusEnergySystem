"""
定时任务执行体
"""

from __future__ import annotations

from sqlmodel import Session, select

from app.core.database import engine
from app.core.logger import logger
from app.core.settings import settings
from app.services.data_cleanup_service import cleanup_old_data

try:
    from app.integrations.forecasting import ForecastAdapter
    from app.models.tables import Device
    from lstm_forecast import LSTM_AVAILABLE

    FORECAST_AVAILABLE = True
except ImportError:
    FORECAST_AVAILABLE = False
    LSTM_AVAILABLE = False


def auto_train_lstm_models() -> None:
    """自动训练 LSTM 模型。"""
    if not LSTM_AVAILABLE:
        logger.warning("LSTM服务不可用，跳过自动训练")
        return

    logger.info("开始自动训练LSTM模型...")

    try:
        with Session(engine) as session:
            adapter = ForecastAdapter()

            _train_model(adapter, session, prediction_type="load", device_id=None)

            devices = session.exec(select(Device).where(Device.is_active == True)).all()
            for device in devices:
                _train_model(adapter, session, prediction_type="load", device_id=device.id)

            for prediction_type in ("solar", "wind"):
                try:
                    result = adapter.train_model(
                        session=session,
                        prediction_type=prediction_type,
                        device_id=None,
                        days=60,
                        retrain=False,
                    )
                    logger.info(f"{prediction_type}预测模型训练完成: {result.get('status')}")
                except Exception as exc:
                    logger.warning(f"{prediction_type}预测模型训练失败（可能无相关数据）: {exc}")

        logger.info("LSTM模型自动训练完成")
    except Exception as exc:
        logger.error(f"自动训练LSTM模型时发生错误: {exc}")


def auto_update_forecasts() -> None:
    """自动更新预测。"""
    logger.debug("自动更新预测任务执行中...")

    if not FORECAST_AVAILABLE:
        logger.warning("预测模块不可用，跳过自动更新")
        return

    try:
        with Session(engine) as session:
            adapter = ForecastAdapter()
            algorithm = "lstm" if LSTM_AVAILABLE and settings.forecast_lstm_enabled else "moving_average"

            try:
                adapter.forecast_load(
                    session=session,
                    device_id=None,
                    hours=24,
                    algorithm=algorithm,
                )
            except Exception as exc:
                logger.warning(f"更新系统负荷预测失败: {exc}")

            devices = session.exec(select(Device).where(Device.is_active == True)).all()
            for device in devices:
                try:
                    adapter.forecast_load(
                        session=session,
                        device_id=device.id,
                        hours=24,
                        algorithm=algorithm,
                    )
                except Exception as exc:
                    logger.debug(f"更新设备 {device.id} 预测失败: {exc}")

        logger.debug("自动更新预测完成")
    except Exception as exc:
        logger.error(f"自动更新预测时发生错误: {exc}")


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


def _train_model(adapter: "ForecastAdapter", session: Session, prediction_type: str, device_id: int | None) -> None:
    """训练单个预测模型并记录日志。"""
    try:
        result = adapter.train_model(
            session=session,
            prediction_type=prediction_type,
            device_id=device_id,
            days=60,
            retrain=False,
        )
        if device_id is None:
            logger.info(f"系统{prediction_type}预测模型训练完成: {result.get('status')}")
        else:
            logger.info(f"设备 {device_id} {prediction_type}预测模型训练完成: {result.get('status')}")
    except Exception as exc:
        if device_id is None:
            logger.error(f"系统{prediction_type}预测模型训练失败: {exc}")
        else:
            logger.error(f"设备 {device_id} {prediction_type}预测模型训练失败: {exc}")
