"""
数据生成服务
生成模拟的时序数据用于LSTM模型训练和测试
独立模块，不依赖后端主程序
"""
import random
import math
from datetime import datetime, timedelta
from typing import List, Optional, Tuple


class DataGenerator:
    """
    数据生成器
    
    生成模拟的设备遥测数据，包括：
    - 负荷数据（考虑日周期、周周期）
    - 光伏数据（考虑日周期、天气影响）
    - 风电数据（考虑季节性、随机波动）
    """
    
    @staticmethod
    def generate_timeseries_data(
        days: int = 60,
        interval_minutes: int = 60,
        data_type: str = "load",
        base_power: float = 100.0
    ) -> List[Tuple[datetime, float, float, float, float]]:
        """
        生成时间序列数据
        
        Args:
            days: 生成数据的天数
            interval_minutes: 数据间隔（分钟）
            data_type: 数据类型（load/solar/wind）
            base_power: 基础功率
            
        Returns:
            数据列表: [(timestamp, voltage, current, power, energy), ...]
        """
        start_time = datetime.now() - timedelta(days=days)
        
        # 计算时间点
        time_points = []
        current_time = start_time
        end_time = datetime.now()
        
        while current_time < end_time:
            time_points.append(current_time)
            current_time += timedelta(minutes=interval_minutes)
        
        # 根据数据类型生成数据
        if data_type == "load":
            data_points = DataGenerator._generate_load_data(time_points, base_power)
        elif data_type == "solar":
            data_points = DataGenerator._generate_solar_data(time_points, base_power)
        elif data_type == "wind":
            data_points = DataGenerator._generate_wind_data(time_points, base_power)
        else:
            raise ValueError(f"不支持的数据类型: {data_type}")
        
        # 计算能耗（累积值）
        result = []
        cumulative_energy = 0.0
        prev_timestamp = None
        
        for timestamp, voltage, current, power, _ in data_points:
            if prev_timestamp is not None:
                time_diff_hours = interval_minutes / 60.0
                energy_increment = power * time_diff_hours
                cumulative_energy += energy_increment
            else:
                cumulative_energy = power * (interval_minutes / 60.0) * 0.5
            
            result.append((
                timestamp,
                round(voltage, 2),
                round(current, 2),
                round(power, 2),
                round(cumulative_energy, 2)
            ))
            prev_timestamp = timestamp
        
        return result
    
    @staticmethod
    def _generate_load_data(
        time_points: List[datetime],
        base_power: float = 100.0
    ) -> List[Tuple[datetime, float, float, float, float]]:
        """生成负荷数据（考虑日周期和周周期）"""
        data = []
        
        for timestamp in time_points:
            hour = timestamp.hour
            weekday = timestamp.weekday()  # 0=周一, 6=周日
            
            # 日周期因子（白天高，夜间低）
            if 6 <= hour <= 22:
                time_factor = 1.0 + 0.5 * math.sin((hour - 6) * math.pi / 16)
            else:
                time_factor = 0.4 + 0.1 * random.random()
            
            # 周周期因子（工作日高，周末低）
            if weekday < 5:  # 工作日
                week_factor = 1.0
            else:  # 周末
                week_factor = 0.7
            
            # 随机波动
            random_factor = random.uniform(0.9, 1.1)
            
            # 计算功率
            power = base_power * time_factor * week_factor * random_factor
            
            # 估算电压和电流
            voltage = 380.0 + random.uniform(-5, 5)
            current = power * 1000 / voltage  # P = U * I / 1000
            
            data.append((timestamp, voltage, current, power, 0.0))
        
        return data
    
    @staticmethod
    def _generate_solar_data(
        time_points: List[datetime],
        base_power: float = 150.0
    ) -> List[Tuple[datetime, float, float, float, float]]:
        """生成光伏数据（考虑日周期和天气影响）"""
        data = []
        
        for timestamp in time_points:
            hour = timestamp.hour
            
            # 日周期因子（只有白天有输出）
            if 6 <= hour <= 18:
                # 使用正弦函数模拟日照变化
                time_factor = math.sin((hour - 6) * math.pi / 12)
            else:
                time_factor = 0.0
            
            # 模拟天气影响（50-100%的输出）
            weather_factor = random.uniform(0.5, 1.0)
            
            # 随机波动
            random_factor = random.uniform(0.95, 1.05)
            
            # 计算功率
            power = base_power * time_factor * weather_factor * random_factor
            
            # 估算电压和电流
            voltage = 380.0 + random.uniform(-5, 5)
            current = power * 1000 / voltage if power > 0 else 0
            
            data.append((timestamp, voltage, current, power, 0.0))
        
        return data
    
    @staticmethod
    def _generate_wind_data(
        time_points: List[datetime],
        base_power: float = 120.0
    ) -> List[Tuple[datetime, float, float, float, float]]:
        """生成风电数据（考虑季节性和随机波动）"""
        data = []
        
        for timestamp in time_points:
            month = timestamp.month
            
            # 季节性因子（冬季风力较大）
            if month in [12, 1, 2]:  # 冬季
                season_factor = 1.2
            elif month in [6, 7, 8]:  # 夏季
                season_factor = 0.8
            else:
                season_factor = 1.0
            
            # 较大的随机波动（风速不稳定）
            random_factor = random.uniform(0.7, 1.3)
            
            # 计算功率
            power = base_power * season_factor * random_factor
            
            # 估算电压和电流
            voltage = 380.0 + random.uniform(-5, 5)
            current = power * 1000 / voltage
            
            data.append((timestamp, voltage, current, power, 0.0))
        
        return data
