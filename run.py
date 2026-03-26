import uvicorn
from app.core.settings import settings  # 使用统一配置管理

if __name__ == "__main__":
    # 开发环境需要热重载时必须传入导入字符串；
    # 非热重载场景直接传应用对象，减少文件监听和导入链带来的启动干扰。
    if settings.reload:
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=True,
            workers=1,
        )
    else:
        from app.main import app

        uvicorn.run(
            app,
            host=settings.host,
            port=settings.port,
            reload=False,
            workers=max(1, settings.workers),
        )
