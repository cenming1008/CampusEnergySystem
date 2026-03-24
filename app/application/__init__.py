"""
应用层（Use Case / Workflow）
负责跨 service 的流程编排。
"""

from app.application.device_reporting import report_device_data_use_case
from app.application.energy_management import (
    get_carbon_summary_use_case,
    get_energy_statistics_use_case,
    list_carbon_emissions_use_case,
    save_energy_data_use_case,
)
from app.application.forecasting import (
    evaluate_lstm_model_use_case,
    evaluate_prediction_accuracy_use_case,
    forecast_load_use_case,
    get_forecast_adapter,
    list_latest_predictions_use_case,
    train_lstm_model_use_case,
)
from app.application.telemetry_ingestion import (
    TelemetryIngestionResult,
    ingest_telemetry_use_case,
)

__all__ = [
    "TelemetryIngestionResult",
    "evaluate_lstm_model_use_case",
    "evaluate_prediction_accuracy_use_case",
    "forecast_load_use_case",
    "get_carbon_summary_use_case",
    "get_energy_statistics_use_case",
    "get_forecast_adapter",
    "ingest_telemetry_use_case",
    "list_carbon_emissions_use_case",
    "list_latest_predictions_use_case",
    "report_device_data_use_case",
    "save_energy_data_use_case",
    "train_lstm_model_use_case",
]
