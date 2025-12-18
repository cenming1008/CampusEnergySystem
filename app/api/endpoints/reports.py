import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.tables import DeviceData, Device

router = APIRouter()

@router.get("/export_csv")
def export_telemetry_csv(session: Session = Depends(get_session)):
    """
    导出所有设备的历史数据为 CSV 文件
    """
    # 1. 创建内存中的 CSV 缓冲区
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 2. 写入表头
    writer.writerow(["时间", "设备ID", "设备名称", "电压(V)", "电流(A)", "功率(kW)", "能耗(kWh)"])
    
    # 3. 查询数据 (为了演示只取最近 1000 条，防止卡死)
    # 联表查询：我们需要 Device 表里的 name
    statement = (
        select(DeviceData, Device.name)
        .join(Device, Device.id == DeviceData.device_id)
        .order_by(DeviceData.timestamp.desc())
        .limit(1000)
    )
    results = session.exec(statement).all()
    
    # 4. 写入数据行
    for data, dev_name in results:
        writer.writerow([
            data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            data.device_id,
            dev_name,
            data.voltage,
            data.current,
            data.power,
            data.energy
        ])
    
    # 5. 重置指针到开头
    output.seek(0)
    
    # 6.以此流的形式返回，浏览器会自动触发下载
    response = StreamingResponse(
        iter([output.getvalue()]), 
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=energy_report.csv"
    return response