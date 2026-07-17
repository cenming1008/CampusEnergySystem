"""
应用配置（Pydantic Settings）

统一管理数据库、Redis、MQTT、JWT、CORS、日志、服务端口等配置。
"""
import json
import warnings
from typing import List, Optional

# Pydantic v2 推荐：BaseSettings 在 pydantic-settings；如果环境未安装，则回退到 pydantic.v1
try:
    from pydantic import Field, validator  # type: ignore
    from pydantic_settings import BaseSettings  # type: ignore
except Exception:
    try:
        # Pydantic v2 兼容层（无需安装 pydantic-settings）
        from pydantic.v1 import BaseSettings, Field, validator  # type: ignore
    except Exception:
        # Pydantic v1
        from pydantic import BaseSettings, Field, validator  # type: ignore


DEFAULT_SECRET_KEY = "campus-energy-system-secret-key-change-me"
POSTGRES_SCHEMES = ("postgresql://", "postgresql+psycopg2://")


def validate_database_url_value(value: str) -> str:
    """验证数据库 URL 格式。"""
    if not value.startswith(POSTGRES_SCHEMES):
        raise ValueError("DATABASE_URL 必须以 postgresql:// 或 postgresql+psycopg2:// 开头")
    return value

def validate_secret_key_value(value: str) -> str:
    """验证密钥强度。"""
    if len(value) < 32:
        raise ValueError("SECRET_KEY 长度至少32个字符，请使用强密钥！")
    if value == DEFAULT_SECRET_KEY:
        warnings.warn(
            "⚠️ 警告：你正在使用默认的SECRET_KEY，生产环境请务必修改！",
            UserWarning,
        )
    return value


def parse_cors_origins_value(value):
    """解析 CORS 来源配置。"""
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return [origin.strip() for origin in value.split(",") if origin.strip()]
    return value


def parse_list_setting(value):
    """解析 JSON 数组或逗号分隔列表配置。"""
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            pass
        return [item.strip() for item in value.split(",") if item.strip()]
    return value

