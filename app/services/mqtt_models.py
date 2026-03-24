"""
MQTT 处理相关数据模型
"""

from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TelemetryBroadcastData:
    device_id: int
    voltage: float | None
    current: float | None
    power: float | None
    energy: float | None
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
