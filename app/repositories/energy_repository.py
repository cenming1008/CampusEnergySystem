"""
能源数据访问
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlmodel import Session, func, select

from app.models.tables import CarbonEmission, Device, EnergyData, EnergyStatistics


class EnergyRepository:
    """能源相关数据仓储。"""

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
        session.add(energy_data)
        if commit:
            session.commit()
            session.refresh(energy_data)
        else:
            session.flush()
        return energy_data

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
        session.add(carbon_record)
        if commit:
            session.commit()
            session.refresh(carbon_record)
        else:
            session.flush()
        return carbon_record

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
    ) -> list[CarbonEmission]:
        statement = select(CarbonEmission)
        if device_id:
            statement = statement.where(CarbonEmission.device_id == device_id)
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
    ) -> list[EnergyData]:
        statement = select(EnergyData).where(
            EnergyData.energy_type == energy_type,
            EnergyData.timestamp >= start_time,
            EnergyData.timestamp <= end_time,
        )
        if device_id:
            statement = statement.where(EnergyData.device_id == device_id)
        return list(session.exec(statement).all())

    @staticmethod
    def summarize_carbon_rows(
        session: Session,
        start_time: datetime,
        end_time: datetime,
        device_id: Optional[int] = None,
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
        statement = statement.group_by(CarbonEmission.energy_type)
        return list(session.exec(statement).all())

    @staticmethod
    def save_statistics_record(session: Session, stat_record: EnergyStatistics) -> EnergyStatistics:
        session.add(stat_record)
        session.commit()
        session.refresh(stat_record)
        return stat_record

    @staticmethod
    def list_energy_report_rows(session: Session, limit: int = 1000) -> list[tuple[EnergyData, str]]:
        statement = (
            select(EnergyData, Device.name)
            .join(Device, Device.id == EnergyData.device_id)
            .order_by(EnergyData.timestamp.desc())
            .limit(limit)
        )
        return list(session.exec(statement).all())