class Settings(BaseSettings):
    """
    应用配置类
    所有配置项都可以通过环境变量或 .env 文件设置
    """
    
    # ==================== 应用基础配置 ====================
    app_name: str = Field(
        default="园区综合能源管理系统",
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

    app_env: str = Field(
        default="development",
        env="APP_ENV",
        description="运行环境：development/staging/production"
    )

    strict_startup_checks: bool = Field(
        default=True,
        env="STRICT_STARTUP_CHECKS",
        description="是否启用严格启动检查"
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
        return validate_database_url_value(v)
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

    scheduler_enabled: bool = Field(
        default=True,
        env="SCHEDULER_ENABLED",
        description="是否启用进程内 scheduler"
    )

    scheduler_mode: str = Field(
        default="auto",
        env="SCHEDULER_MODE",
        description="scheduler 模式：auto/local/redis_owner"
    )

    scheduler_lease_key: str = Field(
        default="campus:scheduler:owner",
        env="SCHEDULER_LEASE_KEY",
        description="scheduler owner 竞争使用的 Redis lease key"
    )

    scheduler_lease_ttl_seconds: int = Field(
        default=30,
        env="SCHEDULER_LEASE_TTL_SECONDS",
        description="scheduler owner lease TTL（秒）"
    )

    scheduler_lease_renew_interval_seconds: int = Field(
        default=10,
        env="SCHEDULER_LEASE_RENEW_INTERVAL_SECONDS",
        description="scheduler owner lease 续租间隔（秒）"
    )
    
    # ==================== MQTT配置 ====================
    mqtt_broker: str = Field(
        default="127.0.0.1",
        env="MQTT_BROKER",
        description="MQTT Broker地址"
    )
    
    mqtt_port: int = Field(
        default=8883,
        env="MQTT_PORT",
        description="MQTT端口（默认 8883 = TLS）"
    )

    mqtt_username: Optional[str] = Field(
        default=None,
        env="MQTT_USERNAME",
        description="MQTT用户名（ingest worker 使用，亦作为旧字段兼容）"
    )

    mqtt_password: Optional[str] = Field(
        default=None,
        env="MQTT_PASSWORD",
        description="MQTT密码（ingest worker 使用，亦作为旧字段兼容）"
    )

    # ---------- TLS ----------
    mqtt_tls_enabled: bool = Field(
        default=True,
        env="MQTT_TLS_ENABLED",
        description="是否对 MQTT 客户端启用 TLS"
    )

    mqtt_tls_ca_path: Optional[str] = Field(
        default=None,
        env="MQTT_TLS_CA_PATH",
        description="自签 CA 证书路径，启用 TLS 时必填"
    )

    mqtt_tls_certfile: Optional[str] = Field(
        default=None,
        env="MQTT_TLS_CERTFILE",
        description="客户端证书路径（仅 mTLS 时需要）"
    )

    mqtt_tls_keyfile: Optional[str] = Field(
        default=None,
        env="MQTT_TLS_KEYFILE",
        description="客户端私钥路径（仅 mTLS 时需要）"
    )

    mqtt_tls_insecure: bool = Field(
        default=False,
        env="MQTT_TLS_INSECURE",
        description="是否跳过服务端证书 hostname 校验（仅 dev 调试用）"
    )

    # ---------- 分角色凭据 ----------
    mqtt_control_username: Optional[str] = Field(
        default=None,
        env="MQTT_CONTROL_USERNAME",
        description="控制下发使用的 MQTT 账号（缺省回退到 mqtt_username）"
    )

    mqtt_control_password: Optional[str] = Field(
        default=None,
        env="MQTT_CONTROL_PASSWORD",
        description="控制下发使用的 MQTT 密码（缺省回退到 mqtt_password）"
    )
    
    mqtt_topic: str = Field(
        default="campus/telemetry",
        env="MQTT_TOPIC",
        description="MQTT订阅主题"
    )
    
    mqtt_topic_wildcard: str = Field(
        default="campus/device/+/telemetry",
        env="MQTT_TOPIC_WILDCARD",
        description="MQTT通配符主题"
    )

    mqtt_control_topic_prefix: str = Field(
        default="campus/control/",
        env="MQTT_CONTROL_TOPIC_PREFIX",
        description="MQTT控制指令主题前缀"
    )

    storage_ems_enabled: bool = Field(
        default=False,
        env="STORAGE_EMS_ENABLED",
        description="是否启用储能 EMS 自动控制能力"
    )

    storage_simulation_enabled: bool = Field(
        default=False,
        env="STORAGE_SIMULATION_ENABLED",
        description="是否启用应用内储能仿真接口与任务"
    )

    storage_simulation_topic_prefix: str = Field(
        default="campus/simulation/",
        env="STORAGE_SIMULATION_TOPIC_PREFIX",
        description="储能模拟器专属控制主题前缀"
    )

    storage_daily_dispatch_time: str = Field(
        default="00:05",
        env="STORAGE_DAILY_DISPATCH_TIME",
        description="储能日前计划每日生成时间（HH:MM）"
    )

    compensation_control_receipt_timeout_seconds: int = Field(
        default=120,
        env="COMPENSATION_CONTROL_RECEIPT_TIMEOUT_SECONDS",
        description="补偿控制指令等待设备回执的超时时间（秒）"
    )

    mqtt_consumer_enabled: bool = Field(
        default=False,
        env="MQTT_CONSUMER_ENABLED",
        description="当前进程是否启用 MQTT 订阅消费"
    )

    mqtt_realtime_bridge_channel: str = Field(
        default="campus-energy-system:mqtt:realtime-events",
        env="MQTT_REALTIME_BRIDGE_CHANNEL",
        description="worker -> API 的 Redis 实时事件桥接频道"
    )

    mqtt_worker_health_key: str = Field(
        default="campus-energy-system:mqtt:worker-health",
        env="MQTT_WORKER_HEALTH_KEY",
        description="MQTT worker 健康状态在 Redis 中的键"
    )

    mqtt_worker_health_ttl_seconds: int = Field(
        default=30,
        env="MQTT_WORKER_HEALTH_TTL_SECONDS",
        description="MQTT worker 健康状态 TTL（秒）"
    )

    mqtt_worker_health_heartbeat_seconds: int = Field(
        default=10,
        env="MQTT_WORKER_HEALTH_HEARTBEAT_SECONDS",
        description="MQTT worker 健康心跳刷新间隔（秒）"
    )
    
    mqtt_auto_create_device: bool = Field(
        default=True,
        env="MQTT_AUTO_CREATE_DEVICE",
        description="收到未知 device_code 时是否自动创建设备（即插即用）"
    )

    mqtt_max_future_seconds: int = Field(
        default=300,
        env="MQTT_MAX_FUTURE_SECONDS",
        description="允许设备时间戳领先当前时间的最大秒数，超过则丢弃"
    )

    mqtt_stale_data_days: int = Field(
        default=90,
        env="MQTT_STALE_DATA_DAYS",
        description="允许接收的历史数据最大天数，超过则丢弃"
    )

    mqtt_online_timeout_seconds: int = Field(
        default=300,
        env="MQTT_ONLINE_TIMEOUT_SECONDS",
        description="设备成功上报后判定在线的持续秒数"
    )

    mqtt_retry_max_attempts: int = Field(
        default=3,
        env="MQTT_RETRY_MAX_ATTEMPTS",
        description="MQTT 消息失败后的最大自动/运维重试次数"
    )

    mqtt_retry_backoff_seconds: int = Field(
        default=60,
        env="MQTT_RETRY_BACKOFF_SECONDS",
        description="MQTT 消息失败后的基础重试退避秒数"
    )

    auth_rate_limit_count: int = Field(
        default=10,
        env="AUTH_RATE_LIMIT_COUNT",
        description="认证接口窗口内最大请求数"
    )

    auth_rate_limit_window_seconds: int = Field(
        default=60,
        env="AUTH_RATE_LIMIT_WINDOW_SECONDS",
        description="认证接口限流窗口（秒）"
    )

    device_report_rate_limit_count: int = Field(
        default=120,
        env="DEVICE_REPORT_RATE_LIMIT_COUNT",
        description="设备数据上报接口窗口内最大请求数"
    )

    device_report_rate_limit_window_seconds: int = Field(
        default=60,
        env="DEVICE_REPORT_RATE_LIMIT_WINDOW_SECONDS",
        description="设备数据上报接口限流窗口（秒）"
    )

    device_control_rate_limit_count: int = Field(
        default=20,
        env="DEVICE_CONTROL_RATE_LIMIT_COUNT",
        description="设备控制接口窗口内最大请求数"
    )

    device_control_rate_limit_window_seconds: int = Field(
        default=60,
        env="DEVICE_CONTROL_RATE_LIMIT_WINDOW_SECONDS",
        description="设备控制接口限流窗口（秒）"
    )

    api_global_rate_limit_count: int = Field(
        default=300,
        env="API_GLOBAL_RATE_LIMIT_COUNT",
        description="全局 API 限流窗口内最大请求数"
    )

    api_global_rate_limit_window_seconds: int = Field(
        default=60,
        env="API_GLOBAL_RATE_LIMIT_WINDOW_SECONDS",
        description="全局 API 限流窗口（秒）"
    )

    report_export_rate_limit_count: int = Field(
        default=20,
        env="REPORT_EXPORT_RATE_LIMIT_COUNT",
        description="报表导出接口窗口内最大请求数"
    )

    report_export_rate_limit_window_seconds: int = Field(
        default=300,
        env="REPORT_EXPORT_RATE_LIMIT_WINDOW_SECONDS",
        description="报表导出接口限流窗口（秒）"
    )

    rate_limit_backend: str = Field(
        default="auto",
        env="RATE_LIMIT_BACKEND",
        description="限流后端：auto/memory/redis"
    )

    rate_limit_key_prefix: str = Field(
        default="campus-energy-system:rate-limit",
        env="RATE_LIMIT_KEY_PREFIX",
        description="共享限流键前缀"
    )

    rate_limit_fail_open: bool = Field(
        default=True,
        env="RATE_LIMIT_FAIL_OPEN",
        description="共享限流异常时是否放行请求"
    )

    rate_limit_fallback_to_memory: bool = Field(
        default=True,
        env="RATE_LIMIT_FALLBACK_TO_MEMORY",
        description="共享限流异常时是否回退到进程内限流"
    )

    websocket_auth_mode: str = Field(
        default="query_token",
        env="WEBSOCKET_AUTH_MODE",
        description="WebSocket 鉴权方式：query_token/disabled"
    )

    monitoring_access_mode: str = Field(
        default="internal_or_jwt",
        env="MONITORING_ACCESS_MODE",
        description="监控端点访问控制：public/internal/jwt/internal_or_jwt"
    )

    monitoring_access_roles: List[str] = Field(
        default=["admin", "maintainer"],
        env="MONITORING_ACCESS_ROLES",
        description="允许访问监控端点的角色列表"
    )
    
    # ==================== JWT认证配置 ====================
    secret_key: str = Field(
        default=DEFAULT_SECRET_KEY,
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

    refresh_token_expire_minutes: int = Field(
        default=60 * 24 * 7,
        env="REFRESH_TOKEN_EXPIRE_MINUTES",
        description="刷新令牌过期时间（分钟）"
    )

    auth_max_failed_attempts: int = Field(
        default=5,
        env="AUTH_MAX_FAILED_ATTEMPTS",
        description="连续登录失败锁定阈值"
    )

    auth_lock_minutes: int = Field(
        default=15,
        env="AUTH_LOCK_MINUTES",
        description="账户锁定时长（分钟）"
    )
    
    @validator("secret_key")
    def validate_secret_key(cls, v):
        """验证密钥强度"""
        return validate_secret_key_value(v)
    
    # ==================== CORS配置 ====================
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ],
        env="CORS_ORIGINS",
        description="允许的CORS来源（JSON数组格式或逗号分隔）"
    )

    db_pool_size: int = Field(
        default=20,
        env="DB_POOL_SIZE",
        description="数据库连接池基础连接数"
    )

    db_max_overflow: int = Field(
        default=40,
        env="DB_MAX_OVERFLOW",
        description="数据库连接池溢出连接数"
    )

    db_pool_timeout: int = Field(
        default=30,
        env="DB_POOL_TIMEOUT",
        description="数据库连接池获取连接超时时间（秒）"
    )

    db_pool_recycle: int = Field(
        default=1800,
        env="DB_POOL_RECYCLE",
        description="数据库连接回收时间（秒）"
    )

    db_auto_create_tables: bool = Field(
        default=False,
        env="DB_AUTO_CREATE_TABLES",
        description="兼容配置；True 会被拒绝，数据库 schema 由 Alembic 管理"
    )

    db_runtime_schema_sync: bool = Field(
        default=False,
        env="DB_RUNTIME_SCHEMA_SYNC",
        description="兼容配置；True 会被拒绝，数据库 schema 由 Alembic 管理"
    )
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """解析CORS来源配置"""
        return parse_cors_origins_value(v)

    trusted_hosts: List[str] = Field(
        default=["localhost", "127.0.0.1", "0.0.0.0"],
        env="TRUSTED_HOSTS",
        description="允许访问的 Host 列表（JSON 数组或逗号分隔），生产环境应设为实际域名/IP"
    )

    force_https: bool = Field(
        default=False,
        env="FORCE_HTTPS",
        description="是否在应用层强制 HTTPS 重定向"
    )

    security_hsts_seconds: int = Field(
        default=31536000,
        env="SECURITY_HSTS_SECONDS",
        description="HSTS 生效秒数"
    )

    security_content_security_policy: str = Field(
        default="default-src 'self'; img-src 'self' data:; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'; connect-src 'self' ws: wss:; font-src 'self' data:; frame-ancestors 'none'; base-uri 'self'; form-action 'self'",
        env="SECURITY_CONTENT_SECURITY_POLICY",
        description="CSP 头"
    )

    security_referrer_policy: str = Field(
        default="strict-origin-when-cross-origin",
        env="SECURITY_REFERRER_POLICY",
        description="Referrer-Policy 头"
    )

    security_permissions_policy: str = Field(
        default="geolocation=(), microphone=(), camera=(), payment=()",
        env="SECURITY_PERMISSIONS_POLICY",
        description="Permissions-Policy 头"
    )

    alerting_enabled: bool = Field(
        default=False,
        env="ALERTING_ENABLED",
        description="是否启用运行时告警通知"
    )

    alerting_project_name: str = Field(
        default="CampusEnergySystem",
        env="ALERTING_PROJECT_NAME",
        description="告警通知中的项目名"
    )

    alerting_webhook_url: Optional[str] = Field(
        default=None,
        env="ALERTING_WEBHOOK_URL",
        description="告警 Webhook 地址"
    )

    alerting_email_enabled: bool = Field(
        default=False,
        env="ALERTING_EMAIL_ENABLED",
        description="是否启用 SMTP 邮件通知"
    )

    alerting_smtp_host: Optional[str] = Field(
        default=None,
        env="ALERTING_SMTP_HOST",
        description="SMTP 主机"
    )

    alerting_smtp_port: int = Field(
        default=587,
        env="ALERTING_SMTP_PORT",
        description="SMTP 端口"
    )

    alerting_smtp_username: Optional[str] = Field(
        default=None,
        env="ALERTING_SMTP_USERNAME",
        description="SMTP 用户名"
    )

    alerting_smtp_password: Optional[str] = Field(
        default=None,
        env="ALERTING_SMTP_PASSWORD",
        description="SMTP 密码"
    )

    alerting_email_from: Optional[str] = Field(
        default=None,
        env="ALERTING_EMAIL_FROM",
        description="告警发件人"
    )

    alerting_email_to: List[str] = Field(
        default=[],
        env="ALERTING_EMAIL_TO",
        description="告警收件人列表"
    )

    alerting_cooldown_seconds: int = Field(
        default=300,
        env="ALERTING_COOLDOWN_SECONDS",
        description="同类告警通知冷却时间（秒）"
    )

    @validator("trusted_hosts", pre=True)
    def parse_trusted_hosts(cls, v):
        return parse_list_setting(v)

    @validator("alerting_email_to", pre=True)
    def parse_alerting_email_to(cls, v):
        return parse_list_setting(v)

    @validator("monitoring_access_roles", pre=True)
    def parse_monitoring_access_roles(cls, v):
        return parse_list_setting(v)

    @validator("app_env")
    def validate_app_env(cls, v):
        normalized = v.lower().strip()
        allowed = {"development", "staging", "production"}
        if normalized not in allowed:
            raise ValueError(f"APP_ENV 必须是 {sorted(allowed)} 之一")
        return normalized

    @validator("rate_limit_backend")
    def validate_rate_limit_backend(cls, v):
        normalized = str(v).lower().strip()
        allowed = {"auto", "memory", "redis"}
        if normalized not in allowed:
            raise ValueError(f"RATE_LIMIT_BACKEND 必须是 {sorted(allowed)} 之一")
        return normalized

    @validator("scheduler_mode")
    def validate_scheduler_mode(cls, v):
        normalized = str(v).lower().strip()
        allowed = {"auto", "local", "redis_owner"}
        if normalized not in allowed:
            raise ValueError(f"SCHEDULER_MODE 必须是 {sorted(allowed)} 之一")
        return normalized

    @validator("websocket_auth_mode")
    def validate_websocket_auth_mode(cls, v):
        normalized = str(v).lower().strip()
        allowed = {"query_token", "disabled"}
        if normalized not in allowed:
            raise ValueError(f"WEBSOCKET_AUTH_MODE 必须是 {sorted(allowed)} 之一")
        return normalized

    @validator("monitoring_access_mode")
    def validate_monitoring_access_mode(cls, v):
        normalized = str(v).lower().strip()
        allowed = {"public", "internal", "jwt", "internal_or_jwt"}
        if normalized not in allowed:
            raise ValueError(f"MONITORING_ACCESS_MODE 必须是 {sorted(allowed)} 之一")
        return normalized
    
    # ==================== 电价配置 ====================
    peak_price: float = Field(
        default=1.25,
        env="PEAK_PRICE",
        description="高峰电价（元/kWh）"
    )
    flat_price: float = Field(
        default=0.80,
        env="FLAT_PRICE",
        description="平电电价（元/kWh）"
    )
    valley_price: float = Field(
        default=0.40,
        env="VALLEY_PRICE",
        description="低谷电价（元/kWh）"
    )
    # 峰谷平时段（小时，左闭右开）。多个区间用逗号分隔，每个区间为 开始-结束，如 "8-12,18-23"
    electricity_peak_hours: str = Field(
        default="8-12,18-23",
        env="ELECTRICITY_PEAK_HOURS",
        description="峰时段（小时），如 8-12,18-23 表示 8:00-12:00 与 18:00-23:00"
    )
    electricity_flat_hours: str = Field(
        default="7-8,12-18",
        env="ELECTRICITY_FLAT_HOURS",
        description="平时段（小时），如 7-8,12-18 表示 7:00-8:00 与 12:00-18:00；其余为谷时段"
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
    
    mqtt_ingestion_retention_days: int = Field(
        default=30,
        env="MQTT_INGESTION_RETENTION_DAYS",
        description="MQTT 流水记录保留天数（mqtt_ingestion_record）"
    )

    audit_event_retention_days: int = Field(
        default=30,
        env="AUDIT_EVENT_RETENTION_DAYS",
        description="审计事件保留天数（audit_event）"
    )

    enable_auto_cleanup: bool = Field(
        default=True,
        env="ENABLE_AUTO_CLEANUP",
        description="是否启用自动数据清理"
    )

    compensation_temperature_warning_margin_c: float = Field(
        default=5.0,
        env="COMPENSATION_TEMPERATURE_WARNING_MARGIN_C",
        description="补偿器温度“接近上限”预警边距（摄氏度）"
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

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def scheduler_effective_mode(self) -> str:
        if self.scheduler_mode != "auto":
            return self.scheduler_mode
        return "redis_owner" if self.is_production else "local"


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
