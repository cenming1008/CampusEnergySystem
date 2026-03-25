"""
报表导出API端点
"""
import csv
import io
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlmodel import Session

from app.application.reporting import list_energy_report_rows_use_case
from app.core.database import get_session

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
    results = list_energy_report_rows_use_case(session=session, limit=1000)
    
    # 写入数据行
    for data, device_name in results:
        writer.writerow([
            data.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            data.device_id,
            device_name,
            data.voltage,
            data.current,
            data.flow_rate,
            data.consumption
        ])
    
    # 返回CSV文件
    output.seek(0)
    response = StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv"
    )
    response.headers["Content-Disposition"] = "attachment; filename=energy_report.csv"
    return response
