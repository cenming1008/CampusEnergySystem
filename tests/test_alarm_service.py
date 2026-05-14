import os
import unittest
import unittest.mock
from datetime import datetime, timedelta
from typing import Optional

from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import Alarm, Device
from app.services.alarm_service import AlarmService


class TestAlarmService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def _create_device(self, session: Session, sn: str, location_id: Optional[int] = None) -> Device:
        device = Device(
            name=f"设备-{sn}",
            sn=sn,
            device_type="load",
            device_category="load",
            energy_type="electricity",
            location_id=location_id,
            is_active=True,
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        return device

    def test_check_and_create_alarm_deduplicates_continuous_anomaly_and_marks_recovery(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-001")
            with unittest.mock.patch.object(
                AlarmService,
                "load_thresholds",
                return_value={"default": {"current_max": 10.0}},
            ):
                first_at = datetime(2026, 3, 29, 10, 0, 0)
                second_at = first_at + timedelta(minutes=2)
                recovery_at = first_at + timedelta(minutes=5)

                created = AlarmService.check_and_create_alarm(
                    session,
                    device.id,
                    {"current": 12.0},
                    first_at,
                )
                self.assertEqual(len(created), 1)

                created = AlarmService.check_and_create_alarm(
                    session,
                    device.id,
                    {"current": 18.0},
                    second_at,
                )
                self.assertEqual(created, [])

                alarms = session.exec(select(Alarm)).all()
                self.assertEqual(len(alarms), 1)
                alarm = alarms[0]
                self.assertIsNotNone(alarm.instance_key)
                self.assertEqual(alarm.timestamp, first_at)
                self.assertEqual(alarm.last_seen_at, second_at)
                self.assertIsNone(alarm.recovered_at)
                self.assertFalse(alarm.is_resolved)

                AlarmService.check_and_create_alarm(
                    session,
                    device.id,
                    {"current": 5.0},
                    recovery_at,
                )
                session.refresh(alarm)
                self.assertEqual(alarm.recovered_at, recovery_at)
                self.assertFalse(alarm.is_resolved)
                self.assertIsNone(alarm.resolved_at)

    def test_general_threshold_alarm_uses_platform_rule_source_for_load_device(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-011")
            with unittest.mock.patch.object(
                AlarmService,
                "load_thresholds",
                return_value={"default": {"current_max": 10.0}},
            ):
                created = AlarmService.check_and_create_alarm(
                    session,
                    device.id,
                    {"current": 12.0},
                    datetime(2026, 5, 14, 9, 0, 0),
                )

            self.assertEqual(len(created), 1)
            self.assertEqual(created[0].source, "platform_rule")

    def test_general_threshold_alarm_skips_compensation_devices(self):
        with Session(self.engine) as session:
            device = Device(
                name="补偿柜-ALARM-012",
                sn="ALARM-012",
                device_type="capacitor_bank_controller",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            with unittest.mock.patch.object(
                AlarmService,
                "load_thresholds",
                return_value={"default": {"current_max": 10.0, "voltage_max": 230.0, "voltage_min": 190.0}},
            ):
                created = AlarmService.check_and_create_alarm(
                    session,
                    device.id,
                    {"current": 99.0, "voltage": 260.0},
                    datetime(2026, 5, 14, 9, 5, 0),
                )

            self.assertEqual(created, [])
            self.assertEqual(session.exec(select(Alarm)).all(), [])

    def test_manual_handle_is_separate_from_system_recovery(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-002")
            triggered_at = datetime(2026, 3, 29, 11, 0, 0)
            recovered_at = triggered_at + timedelta(minutes=3)

            alarm = AlarmService.create_alarm(
                session,
                device.id,
                "电压异常",
                timestamp=triggered_at,
                category="voltage_out_of_range",
                source="telemetry",
                instance_key=AlarmService.build_instance_key(device.id, "voltage_out_of_range"),
                last_seen_at=triggered_at,
            )
            alarm.recovered_at = recovered_at
            session.add(alarm)
            session.commit()

            handled = AlarmService.resolve_alarm(
                session,
                alarm.id,
                resolved_by="operator",
                handling_note="已确认，无需现场处理",
                allowed_device_ids={device.id},
            )
            self.assertTrue(handled)

            session.refresh(alarm)
            self.assertEqual(alarm.recovered_at, recovered_at)
            self.assertTrue(alarm.is_resolved)
            self.assertIsNotNone(alarm.resolved_at)
            self.assertEqual(alarm.resolved_by, "operator")
            self.assertEqual(alarm.handling_note, "已确认，无需现场处理")

    def test_resolve_all_alarms_respects_allowed_device_ids(self):
        with Session(self.engine) as session:
            device_a = self._create_device(session, "ALARM-003", location_id=1)
            device_b = self._create_device(session, "ALARM-004", location_id=2)

            alarm_a = AlarmService.create_alarm(session, device_a.id, "A-告警", category="threshold", auto_commit=False)
            alarm_b = AlarmService.create_alarm(session, device_b.id, "B-告警", category="threshold", auto_commit=False)
            session.commit()
            session.refresh(alarm_a)
            session.refresh(alarm_b)

            count = AlarmService.resolve_all_alarms(
                session,
                resolved_by="maintainer",
                allowed_device_ids={device_a.id},
            )
            self.assertEqual(count, 1)

            session.refresh(alarm_a)
            session.refresh(alarm_b)
            self.assertTrue(alarm_a.is_resolved)
            self.assertFalse(alarm_b.is_resolved)

    def test_list_alarms_filters_by_resolution_and_allowed_devices(self):
        with Session(self.engine) as session:
            device_a = self._create_device(session, "ALARM-005")
            device_b = self._create_device(session, "ALARM-006")
            alarm_a = AlarmService.create_alarm(session, device_a.id, "A-告警", category="threshold", auto_commit=False)
            alarm_b = AlarmService.create_alarm(session, device_b.id, "B-告警", category="threshold", auto_commit=False)
            alarm_b.is_resolved = True
            session.add(alarm_b)
            session.commit()

            alarms = AlarmService.list_alarms(
                session,
                resolved=False,
                allowed_device_ids={device_a.id},
            )

            self.assertEqual([alarm.id for alarm in alarms], [alarm_a.id])

    def test_get_alarm_count_supports_device_and_resolved_filters(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-007")
            alarm_a = AlarmService.create_alarm(session, device.id, "A-告警", category="threshold", auto_commit=False)
            alarm_b = AlarmService.create_alarm(session, device.id, "B-告警", category="threshold", auto_commit=False)
            alarm_b.is_resolved = True
            session.add(alarm_b)
            session.commit()

            unresolved_count = AlarmService.get_alarm_count(session, device_id=device.id, resolved=False)
            resolved_count = AlarmService.get_alarm_count(session, device_id=device.id, resolved=True)

            self.assertEqual(unresolved_count, 1)
            self.assertEqual(resolved_count, 1)

    def test_mark_recovered_alarms_backfills_instance_key_and_marks_recovery(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-008")
            alarm = AlarmService.create_alarm(
                session,
                device.id,
                "电流过高",
                category="current_overload",
                source="telemetry",
                instance_key=None,
                auto_commit=False,
            )
            session.commit()

            recovered_count = AlarmService.mark_recovered_alarms(
                session=session,
                device_id=device.id,
                active_instance_keys=set(),
                timestamp=datetime(2026, 4, 3, 10, 0, 0),
                categories={"current_overload"},
            )
            session.commit()
            session.refresh(alarm)

            self.assertEqual(recovered_count, 1)
            self.assertEqual(
                alarm.instance_key,
                AlarmService.build_instance_key(device.id, "current_overload", "telemetry"),
            )
            self.assertIsNotNone(alarm.recovered_at)

    def test_load_thresholds_returns_empty_when_file_missing(self):
        with unittest.mock.patch("os.path.exists", return_value=False):
            thresholds = AlarmService.load_thresholds()

        self.assertEqual(thresholds, {})

    def test_check_capacitor_bank_faults_creates_and_recovers_protocol_alarms(self):
        with Session(self.engine) as session:
            device = Device(
                name="补偿柜-ALARM-009",
                sn="ALARM-009",
                device_type="capacitor_bank_controller",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            first_at = datetime(2026, 4, 15, 16, 0, 0)
            recovered_at = first_at + timedelta(minutes=3)

            created = AlarmService.check_capacitor_bank_faults(
                session=session,
                device_id=device.id,
                cap_data={
                    "temperature": 58.0,
                    "temp_alarm": True,
                    "overvoltage_alarm_a": True,
                    "voltage_thd_alarm_b": True,
                    "current_thd_alarm_c": True,
                    "undercurrent_a": True,
                    "reactive_power": -18.0,
                    "leading_a": True,
                    "leading_b": True,
                    "leading_c": False,
                },
                timestamp=first_at,
                profile_data={
                    "temperature_upper_limit": 55.0,
                    "overvoltage_threshold": 245.0,
                    "voltage_harmonic_threshold": 4.5,
                    "current_harmonic_threshold": 2.8,
                },
            )

            self.assertEqual(len(created), 6)
            self.assertTrue(all(alarm.source == "device_native" for alarm in created if alarm.category != "cap_overcompensation"))
            self.assertEqual(
                next(alarm for alarm in created if alarm.category == "cap_overcompensation").source,
                "platform_rule",
            )
            categories = {alarm.category for alarm in session.exec(select(Alarm)).all()}
            self.assertEqual(
                categories,
                {
                    "cap_temp_alarm",
                    "cap_overvoltage_a",
                    "cap_voltage_thd_b",
                    "cap_current_thd_c",
                    "cap_undercurrent_a",
                    "cap_overcompensation",
                },
            )

            AlarmService.check_capacitor_bank_faults(
                session=session,
                device_id=device.id,
                cap_data={
                    "temperature": 42.0,
                    "temp_alarm": False,
                    "overvoltage_alarm_a": False,
                    "voltage_thd_alarm_b": False,
                    "current_thd_alarm_c": False,
                    "undercurrent_a": False,
                    "reactive_power": -2.0,
                    "leading_a": False,
                    "leading_b": False,
                    "leading_c": False,
                },
                timestamp=recovered_at,
                profile_data={
                    "temperature_upper_limit": 55.0,
                    "overvoltage_threshold": 245.0,
                    "voltage_harmonic_threshold": 4.5,
                    "current_harmonic_threshold": 2.8,
                },
            )

            for alarm in session.exec(select(Alarm)).all():
                self.assertEqual(alarm.recovered_at, recovered_at)

    def test_check_capacitor_bank_faults_uses_threshold_values_without_status_bits(self):
        with Session(self.engine) as session:
            device = Device(
                name="补偿柜-ALARM-010",
                sn="ALARM-010",
                device_type="capacitor_bank_controller",
                device_subtype="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
                is_active=True,
            )
            session.add(device)
            session.commit()
            session.refresh(device)

            created = AlarmService.check_capacitor_bank_faults(
                session=session,
                device_id=device.id,
                cap_data={
                    "temperature": 56.5,
                    "voltage_a": 248.0,
                    "voltage_thd_a": 4.9,
                    "current_harmonic_a": 3.2,
                },
                timestamp=datetime(2026, 4, 15, 17, 0, 0),
                profile_data={
                    "temperature_upper_limit": 55.0,
                    "overvoltage_threshold": 245.0,
                    "voltage_harmonic_threshold": 4.5,
                    "current_harmonic_threshold": 2.8,
                },
            )

            self.assertEqual({alarm.category for alarm in created}, {
                "cap_temp_alarm",
                "cap_overvoltage_a",
                "cap_voltage_thd_a",
                "cap_current_thd_a",
            })
            self.assertEqual({alarm.source for alarm in created}, {"platform_rule"})

    def test_sync_platform_comm_alarm_creates_and_recovers_offline_instance(self):
        with Session(self.engine) as session:
            device = self._create_device(session, "ALARM-013")
            detected_at = datetime(2026, 5, 14, 10, 0, 0)
            recovered_at = detected_at + timedelta(minutes=3)

            alarm, created = AlarmService.sync_platform_comm_alarm(
                session=session,
                device_id=device.id,
                is_offline=True,
                timestamp=detected_at,
                last_success_at=detected_at - timedelta(minutes=10),
            )

            self.assertTrue(created)
            self.assertEqual(alarm.source, "platform_comm")
            self.assertEqual(alarm.category, "communication_offline")
            self.assertIsNone(alarm.recovered_at)
            self.assertFalse(alarm.is_resolved)

            recovered_count = AlarmService.sync_platform_comm_alarm(
                session=session,
                device_id=device.id,
                is_offline=False,
                timestamp=recovered_at,
                last_success_at=recovered_at,
            )

            session.refresh(alarm)
            self.assertEqual(recovered_count, 1)
            self.assertEqual(alarm.recovered_at, recovered_at)
            self.assertFalse(alarm.is_resolved)


if __name__ == "__main__":
    unittest.main()
