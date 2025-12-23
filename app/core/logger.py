import sys
import os
from loguru import logger

# 1. 定义日志保存路径
LOG_DIR = "logs"
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# 2. 移除默认的控制台输出 (默认级别可能不符合需求)
logger.remove()

# 3. 自定义控制台输出格式
# <green>{time}</green>: 绿色时间
# <level>{level}</level>: 日志级别
# <cyan>{name}:{function}:{line}</cyan>: 文件名:函数名:行号 (方便定位 bug)
logger.add(
    sys.stderr,
    level="INFO",
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
)

# 4. 添加文件输出：普通日志 (按天轮转，保留 7 天)
logger.add(
    os.path.join(LOG_DIR, "ems_app_{time:YYYY-MM-DD}.log"),
    rotation="00:00",   # 每天午夜创建新文件
    retention="7 days", # 只保留最近 7 天的日志
    level="INFO",       # 记录 INFO 及以上级别
    encoding="utf-8",
    enqueue=True,       # 开启异步写入 (避免阻塞主线程)
)

# 5. 添加文件输出：错误日志 (单独保存，方便排查问题)
logger.add(
    os.path.join(LOG_DIR, "ems_error_{time:YYYY-MM-DD}.log"),
    rotation="00:00",
    retention="30 days",
    level="ERROR",      # 只记录 ERROR 和 CRITICAL
    encoding="utf-8",
    enqueue=True,
    backtrace=True,     # 记录完整的异常堆栈
    diagnose=True,      # 显示变量值 (生产环境可关闭以免泄露敏感信息)
)

# 导出 logger 对象
__all__ = ["logger"]