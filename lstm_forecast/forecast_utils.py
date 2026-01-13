"""
预测工具函数
提供简单的预测算法（移动平均、线性回归等）
"""
from typing import List, Dict, Any
from datetime import datetime, timedelta
import statistics


class ForecastUtils:
    """预测工具类，提供简单预测算法"""
    
    @staticmethod
    def moving_average_forecast(
        historical_data: List[float],
        hours: int = 24,
        interval_minutes: int = 60,
        window_size: int = 24
    ) -> List[Dict[str, Any]]:
        """
        移动平均预测
        
        Args:
            historical_data: 历史数据
            hours: 预测小时数
            interval_minutes: 预测间隔（分钟）
            window_size: 移动窗口大小
            
        Returns:
            预测结果列表
        """
        if len(historical_data) < window_size:
            window_size = len(historical_data)
        
        # 计算移动平均
        avg_value = statistics.mean(historical_data[-window_size:])
        
        # 生成预测
        now = datetime.now()
        num_points = (hours * 60) // interval_minutes
        predictions = []
        
        for i in range(num_points):
            forecast_time = now + timedelta(minutes=interval_minutes * (i + 1))
            predictions.append({
                "forecast_time": forecast_time,
                "predicted_value": round(avg_value, 2),
                "confidence": 0.7
            })
        
        return predictions
    
    @staticmethod
    def linear_regression_forecast(
        historical_data: List[float],
        hours: int = 24,
        interval_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        简单线性回归预测
        
        Args:
            historical_data: 历史数据
            hours: 预测小时数
            interval_minutes: 预测间隔（分钟）
            
        Returns:
            预测结果列表
        """
        n = len(historical_data)
        if n < 2:
            return ForecastUtils.moving_average_forecast(
                historical_data, hours, interval_minutes
            )
        
        # 计算线性回归参数
        x = list(range(n))
        y = historical_data
        
        x_mean = statistics.mean(x)
        y_mean = statistics.mean(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(n))
        denominator = sum((x[i] - x_mean) ** 2 for i in range(n))
        
        if denominator == 0:
            return ForecastUtils.moving_average_forecast(
                historical_data, hours, interval_minutes
            )
        
        slope = numerator / denominator
        intercept = y_mean - slope * x_mean
        
        # 生成预测
        now = datetime.now()
        num_points = (hours * 60) // interval_minutes
        predictions = []
        
        for i in range(num_points):
            x_future = n + i
            predicted_value = slope * x_future + intercept
            predicted_value = max(0, predicted_value)  # 确保非负
            
            forecast_time = now + timedelta(minutes=interval_minutes * (i + 1))
            predictions.append({
                "forecast_time": forecast_time,
                "predicted_value": round(predicted_value, 2),
                "confidence": 0.75
            })
        
        return predictions
    
    @staticmethod
    def calculate_confidence(data: List[float]) -> float:
        """
        计算预测置信度
        
        基于数据的稳定性计算置信度
        """
        if len(data) < 2:
            return 0.5
        
        try:
            mean_val = statistics.mean(data)
            if mean_val == 0:
                return 0.5
            
            stdev = statistics.stdev(data)
            cv = stdev / mean_val  # 变异系数
            
            # 变异系数越小，置信度越高
            confidence = max(0.5, min(0.95, 1.0 - cv))
            return round(confidence, 2)
        except:
            return 0.5
