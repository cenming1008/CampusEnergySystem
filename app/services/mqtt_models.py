"""
MQTT 处理相关数据模型
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Optional


@dataclass(frozen=True)
class TelemetryBroadcastData:
    device_id: int
    voltage: Optional[float]
    current: Optional[float]
    power: Optional[float]
    energy: Optional[float]
    timestamp: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class TelemetryBroadcastMessage:
    type: str
    data: TelemetryBroadcastData

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "data": self.data.to_dict(),
        }
