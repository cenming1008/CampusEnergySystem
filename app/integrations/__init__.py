"""
外部集成层
"""

from app.integrations.forecasting import ForecastAdapter
from app.integrations.mqtt import process_payload, process_payload_dict

__all__ = [
    "ForecastAdapter",
    "process_payload",
    "process_payload_dict",
]
