"""
应用配置（Pydantic Settings）

统一管理数据库、Redis、MQTT、JWT、CORS、日志、服务端口等配置。
"""
from typing import List, Optional

# Pydantic v2 推荐：BaseSettings 在 pydantic-settings；如果环境未安装，则回退到 pydantic.v1
try:
    from pydantic_settings import BaseSettings  # type: ignore
    from pydantic import Field, validator  # type: ignore
except Exception:
    try:
        # Pydantic v2 兼容层（无需安装 pydantic-settings）
        from pydantic.v1 import BaseSettings, Field, validator  # type: ignore
    except Exception:
        # Pydantic v1
        from pydantic import BaseSettings, Field, validator  # type: ignore

class Settings(BaseSettings):
    """
    应用配置类
    所有配置项都可以通过环境变量或 .env 文件设置
    """
    
    # ==================== 应用基础配置 ====================
    app_name: str = Field(
        default="煤矿综合能源管理系统",
        env="APP_NAME",
        description="应用名称"
    )
    app_version: str = Field(
        default="2.0.0",
        env="APP_VERSION",
        description="应用版本"
    )
    debug: bool = Field(
        default=False,
        env="DEBUG",
        description="调试模式（开发环境设为True）"
    )
    
    # ==================== 数据库配置 ====================
    database_url: str = Field(
        ...,
        env="DATABASE_URL",
        description="数据库连接URL"
    )
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """验证数据库URL格式：只允许PostgreSQL连接地址"""
        if not v.startswith(("postgresql://", "postgresql+psycopg2://")):
            raise ValueError("DATABASE_URL 必须以 postgresql:// 或 postgresql+psycopg2:// 开头")
        return v
    # ==================== Redis配置 ====================
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        env="REDIS_URL",
        description="Redis连接URL"
    )
    
    redis_password: Optional[str] = Field(
        default=None,
        env="REDIS_PASSWORD",
        description="Redis密码（如果需要）"
    )
    
    # ==================== MQTT配置 ====================
    mqtt_broker: str = Field(
        default="127.0.0.1",
        env="MQTT_BROKER",
        description="MQTT Broker地址"
    )
    
    mqtt_port: int = Field(
        default=1883,
        env="MQTT_PORT",
        description="MQTT端口"
    )
    
    mqtt_username: Optional[str] = Field(
        default=None,
        env="MQTT_USERNAME",
        description="MQTT用户名（可选）"
    )
    
    mqtt_password: Optional[str] = Field(
        default=None,
        env="MQTT_PASSWORD",
        description="MQTT密码（可选）"
    )
    
    mqtt_topic: str = Field(
        default="mine/telemetry",
        env="MQTT_TOPIC",
        description="MQTT订阅主题"
    )
    
    mqtt_topic_wildcard: str = Field(
        default="mine/device/+/telemetry",
        env="MQTT_TOPIC_WILDCARD",
        description="MQTT通配符主题"
    )
    
    # ==================== JWT认证配置 ====================
    secret_key: str = Field(
        default="mine-energy-system-secret-key-change-me",
        env="SECRET_KEY",
        description="JWT密钥（生产环境必须修改！）"
    )
    
    algorithm: str = Field(
        default="HS256",
        env="ALGORITHM",
        description="JWT算法"
    )
    
    access_token_expire_minutes: int = Field(
        default=300,
        env="ACCESS_TOKEN_EXPIRE_MINUTES",
        description="访问令牌过期时间（分钟）"
    )
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        if len(v) < 32:
            raise ValueError("SECRET_KEY 长度至少32个字符，请使用强密钥！")
        if v == "mine-energy-system-secret-key-change-me":
            import warnings
            warnings.warn(
                "⚠️ 警告：你正在使用默认的SECRET_KEY，生产环境请务必修改！",
                UserWarning
            )
        return v
    
    # ==================== CORS配置 ====================
    cors_origins: List[str] = Field(
        default=["http://localhost:5173", "http://127.0.0.1:5173"],
        env="CORS_ORIGINS",
        description="允许的CORS来源（JSON数组格式或逗号分隔）"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS来源配置"""
        if isinstance(v, str):
            # 尝试解析JSON数组
            import json
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # 如果不是JSON，按逗号分隔
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v
    
    # ==================== 电价配置 ====================
    peak_price: float = Field(
        default=1.25,
        env="PEAK_PRICE",
        description="高峰电价"
    )
    
    flat_price: float = Field(
        default=0.80,
        env="FLAT_PRICE",
        description="平电电价"
    )
    
    valley_price: float = Field(
        default=0.40,
        env="VALLEY_PRICE",
        description="低谷电价"
    )

    # ==================== 故障诊断配置 ====================
    fdd_voltage_fluctuation_limit: float = Field(
        default=0.10,
        env="FDD_VOLTAGE_FLUCTUATION_LIMIT",
        description="电压波动阈值（%）"
    )
    fdd_overload_ratio: float = Field(
        default=0.90,
        env="FDD_OVERLOAD_RATIO",
        description="负载率阈值"
    )
    fdd_rated_power: float = Field(
        default=1000.0,
        env="FDD_RATED_POWER",
        description="设备额定功率（kW），用于计算负载率"
    )
    fdd_alarm_threshold: int = Field(
        default=10,
        env="FDD_ALARM_THRESHOLD",
        description="报警次数阈值，超过此值将扣分"
    )
    fdd_frequent_start_count: int = Field(
        default=5,
        env="FDD_FREQUENT_START_COUNT",
        description="频繁启动次数阈值"
    )

    # ==================== 预测配置 ====================
    forecast_horizon_hours: int = Field(
        default=24,
        env="FORECAST_HORIZON_HOURS",
        description="预测时间范围（小时），默认24小时"
    )
    forecast_interval_minutes: int = Field(
        default=60,
        env="FORECAST_INTERVAL_MINUTES",
        description="预测时间间隔（分钟），默认60分钟"
    )
    forecast_history_days: int = Field(
        default=30,
        env="FORECAST_HISTORY_DAYS",
        description="用于预测的历史数据天数，默认30天"
    )
    forecast_algorithm: str = Field(
        default="moving_average",
        env="FORECAST_ALGORITHM",
        description="默认预测算法：moving_average, linear_regression, arima"
    )
    forecast_auto_update: bool = Field(
        default=True,
        env="FORECAST_AUTO_UPDATE",
        description="是否自动更新预测（定时任务）"
    )
    forecast_lstm_enabled: bool = Field(
        default=True,
        env="FORECAST_LSTM_ENABLED",
        description="是否启用LSTM预测（需要安装TensorFlow）"
    )
    forecast_lstm_sequence_length: int = Field(
        default=24,
        env="FORECAST_LSTM_SEQUENCE_LENGTH",
        description="LSTM输入序列长度（小时）"
    )
    forecast_lstm_units: str = Field(
        default="64,32",
        env="FORECAST_LSTM_UNITS",
        description="LSTM层单元数（逗号分隔，如：64,32）"
    )
    forecast_lstm_epochs: int = Field(
        default=50,
        env="FORECAST_LSTM_EPOCHS",
        description="LSTM训练轮数"
    )

    # ==================== 日志配置 ====================
    log_level: str = Field(
        default="INFO",
        env="LOG_LEVEL",
        description="日志级别（DEBUG, INFO, WARNING, ERROR, CRITICAL）"
    )
    
    log_dir: str = Field(
        default="logs",
        env="LOG_DIR",
        description="日志文件目录"
    )
    
    log_retention_days: int = Field(
        default=7,
        env="LOG_RETENTION_DAYS",
        description="日志保留天数"
    )
    
    # ==================== 数据清理配置 ====================
    data_retention_days: int = Field(
        default=90,
        env="DATA_RETENTION_DAYS",
        description="时序数据保留天数（DeviceData、EnergyData等）"
    )
    
    alarm_retention_days: int = Field(
        default=180,
        env="ALARM_RETENTION_DAYS",
        description="报警记录保留天数"
    )
    
    statistics_retention_days: int = Field(
        default=365,
        env="STATISTICS_RETENTION_DAYS",
        description="统计数据保留天数（EnergyStatistics等）"
    )
    
    enable_auto_cleanup: bool = Field(
        default=True,
        env="ENABLE_AUTO_CLEANUP",
        description="是否启用自动数据清理"
    )
    
    # ==================== 服务器配置 ====================
    host: str = Field(
        default="0.0.0.0",
        env="HOST",
        description="服务器监听地址"
    )
    
    port: int = Field(
        default=8088,
        env="PORT",
        description="服务器端口"
    )
    
    workers: int = Field(
        default=1,
        env="WORKERS",
        description="工作进程数（生产环境建议设为CPU核心数）"
    )
    
    reload: bool = Field(
        default=False,
        env="RELOAD",
        description="是否开启热重载（仅开发环境）"
    )
    
    # ==================== 配置文件路径 ====================
    config_dir: str = Field(
        default="config",
        env="CONFIG_DIR",
        description="配置文件目录"
    )
    
    settings_json_path: Optional[str] = Field(
        default=None,
        env="SETTINGS_JSON_PATH",
        description="settings.json文件路径（可选，用于报警阈值配置）"
    )
    
    class Config:
        """Pydantic配置"""
        env_file = ".env"  # 从 .env 文件读取
        env_file_encoding = "utf-8"  # 文件编码
        case_sensitive = False  # 不区分大小写
        # 允许使用环境变量前缀（可选）
        # env_prefix = "MINE_EMS_"


# 创建全局配置实例
# 这个实例会在首次导入时自动从环境变量和 .env 文件加载配置
settings = Settings()

# 导出常用配置的快捷方式（保持向后兼容）
DATABASE_URL = settings.database_url
REDIS_URL = settings.redis_url
MQTT_BROKER = settings.mqtt_broker
MQTT_PORT = settings.mqtt_port
SECRET_KEY = settings.secret_key
ALGORITHM = settings.algorithm
PEAK_PRICE = settings.peak_price
FLAT_PRICE = settings.flat_price
VALLEY_PRICE = settings.valley_price
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes

