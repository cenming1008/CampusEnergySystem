"""
独立的LSTM预测服务
与后端主程序解耦，提供LSTM深度学习预测功能
"""
import os
import json
import pickle
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from pathlib import Path
import numpy as np

# 尝试导入TensorFlow/Keras
try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import Sequential, load_model
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
    from sklearn.preprocessing import MinMaxScaler
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


class LSTMForecastService:
    """
    LSTM预测服务类
    
    使用长短期记忆网络（LSTM）进行时间序列预测
    支持负荷预测和风光预测
    
    这是一个独立的模块，不依赖后端主程序
    """
    
    # 模型存储目录
    MODEL_DIR = Path("models/lstm")
    SCALER_DIR = Path("models/scalers")
    VERSION_DIR = Path("models/versions")
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化LSTM服务
        
        Args:
            config: 配置字典，包含：
                - sequence_length: 序列长度（默认24）
                - lstm_units: LSTM单元数列表（默认[64, 32]）
                - dropout_rate: Dropout比率（默认0.2）
                - epochs: 训练轮数（默认50）
                - batch_size: 批次大小（默认32）
                - validation_split: 验证集比例（默认0.2）
                - patience: 早停耐心值（默认10）
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow未安装，无法使用LSTM预测功能。请运行: pip install tensorflow scikit-learn")
        
        # 创建模型目录
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        self.SCALER_DIR.mkdir(parents=True, exist_ok=True)
        self.VERSION_DIR.mkdir(parents=True, exist_ok=True)
        
        # 从配置或默认值获取超参数
        if config:
            self.default_params = {
                "sequence_length": config.get("sequence_length", 24),
                "lstm_units": config.get("lstm_units", [64, 32]),
                "dropout_rate": config.get("dropout_rate", 0.2),
                "epochs": config.get("epochs", 50),
                "batch_size": config.get("batch_size", 32),
                "validation_split": config.get("validation_split", 0.2),
                "patience": config.get("patience", 10)
            }
        else:
            # 默认超参数
            self.default_params = {
                "sequence_length": 24,
                "lstm_units": [64, 32],
                "dropout_rate": 0.2,
                "epochs": 50,
                "batch_size": 32,
                "validation_split": 0.2,
                "patience": 10
            }
    
    @staticmethod
    def _get_model_path(prediction_type: str, device_id: Optional[int] = None) -> Path:
        """获取模型文件路径"""
        model_name = f"{prediction_type}"
        if device_id:
            model_name += f"_device_{device_id}"
        return LSTMForecastService.MODEL_DIR / f"{model_name}.h5"
    
    @staticmethod
    def _get_scaler_path(prediction_type: str, device_id: Optional[int] = None) -> Path:
        """获取数据标准化器路径"""
        scaler_name = f"{prediction_type}"
        if device_id:
            scaler_name += f"_device_{device_id}"
        return LSTMForecastService.SCALER_DIR / f"{scaler_name}.pkl"
    
    def prepare_data(
        self,
        data: List[Any],  # 数据列表，每个元素应有voltage, current, power属性
        days: int = 60,
        target_column: str = "power",
        use_multivariate: bool = False
    ) -> Tuple[np.ndarray, np.ndarray, Any]:
        """
        准备训练数据
        
        Args:
            data: 历史数据列表（从数据库查询的结果）
            days: 历史数据天数（用于日志）
            target_column: 目标列（power/voltage/current）
            use_multivariate: 是否使用多变量（电压、电流、功率）
            
        Returns:
            (X, y, scaler_data) 训练数据对和标准化器
        """
        if len(data) < 100:
            raise ValueError(f"历史数据不足，至少需要100个数据点，当前只有{len(data)}个")
        
        # 提取数据
        if use_multivariate:
            # 多变量：使用电压、电流、功率作为特征
            features = np.column_stack([
                [d.voltage for d in data],
                [d.current for d in data],
                [d.flow_rate for d in data]
            ])
            
            # 多变量标准化
            feature_scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_features = feature_scaler.fit_transform(features)
            
            # 目标值（功率）
            if target_column == "power":
                target_values = features[:, 2]  # 功率列
            elif target_column == "voltage":
                target_values = features[:, 0]  # 电压列
            elif target_column == "current":
                target_values = features[:, 1]  # 电流列
            else:
                raise ValueError(f"不支持的目标列: {target_column}")
            
            # 目标值标准化（单独处理）
            target_scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_target = target_scaler.fit_transform(target_values.reshape(-1, 1)).flatten()
            
            # 保存scaler（包含特征和目标）
            scaler_data = {
                "feature_scaler": feature_scaler,
                "target_scaler": target_scaler,
                "multivariate": True
            }
        else:
            # 单变量：只使用目标列
            if target_column == "power":
                values = np.array([d.flow_rate for d in data])
            elif target_column == "voltage":
                values = np.array([d.voltage for d in data])
            elif target_column == "current":
                values = np.array([d.current for d in data])
            else:
                raise ValueError(f"不支持的目标列: {target_column}")
            
            # 数据标准化
            scaler = MinMaxScaler(feature_range=(0, 1))
            scaled_data = scaler.fit_transform(values.reshape(-1, 1)).flatten()
            scaled_features = scaled_data.reshape(-1, 1)
            scaled_target = scaled_data
            
            # 保存scaler
            scaler_data = {
                "feature_scaler": scaler,
                "target_scaler": scaler,
                "multivariate": False
            }
        
        # 创建时间序列数据集
        sequence_length = self.default_params["sequence_length"]
        X, y = [], []
        
        for i in range(len(scaled_target) - sequence_length):
            X.append(scaled_features[i:i + sequence_length])
            y.append(scaled_target[i + sequence_length])
        
        X = np.array(X)
        y = np.array(y)
        
        # 重塑为LSTM输入格式 [samples, timesteps, features]
        if len(X.shape) == 2:
            X = X.reshape((X.shape[0], X.shape[1], 1))
        
        return X, y, scaler_data
    
    def build_model(self, input_shape: Tuple[int, int], params: Optional[Dict] = None) -> keras.Model:
        """
        构建LSTM模型
        
        Args:
            input_shape: 输入形状 (timesteps, features)
            params: 超参数字典
            
        Returns:
            Keras模型
        """
        params = params or self.default_params
        
        model = Sequential()
        
        # 第一层LSTM
        model.add(LSTM(
            units=params["lstm_units"][0],
            return_sequences=True,
            input_shape=input_shape
        ))
        model.add(Dropout(params["dropout_rate"]))
        
        # 第二层LSTM（如果有）
        if len(params["lstm_units"]) > 1:
            model.add(LSTM(
                units=params["lstm_units"][1],
                return_sequences=len(params["lstm_units"]) > 2
            ))
            model.add(Dropout(params["dropout_rate"]))
        
        # 第三层LSTM（如果有）
        if len(params["lstm_units"]) > 2:
            model.add(LSTM(
                units=params["lstm_units"][2],
                return_sequences=False
            ))
            model.add(Dropout(params["dropout_rate"]))
        
        # 输出层
        model.add(Dense(1))
        
        # 编译模型
        model.compile(
            optimizer='adam',
            loss='mse',
            metrics=['mae', 'mape']
        )
        
        return model
    
    def train_model(
        self,
        data: List[Any],
        prediction_type: str,
        device_id: Optional[int] = None,
        days: int = 60,
        params: Optional[Dict] = None,
        retrain: bool = False,
        use_multivariate: bool = False,
        version: Optional[str] = None,
        logger: Optional[Any] = None
    ) -> Dict[str, Any]:
        """
        训练LSTM模型
        
        Args:
            data: 训练数据列表
            prediction_type: 预测类型（load/solar/wind）
            device_id: 设备ID
            days: 训练数据天数
            params: 超参数
            retrain: 是否重新训练（即使模型已存在）
            use_multivariate: 是否使用多变量
            version: 版本号
            logger: 日志记录器（可选）
            
        Returns:
            训练结果字典
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow未安装")
        
        params = params or self.default_params
        
        # 版本管理：如果有版本号，使用版本目录
        if version:
            model_path = self.VERSION_DIR / f"{prediction_type}_{device_id or 'system'}_v{version}.h5"
        else:
            model_path = self._get_model_path(prediction_type, device_id)
        
        # 检查模型是否已存在
        if model_path.exists() and not retrain:
            if logger:
                logger.info(f"模型已存在: {model_path}，跳过训练")
            return {
                "status": "skipped",
                "message": "模型已存在，使用 retrain=True 强制重新训练",
                "model_path": str(model_path)
            }
        
        if logger:
            logger.info(f"开始训练LSTM模型: type={prediction_type}, device_id={device_id}, multivariate={use_multivariate}")
        
        # 准备数据
        X, y, scaler_data = self.prepare_data(data, days, use_multivariate=use_multivariate)
        
        # 保存scaler
        scaler_path = self._get_scaler_path(prediction_type, device_id)
        with open(scaler_path, 'wb') as f:
            pickle.dump(scaler_data, f)
        
        # 构建模型（根据输入特征数量）
        input_features = X.shape[2]  # 特征数量（1或3）
        model = self.build_model((X.shape[1], input_features), params)
        
        # 设置回调
        callbacks = [
            EarlyStopping(
                monitor='val_loss',
                patience=params["patience"],
                restore_best_weights=True
            ),
            ModelCheckpoint(
                str(model_path),
                monitor='val_loss',
                save_best_only=True,
                verbose=1
            )
        ]
        
        # 训练模型
        history = model.fit(
            X, y,
            epochs=params["epochs"],
            batch_size=params["batch_size"],
            validation_split=params["validation_split"],
            callbacks=callbacks,
            verbose=1
        )
        
        # 评估模型
        train_loss = history.history['loss'][-1]
        val_loss = history.history['val_loss'][-1]
        train_mae = history.history.get('mae', [0])[-1]
        val_mae = history.history.get('val_mae', [0])[-1]
        
        # 保存模型元数据
        metadata = {
            "prediction_type": prediction_type,
            "device_id": device_id,
            "version": version or "latest",
            "multivariate": use_multivariate,
            "train_loss": float(train_loss),
            "val_loss": float(val_loss),
            "train_mae": float(train_mae),
            "val_mae": float(val_mae),
            "epochs_trained": len(history.history['loss']),
            "params": params,
            "trained_at": datetime.now().isoformat()
        }
        
        metadata_path = model_path.with_suffix('.json')
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
        
        if logger:
            logger.info(f"模型训练完成: train_loss={train_loss:.4f}, val_loss={val_loss:.4f}")
        
        return {
            "status": "success",
            "model_path": str(model_path),
            "metadata_path": str(metadata_path),
            "train_loss": float(train_loss),
            "val_loss": float(val_loss),
            "train_mae": float(train_mae),
            "val_mae": float(val_mae),
            "epochs_trained": len(history.history['loss']),
            "params": params,
            "multivariate": use_multivariate,
            "version": version
        }
    
    def predict(
        self,
        recent_data: List[Any],  # 最近的历史数据
        prediction_type: str,
        device_id: Optional[int] = None,
        hours: int = 24,
        interval_minutes: int = 60,
        sequence_length: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        使用LSTM模型进行预测
        
        Args:
            recent_data: 最近的历史数据列表
            prediction_type: 预测类型
            device_id: 设备ID
            hours: 预测时间范围（小时）
            interval_minutes: 预测间隔（分钟）
            sequence_length: 输入序列长度
            
        Returns:
            预测结果列表
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow未安装")
        
        model_path = self._get_model_path(prediction_type, device_id)
        scaler_path = self._get_scaler_path(prediction_type, device_id)
        
        # 检查模型是否存在
        if not model_path.exists():
            raise FileNotFoundError(
                f"模型不存在: {model_path}，请先训练模型"
            )
        
        if not scaler_path.exists():
            raise FileNotFoundError(
                f"数据标准化器不存在: {scaler_path}"
            )
        
        # 加载模型和scaler
        model = load_model(str(model_path))
        with open(scaler_path, 'rb') as f:
            scaler_data = pickle.load(f)
        
        # 提取scaler信息
        if isinstance(scaler_data, dict):
            multivariate = scaler_data.get("multivariate", False)
            feature_scaler = scaler_data["feature_scaler"]
            target_scaler = scaler_data["target_scaler"]
        else:
            # 兼容旧格式
            multivariate = False
            feature_scaler = scaler_data
            target_scaler = scaler_data
        
        sequence_length = sequence_length or self.default_params["sequence_length"]
        
        if len(recent_data) < sequence_length:
            raise ValueError(
                f"历史数据不足，需要至少{sequence_length}个数据点，当前只有{len(recent_data)}个"
            )
        
        # 提取数据并标准化
        if multivariate:
            # 多变量：电压、电流、功率
            features = np.column_stack([
                [d.voltage for d in recent_data[-sequence_length:]],
                [d.current for d in recent_data[-sequence_length:]],
                [d.flow_rate for d in recent_data[-sequence_length:]]
            ])
            scaled_features = feature_scaler.transform(features)
            current_sequence = scaled_features.copy()
        else:
            # 单变量：只使用功率
            powers = np.array([d.flow_rate for d in recent_data[-sequence_length:]])
            scaled_powers = feature_scaler.transform(powers.reshape(-1, 1)).flatten()
            current_sequence = scaled_powers.copy()
        
        # 生成预测
        predictions = []
        num_points = (hours * 60) // interval_minutes
        
        for i in range(num_points):
            # 预测下一个点
            if multivariate:
                X_batch = current_sequence[-sequence_length:].reshape(1, sequence_length, 3)
            else:
                X_batch = current_sequence[-sequence_length:].reshape(1, sequence_length, 1)
            
            pred_scaled = model.predict(X_batch, verbose=0)[0, 0]
            
            # 反标准化
            pred_value = target_scaler.inverse_transform([[pred_scaled]])[0, 0]
            predictions.append(max(0, pred_value))  # 确保非负
            
            # 更新序列（使用预测值）
            if multivariate:
                # 对于多变量，只更新功率，其他特征使用最后已知值
                last_features = current_sequence[-1].copy()
                last_features[2] = pred_scaled  # 更新功率
                current_sequence = np.vstack([current_sequence, last_features])
                current_sequence = current_sequence[-sequence_length:]
            else:
                current_sequence = np.append(current_sequence, pred_scaled)
                current_sequence = current_sequence[-sequence_length:]
        
        # 生成时间点
        now = datetime.now()
        results = []
        for i, pred_value in enumerate(predictions):
            forecast_time = now + timedelta(minutes=interval_minutes * (i + 1))
            results.append({
                "forecast_time": forecast_time,
                "predicted_value": round(float(pred_value), 2),
                "confidence": 0.85  # LSTM模型置信度
            })
        
        return results
    
    def evaluate_model(
        self,
        test_data: List[Any],  # 测试数据列表
        prediction_type: str,
        device_id: Optional[int] = None,
        test_days: int = 7
    ) -> Dict[str, Any]:
        """
        评估模型性能
        
        Args:
            test_data: 测试数据列表
            prediction_type: 预测类型
            device_id: 设备ID
            test_days: 测试数据天数（用于日志）
            
        Returns:
            评估结果
        """
        if not TF_AVAILABLE:
            raise ImportError("TensorFlow未安装")
        
        model_path = self._get_model_path(prediction_type, device_id)
        scaler_path = self._get_scaler_path(prediction_type, device_id)
        
        if not model_path.exists() or not scaler_path.exists():
            raise FileNotFoundError("模型或标准化器不存在，请先训练模型")
        
        # 加载模型和scaler
        model = load_model(str(model_path))
        with open(scaler_path, 'rb') as f:
            scaler_data = pickle.load(f)
        
        # 兼容旧格式
        if isinstance(scaler_data, dict):
            multivariate = scaler_data.get("multivariate", False)
            feature_scaler = scaler_data["feature_scaler"]
            target_scaler = scaler_data["target_scaler"]
        else:
            multivariate = False
            feature_scaler = scaler_data
            target_scaler = scaler_data
        
        # 准备测试数据
        sequence_length = self.default_params["sequence_length"]
        
        if len(test_data) < 100:
            raise ValueError("测试数据不足")
        
        if multivariate:
            # 多变量
            features = np.column_stack([
                [d.voltage for d in test_data],
                [d.current for d in test_data],
                [d.flow_rate for d in test_data]
            ])
            scaled_features = feature_scaler.transform(features)
            powers = features[:, 2]  # 功率列（实际值）
        else:
            # 单变量
            powers = np.array([d.flow_rate for d in test_data])
            scaled_features = feature_scaler.transform(powers.reshape(-1, 1))
        
        X_test, y_test = [], []
        for i in range(len(powers) - sequence_length):
            if multivariate:
                X_test.append(scaled_features[i:i + sequence_length])
            else:
                X_test.append(scaled_features[i:i + sequence_length].flatten())
            y_test.append(powers[i + sequence_length])  # 使用原始功率值
        
        if multivariate:
            X_test = np.array(X_test).reshape((len(X_test), sequence_length, 3))
        else:
            X_test = np.array(X_test).reshape((len(X_test), sequence_length, 1))
        y_test = np.array(y_test)
        
        # 预测
        y_pred_scaled = model.predict(X_test, verbose=0)
        y_pred = target_scaler.inverse_transform(y_pred_scaled).flatten()
        y_actual = y_test  # 实际值已经是原始值
        
        # 计算评估指标
        mae = np.mean(np.abs(y_pred - y_actual))
        mape = np.mean(np.abs((y_pred - y_actual) / (y_actual + 1e-8))) * 100
        rmse = np.sqrt(np.mean((y_pred - y_actual) ** 2))
        
        return {
            "mae": float(mae),
            "mape": float(mape),
            "rmse": float(rmse),
            "test_samples": len(y_test)
        }
