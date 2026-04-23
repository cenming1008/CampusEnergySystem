"""
应用层（Use Case / Workflow）
负责跨 service 的流程编排。
"""

from app.application.analysis import analyze_device_use_case
from app.application.device_management import create_device_smart_use_case
from app.application.device_management import toggle_device_status_use_case
from app.application.device_reporting import report_device_data_use_case
from app.application.device_reporting import (
    get_device_data_use_case,
    get_device_statistics_use_case,
)
from app.application.energy_management import (
    get_carbon_summary_use_case,
    get_energy_statistics_use_case,
    list_carbon_emissions_use_case,
    save_energy_data_use_case,
)
from app.application.inspection import create_inspection_task_use_case
from app.application.inspection import get_inspection_statistics_use_case
from app.application.maintenance import create_maintenance_record_use_case
from app.application.maintenance import summarize_maintenance_statistics_use_case
from app.application.telemetry_ingestion import (
    TelemetryIngestionResult,
    ingest_telemetry_use_case,
)
from app.application.reporting import list_energy_report_rows_use_case
from app.application.reporting import (
    build_report_csv_export_use_case,
    list_alarm_report_rows_use_case,
    list_carbon_report_rows_use_case,
)
from app.application.users import change_my_password_use_case
from app.application.users import create_user_use_case
from app.application.users import revoke_user_sessions_use_case

__all__ = [
    "TelemetryIngestionResult",
    "analyze_device_use_case",
    "build_report_csv_export_use_case",
    "change_my_password_use_case",
    "create_device_smart_use_case",
    "create_inspection_task_use_case",
    "create_maintenance_record_use_case",
    "create_user_use_case",
    "get_device_data_use_case",
    "get_device_statistics_use_case",
    "get_inspection_statistics_use_case",
    "get_carbon_summary_use_case",
    "get_energy_statistics_use_case",
    "ingest_telemetry_use_case",
    "list_energy_report_rows_use_case",
    "list_alarm_report_rows_use_case",
    "list_carbon_report_rows_use_case",
    "list_carbon_emissions_use_case",
    "revoke_user_sessions_use_case",
    "report_device_data_use_case",
    "save_energy_data_use_case",
    "summarize_maintenance_statistics_use_case",
    "toggle_device_status_use_case",
]
