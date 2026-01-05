import uvicorn
from app.core.settings import settings  # 使用统一配置管理

if __name__ == "__main__":
    # 从统一配置读取启动参数
    # 这样可以通过环境变量或 .env 文件灵活配置
    uvicorn.run(
        "app.main:app", 
        host=settings.host, 
        port=settings.port, 
        reload=settings.reload,  # 从配置读取，生产环境自动关闭
        workers=settings.workers  # 从配置读取工作进程数
    )