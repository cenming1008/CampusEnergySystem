"""
能源数据访问
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, func, select

from app.core.access_control import parse_location_scope
from app.models.tables import CarbonEmission, Device, EnergyData, EnergyStatistics
from app.repositories.base import BaseRepository


class EnergyRepository(BaseRepository):
    """能源相关数据仓储。"""

    @staticmethod
    def resolve_allowed_location_ids(current_user) -> Optional[set[int]]:
        return parse_location_scope(current_user) if current_user is not None else None

    @staticmethod
    def get_energy_record(session: Session, device_id: int, timestamp: datetime) -> Optional[EnergyData]:
        return session.exec(
            select(EnergyData).where(
                EnergyData.device_id == device_id,
                EnergyData.timestamp == timestamp,
            )
        ).first()

    @staticmethod
    def save_energy_record(session: Session, energy_data: EnergyData, commit: bool = True) -> EnergyData:
        return EnergyRepository.save_model(session, energy_data, commit=commit)

    @staticmethod
    def get_carbon_record(session: Session, device_id: int, timestamp: datetime) -> Optional[CarbonEmission]:
        return session.exec(
            select(CarbonEmission).where(
                CarbonEmission.device_id == device_id,
                CarbonEmission.timestamp == timestamp,
            )
        ).first()

    @staticmethod
    def save_carbon_record(session: Session, carbon_record: CarbonEmission, commit: bool = True) -> CarbonEmission:
        return EnergyRepository.save_model(session, carbon_record, commit=commit)

    @staticmethod
    def list_energy_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[EnergyData]:
        statement = select(EnergyData).where(EnergyData.device_id == device_id)
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        if start_time:
            statement = statement.where(EnergyData.timestamp >= start_time)
        if end_time:
            statement = statement.where(EnergyData.timestamp <= end_time)
        statement = statement.order_by(EnergyData.timestamp.desc()).limit(limit)
        return list(reversed(session.exec(statement).all()))

    @staticmethod
    def get_latest_energy_data(
        session: Session,
        device_id: int,
        energy_type: Optional[str] = None,
    ) -> Optional[EnergyData]:
        statement = select(EnergyData).where(EnergyData.device_id == device_id)
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        statement = statement.order_by(EnergyData.timestamp.desc()).limit(1)
        return session.exec(statement).first()

    @staticmethod
    def get_first_energy_data_since(
        session: Session,
        device_id: int,
        start_time: datetime,
        energy_type: Optional[str] = None,
    ) -> Optional[EnergyData]:
        statement = select(EnergyData).where(
            EnergyData.device_id == device_id,
            EnergyData.timestamp >= start_time,
        )
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        statement = statement.order_by(EnergyData.timestamp.asc()).limit(1)
        return session.exec(statement).first()

    @staticmethod
    def list_carbon_emissions(
        session: Session,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[CarbonEmission]:
        statement = select(CarbonEmission)
        if device_id:
            statement = statement.where(CarbonEmission.device_id == device_id)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(CarbonEmission.device_id.in_(allowed_device_ids))
        if energy_type:
            statement = statement.where(CarbonEmission.energy_type == energy_type)
        if start_time:
            statement = statement.where(CarbonEmission.timestamp >= start_time)
        if end_time:
            statement = statement.where(CarbonEmission.timestamp <= end_time)
        statement = statement.order_by(CarbonEmission.timestamp.desc())
        return list(session.exec(statement).all())

    @staticmethod
    def list_energy_statistics_rows(
        session: Session,
        device_id: Optional[int],
        energy_type: str,
        start_time: datetime,
        end_time: datetime,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[EnergyData]:
        statement = select(EnergyData).where(
            EnergyData.energy_type == energy_type,
            EnergyData.timestamp >= start_time,
            EnergyData.timestamp <= end_time,
        )
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(EnergyData.device_id.in_(allowed_device_ids))
        return list(session.exec(statement).all())

    @staticmethod
    def summarize_carbon_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None,
        allowed_device_ids: Optional[set[int]] = None,
    ) -> list[tuple[str, float, float]]:
        statement = select(
            CarbonEmission.energy_type,
            func.sum(CarbonEmission.carbon_emission).label("total_emission"),
            func.sum(CarbonEmission.energy_consumption).label("total_consumption"),
        ).where(
            CarbonEmission.timestamp >= start_time,
            CarbonEmission.timestamp <= end_time,
        )
        if device_id:
            statement = statement.where(CarbonEmission.device_id == device_id)
        if allowed_device_ids is not None:
            if not allowed_device_ids:
                return []
            statement = statement.where(CarbonEmission.device_id.in_(allowed_device_ids))
        statement = statement.group_by(CarbonEmission.energy_type)
        return list(session.exec(statement).all())

    @staticmethod
    def save_statistics_record(session: Session, stat_record: EnergyStatistics) -> EnergyStatistics:
        return EnergyRepository.save_model(session, stat_record)

    @staticmethod
    def list_energy_report_rows(
        session: Session,
        current_user=None,
        device_id: Optional[int] = None,
        energy_type: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 1000,
    ) -> list[tuple[EnergyData, str]]:
        statement = (
            select(EnergyData, Device.name)
            .join(Device, Device.id == EnergyData.device_id)
            .order_by(EnergyData.timestamp.desc())
            .limit(limit)
        )
        allowed_location_ids = EnergyRepository.resolve_allowed_location_ids(current_user)
        if allowed_location_ids is not None:
            statement = statement.where(Device.location_id.in_(allowed_location_ids))
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        if energy_type:
            statement = statement.where(EnergyData.energy_type == energy_type)
        if start_time:
            statement = statement.where(EnergyData.timestamp >= start_time)
        if end_time:
            statement = statement.where(EnergyData.timestamp <= end_time)
        return list(session.exec(statement).all())
