"""
报表导出API端点
"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.tables import EnergyData, Device

router = APIRouter()


@router.get("/export_csv")
def export_csv(session: Session = Depends(get_session)):
    """导出设备历史数据为CSV文件"""
    # 创建CSV缓冲区
    output = io.StringIO()
    writer = csv.writer(output)
    
    # 写入表头
    writer.writerow([
        "时间", "设备ID", "设备名称",
        "电压(V)", "电流(A)", "功率(kW)", "能耗(kWh)"
    ])
    
    # 查询数据（限制1000条）
    statement = (
        select(EnergyData, Device.name)
        .join(Device, Device.id == EnergyData.device_id)
        .order_by(EnergyData.timestamp.desc())
        .limit(1000)
    )
    results = session.exec(statement).all()
    
    # 写入数据行
    for data, device_name in results:
        writer.writerow([
            data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            data.device_id,
            device_name,
            data.voltage,
            data.current,
            data.power,
            data.energy
        ])
    
    # 返回CSV文件
    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=energy_report.csv"
    return response