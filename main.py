import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.core.database import init_db
from app.api.endpoints import devices, telemetry, analysis, alarms, reports, fdd, auth # 👈 1. 导入 auth
from app.api.deps import get_current_user # 👈 2. 导入依赖
from fastapi import Depends # 👈 3. 确保导入 Depends

# 👇 1. 导入新模块 (reports, fdd)
from app.api.endpoints import devices, telemetry, analysis, alarms, reports, fdd
from app.models import tables

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()image.png
    print("🚀 数据库连接成功，全功能系统启动！")
    yield
    print("🛑 系统已关闭")

app = FastAPI(title="煤矿综合能源管理系统后端 image.png", lifespan=lifespan)

app.mount("/view", StaticFiles(directory="static", html=True), name="static")

# 👇 4. 注册登录路由 (不需要保护)
app.include_router(auth.router, prefix="/auth", tags=["认证中心"])

# 👇 5. 给敏感路由加上 dependencies=[Depends(get_current_user)]
# 这样，如果不登录，这些接口都访问不了！
app.include_router(devices.router, prefix="/devices", tags=["设备管理"], dependencies=[Depends(get_current_user)])
app.include_router(alarms.router, prefix="/alarms", tags=["报警中心"], dependencies=[Depends(get_current_user)])
app.include_router(reports.router, prefix="/reports", tags=["报表中心"], dependencies=[Depends(get_current_user)])
# telemetry 通常是设备发的，可能需要单独的 API Key 机制，或者暂时留空不保护以便模拟器运行
app.include_router(telemetry.router, prefix="/telemetry", tags=["遥测数据"]) 
app.include_router(analysis.router, prefix="/analysis", tags=["数据分析"], dependencies=[Depends(get_current_user)])
app.include_router(fdd.router, prefix="/fdd", tags=["故障诊断"], dependencies=[Depends(get_current_user)])

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8088, reload=True)