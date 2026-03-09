"""
预测功能适配器
集成所有预测相关功能（数据生成、LSTM预测、简单预测等），连接后端和独立的预测模块
"""
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.models.tables import EnergyData, Device, Prediction, EnergyType
from app.core.settings import settings
from app.core.logger import logger

# 导入独立的预测模块
try:
    import sys
    from pathlib import Path
    
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    from lstm_forecast import (
        DataGenerator,
        ForecastUtils,
        LSTMForecastService,
        ModelVersionService,
        LSTM_AVAILABLE
    )
    FORECAST_MODULE_AVAILABLE = True
except ImportError as e:
    FORECAST_MODULE_AVAILABLE = False
    DataGenerator = None
    ForecastUtils = None
    LSTMForecastService = None
    ModelVersionService = None
    LSTM_AVAILABLE = False
    logger.warning(f"预测模块不可用: {e}")


class ForecastAdapter:
    """
    预测适配器类
    
    提供与后端主程序兼容的接口，内部调用独立的预测模块
    包含：
    - 数据生成功能
    - LSTM深度学习预测
    - 简单预测算法（移动平均、线性回归）
    - 模型版本管理
    """
    
    def __init__(self):
        """初始化适配器"""
        if not FORECAST_MODULE_AVAILABLE:
            raise ImportError("预测模块不可用")
        
        # LSTM配置
        if LSTM_AVAILABLE:
            try:
                lstm_units_str = settings.forecast_lstm_units
                lstm_units = [int(x.strip()) for x in lstm_units_str.split(',')]
                sequence_length = settings.forecast_lstm_sequence_length
                epochs = settings.forecast_lstm_epochs
            except AttributeError:
                lstm_units = [64, 32]
                sequence_length = 24
                epochs = 50
            
            config = {
                "sequence_length": sequence_length,
                "lstm_units": lstm_units,
                "dropout_rate": 0.2,
                "epochs": epochs,
                "batch_size": 32,
                "validation_split": 0.2,
                "patience": 10
            }
            
            self.lstm_service = LSTMForecastService(config=config)
            self.version_service = ModelVersionService()
        else:
            self.lstm_service = None
            self.version_service = None
    
    # ==================== 数据生成功能 ====================
    
    def generate_device_data(
        self,
        session: Session,
        device_id: int,
        days: int = 60,
        interval_minutes: int = 60,
        data_type: str = "load",
        clear_existing: bool = False
    ) -> int:
        """
        为指定设备生成数据
        
        Args:
            session: 数据库会话
            device_id: 设备ID
            days: 生成数据天数
            interval_minutes: 数据间隔（分钟）
            data_type: 数据类型（load/solar/wind）
            clear_existing: 是否清除现有数据
            
        Returns:
            生成的数据条数
        """
        # 检查设备是否存在
        device = session.get(Device, device_id)
        if not device:
            raise ValueError(f"设备 {device_id} 不存在")
        
        # 清除现有数据
        if clear_existing:
            self.clear_device_data(session, device_id)
        
        # 使用独立模块生成数据
        data_points = DataGenerator.generate_timeseries_data(
            days=days,
            interval_minutes=interval_minutes,
            data_type=data_type
        )
        
        # 保存到数据库
        from app.models.tables import EnergyData, EnergyType
        count = 0
        for timestamp, voltage, current, power, energy in data_points:
            device_data = EnergyData(
                device_id=device_id,
                timestamp=timestamp,
                voltage=voltage,
                current=current,
                power=power,
                energy=energy
            )
            session.add(device_data)
            count += 1
        
        session.commit()
        logger.info(f"为设备 {device_id} 生成了 {count} 条数据")
        return count
    
    def generate_system_data(
        self,
        session: Session,
        days: int = 60,
        interval_minutes: int = 60,
        clear_existing: bool = False
    ) -> int:
        """为所有活跃设备生成数据"""
        devices = session.exec(select(Device).where(Device.is_active == True)).all()
        total_count = 0
        
        for device in devices:
            # 根据设备类型选择数据类型
            device_type_lower = device.device_type.lower() if device.device_type else "load"
            
            if "solar" in device_type_lower or "光伏" in device_type_lower:
                data_type = "solar"
            elif "wind" in device_type_lower or "风电" in device_type_lower:
                data_type = "wind"
            else:
                data_type = "load"
            
            count = self.generate_device_data(
                session, device.id, days, interval_minutes, data_type, clear_existing
            )
            total_count += count
        
        return total_count
    
    def clear_device_data(
        self,
        session: Session,
        device_id: Optional[int] = None,
        days: Optional[int] = None
    ):
        """清除设备数据"""
        statement = select(EnergyData)
        
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        
        if days:
            cutoff_time = datetime.now() - timedelta(days=days)
            statement = statement.where(EnergyData.timestamp >= cutoff_time)
        
        data_to_delete = session.exec(statement).all()
        for data in data_to_delete:
            session.delete(data)
        
        session.commit()
        logger.info(f"清除了 {len(data_to_delete)} 条数据")
    
    # ==================== 预测功能 ====================
    
    def forecast_load(
        self,
        session: Session,
        device_id: Optional[int] = None,
        hours: int = None,
        algorithm: str = None
    ) -> List[Dict[str, Any]]:
        """
        负荷预测
        
        支持算法：lstm, moving_average, linear_regression
        """
        hours = hours or settings.forecast_horizon_hours
        algorithm = algorithm or settings.forecast_algorithm
        interval_minutes = settings.forecast_interval_minutes
        
        # 如果使用LSTM算法
        if algorithm == "lstm" and LSTM_AVAILABLE and self.lstm_service:
            try:
                start_time = datetime.now() - timedelta(hours=self.lstm_service.default_params["sequence_length"] + 1)
                statement = select(EnergyData).where(EnergyData.timestamp >= start_time)
                if device_id:
                    statement = statement.where(EnergyData.device_id == device_id)
                statement = statement.order_by(EnergyData.timestamp.asc())
                recent_data = list(session.exec(statement).all())
                
                results = self.lstm_service.predict(
                    recent_data=recent_data,
                    prediction_type="load",
                    device_id=device_id,
                    hours=hours,
                    interval_minutes=interval_minutes
                )
                
                # 保存预测结果
                self._save_predictions(session, "load", device_id, results, "lstm")
                return results
            except Exception as e:
                logger.warning(f"LSTM预测失败，回退到简单算法: {e}")
                algorithm = "moving_average"
        
        # 使用简单算法
        history_data = self._get_history_data(session, device_id, settings.forecast_history_days)
        if not history_data or len(history_data) < 2:
            logger.warning(f"历史数据不足，无法进行预测: device_id={device_id}")
            return []
        
        historical_powers = [d.flow_rate for d in history_data]
        
        # 调用简单算法
        if algorithm == "moving_average":
            predictions = ForecastUtils.moving_average_forecast(
                historical_powers, hours, interval_minutes
            )
        elif algorithm == "linear_regression":
            predictions = ForecastUtils.linear_regression_forecast(
                historical_powers, hours, interval_minutes
            )
        else:
            predictions = ForecastUtils.moving_average_forecast(
                historical_powers, hours, interval_minutes
            )
        
        # 保存预测结果
        self._save_predictions(session, "load", device_id, predictions, algorithm)
        return predictions
    
    def _get_history_data(
        self,
        session: Session,
        device_id: Optional[int],
        days: int
    ) -> List[EnergyData]:
        """获取历史数据"""
        start_time = datetime.now() - timedelta(days=days)
        statement = select(EnergyData).where(EnergyData.timestamp >= start_time)
        
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        
        statement = statement.order_by(EnergyData.timestamp.asc())
        return list(session.exec(statement).all())
    
    def _save_predictions(
        self,
        session: Session,
        prediction_type: str,
        device_id: Optional[int],
        predictions: List[Dict[str, Any]],
        algorithm: str
    ):
        """保存预测结果到数据库"""
        for pred in predictions:
            prediction = Prediction(
                prediction_type=prediction_type,
                device_id=device_id,
                forecast_time=pred["forecast_time"],
                predicted_value=pred["predicted_value"],
                confidence=pred.get("confidence"),
                algorithm=algorithm
            )
            session.add(prediction)
        
        session.commit()
    
    # ==================== LSTM训练和评估 ====================
    
    def train_lstm_model(
        self,
        session: Session,
        prediction_type: str,
        device_id: Optional[int] = None,
        days: int = 60,
        params: Optional[Dict] = None,
        retrain: bool = False,
        use_multivariate: bool = False,
        version: Optional[str] = None
    ) -> Dict[str, Any]:
        """训练LSTM模型"""
        if not LSTM_AVAILABLE or not self.lstm_service:
            raise ImportError("LSTM功能不可用，请安装TensorFlow")
        
        # 获取历史数据
        start_time = datetime.now() - timedelta(days=days)
        statement = select(EnergyData).where(EnergyData.timestamp >= start_time)
        
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        
        statement = statement.order_by(EnergyData.timestamp.asc())
        data = list(session.exec(statement).all())
        
        if len(data) < 100:
            raise ValueError(f"历史数据不足，至少需要100个数据点，当前只有{len(data)}个")
        
        # 调用LSTM模块训练
        result = self.lstm_service.train_model(
            data=data,
            prediction_type=prediction_type,
            device_id=device_id,
            days=days,
            params=params,
            retrain=retrain,
            use_multivariate=use_multivariate,
            version=version,
            logger=logger
        )
        
        # 如果训练成功且有版本号，创建版本记录
        if result.get("status") == "success" and version and self.version_service:
            try:
                eval_result = self.evaluate_lstm_model(
                    session, prediction_type, device_id, test_days=7
                )
                
                self.version_service.create_version(
                    prediction_type=prediction_type,
                    device_id=device_id,
                    version=version,
                    model_path=result["model_path"],
                    metadata_path=result.get("metadata_path", ""),
                    metrics={
                        "mae": eval_result.get("mae", 0),
                        "mape": eval_result.get("mape", 0),
                        "rmse": eval_result.get("rmse", 0)
                    },
                    logger=logger
                )
            except Exception as e:
                logger.warning(f"创建版本记录失败: {e}")
        
        return result
    
    def evaluate_lstm_model(
        self,
        session: Session,
        prediction_type: str,
        device_id: Optional[int] = None,
        test_days: int = 7
    ) -> Dict[str, Any]:
        """评估LSTM模型性能"""
        if not LSTM_AVAILABLE or not self.lstm_service:
            raise ImportError("LSTM功能不可用")
        
        # 获取测试数据
        end_time = datetime.now() - timedelta(days=test_days)
        start_time = end_time - timedelta(days=test_days * 2)
        
        statement = select(EnergyData).where(
            EnergyData.timestamp >= start_time,
            EnergyData.timestamp < end_time
        )
        
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        
        statement = statement.order_by(EnergyData.timestamp.asc())
        test_data = list(session.exec(statement).all())
        
        if len(test_data) < 100:
            raise ValueError("测试数据不足")
        
        return self.lstm_service.evaluate_model(
            test_data=test_data,
            prediction_type=prediction_type,
            device_id=device_id,
            test_days=test_days
        )
    
    # ==================== 版本管理 ====================
    
    def list_versions(
        self,
        prediction_type: str,
        device_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """列出所有模型版本"""
        if not self.version_service:
            return []
        return self.version_service.list_versions(prediction_type, device_id)
    
    def get_version_info(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str
    ) -> Optional[Dict[str, Any]]:
        """获取指定版本的详细信息"""
        if not self.version_service:
            return None
        return self.version_service.get_version_info(prediction_type, device_id, version)
    
    def set_active_version(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str
    ) -> bool:
        """设置活动版本"""
        if not self.version_service:
            return False
        return self.version_service.set_active_version(
            prediction_type, device_id, version, logger
        )
    
    def get_active_version(
        self,
        prediction_type: str,
        device_id: Optional[int]
    ) -> Optional[str]:
        """获取当前活动版本"""
        if not self.version_service:
            return None
        return self.version_service.get_active_version(prediction_type, device_id)
    
    def compare_versions(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version1: str,
        version2: str
    ) -> Dict[str, Any]:
        """对比两个版本的性能"""
        if not self.version_service:
            raise ValueError("版本管理功能不可用")
        return self.version_service.compare_versions(
            prediction_type, device_id, version1, version2
        )
    
    def delete_version(
        self,
        prediction_type: str,
        device_id: Optional[int],
        version: str
    ) -> bool:
        """删除模型版本"""
        if not self.version_service:
            return False
        return self.version_service.delete_version(
            prediction_type, device_id, version, logger
        )
