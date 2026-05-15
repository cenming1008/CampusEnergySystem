"""
JKWF-LCD 遥测摄取集成测试

验证含 JKWF-LCD 字段的 MQTT payload 经处理后：
1. EnergyData 写入正确的无功功率（三相求和）
2. CapacitorBankTelemetry 行写入，状态标志位和投切状态正确解码
"""

import os
import unittest
from datetime import datetime
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from sqlmodel import Session, SQLModel, create_engine, select

from app.integrations.mqtt.processor import (
    apply_field_aliases,
    extract_capacitor_bank_control_profile,
    extract_capacitor_bank_telemetry,
    persist_device_data,
    normalize_compensation_measurements,
)
from app.models.tables import Alarm, CapacitorBankControlProfile, CapacitorBankTelemetry, Device


# ──────────────────────────────────────────────────────────────────────────────
# 测试用 payload（模拟 JKWF-LCD 网关上报格式，字段已含别名）
# ──────────────────────────────────────────────────────────────────────────────

RAW_PAYLOAD = {
    "device_code": "JKWF-TEST-01",
    "timestamp": "2026-04-14T10:00:00",
    # 三相电压 / 电流（保留原始 gateway 字段名，经别名映射后进入）
    "voltage_a": 220.0, "voltage_b": 219.5, "voltage_c": 221.0,
    "current_a": 10.2, "current_b": 9.8, "current_c": 10.5,
    # 三相功率因数
    "pf_a": 0.985, "pf_b": 0.980, "pf_c": 0.990,
    # 三相有功 / 无功 / 视在功率（已用别名形式）
    "p_a": 22.0, "p_b": 21.0, "p_c": 23.0,
    "q_a": -8.0, "q_b": -7.0, "q_c": -9.0,    # 容性为负
    "s_a": 24.0, "s_b": 23.0, "s_c": 25.0,
    # 谐波 THD
    "thd_ua": 3.2, "thd_ub": 3.0, "thd_uc": 3.1,
    "thd_ia": 1.5, "thd_ib": 1.4, "thd_ic": 1.6,
    # 系统参数
    "freq": 50.0,
    "temp": 38.0,
    # 状态标志位：leading_a (bit0) + temp_alarm (bit15) → 0x8001
    "jkwf_status": 0x8001,
    # 投切状态寄存器
    "circuit_state_1": 0x0F05,
    "circuit_state_2": 0x0300,
    "circuit_state_3": 0x0000,
    # 控制台参数快照
    "switch_on_power_factor": 95,
    "switch_off_power_factor": 105,
    "switch_on_delay_seconds": 10,
    "switch_off_delay_seconds": 8,
    "phase_a_circuit_total_count": 3,
    "phase_b_circuit_total_count": 3,
    "phase_c_circuit_total_count": 2,
    "common_1_circuit_total_count": 6,
    "common_2_circuit_total_count": 4,
    "common_3_circuit_total_count": 2,
    "phase_a_capacity_steps_kvar": [12.0, 12.0, 24.0],
    "phase_b_capacity_steps_kvar": [48.0, 12.0, 12.0],
    "phase_c_capacity_steps_kvar": [24.0, 48.0],
    "common_1_capacity_steps_kvar": [30.0, 60.0, 90.0, 90.0, 30.0, 60.0],
    "common_2_capacity_steps_kvar": [90.0, 90.0, 30.0, 60.0],
    "common_3_capacity_steps_kvar": [90.0, 90.0],
    "running_circuit_count": 12,
    "split_circuit_running_count": 6,
    "common_circuit_running_count": 6,
    "phase_a_circuit_running_count": 2,
    "phase_b_circuit_running_count": 3,
    "phase_c_circuit_running_count": 1,
    "common_group_1_running_count": 4,
    "common_group_2_running_count": 2,
    "common_group_3_running_count": 0,
    "control_mode": "manual",
    "common_capacity_code": "4:1233",
    "split_capacity_code": "7:1124",
    "temperature_upper_limit": 55.0,
    "baud_rate": 9600,
    "voltage_harmonics_a": [
        {"order": 2, "value": 1.2},
        {"order": 5, "value": 6.4},
        {"order": 32, "value": 9.9},
        {"order": 7, "value": "bad"},
    ],
    "current_harmonics_b": [
        {"order": 3, "value": 0.8},
        {"order": 11, "value": 2.1},
    ],
}


class TestCapacitorBankExtraction(unittest.TestCase):
    """测试 extract_capacitor_bank_telemetry() 的字段提取和解码。"""

    def setUp(self):
        # 完整的字段归一化流水线（别名 → 补偿测量归一）
        data = apply_field_aliases(RAW_PAYLOAD)
        self.data = normalize_compensation_measurements(data)

    def test_three_phase_voltage_extracted(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertIsNotNone(result)
        self.assertAlmostEqual(result["voltage_a"], 220.0, places=1)
        self.assertAlmostEqual(result["voltage_b"], 219.5, places=1)
        self.assertAlmostEqual(result["voltage_c"], 221.0, places=1)

    def test_three_phase_reactive_power_extracted(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertAlmostEqual(result["reactive_power_a"], -8.0, places=1)
        self.assertAlmostEqual(result["reactive_power_b"], -7.0, places=1)
        self.assertAlmostEqual(result["reactive_power_c"], -9.0, places=1)

    def test_running_count_and_control_mode_fields_extracted(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertEqual(result["running_circuit_count"], 12)
        self.assertEqual(result["split_circuit_running_count"], 6)
        self.assertEqual(result["common_group_2_running_count"], 2)
        self.assertEqual(result["control_mode"], "manual")

    def test_apparent_power_extracted_via_alias(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertAlmostEqual(result["apparent_power_a"], 24.0, places=1)
        self.assertAlmostEqual(result["apparent_power_b"], 23.0, places=1)
        self.assertAlmostEqual(result["apparent_power_c"], 25.0, places=1)

    def test_voltage_thd_extracted_via_alias(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertAlmostEqual(result["voltage_thd_a"], 3.2, places=1)
        self.assertAlmostEqual(result["voltage_thd_b"], 3.0, places=1)
        self.assertAlmostEqual(result["voltage_thd_c"], 3.1, places=1)

    def test_current_harmonic_extracted(self):
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertAlmostEqual(result["current_harmonic_a"], 1.5, places=1)

    def test_harmonic_spectrum_extracted_and_sanitized(self):
        result = extract_capacitor_bank_telemetry(self.data)

        self.assertEqual(
            result["voltage_harmonics_a"],
            [{"order": 2, "value": 1.2}, {"order": 5, "value": 6.4}],
        )
        self.assertEqual(
            result["current_harmonics_b"],
            [{"order": 3, "value": 0.8}, {"order": 11, "value": 2.1}],
        )
        self.assertNotIn("voltage_harmonics_b", result)

    def test_status_flags_decoded(self):
        """jkwf_status=0x8001 → leading_a=True, temp_alarm=True, 其余 False"""
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertTrue(result["leading_a"])
        self.assertTrue(result["temp_alarm"])
        self.assertFalse(result["leading_b"])
        self.assertFalse(result["leading_c"])
        self.assertFalse(result["undercurrent_a"])

    def test_circuit_states_decoded(self):
        """circuit_state_1=0x0F05 → phase_a=0x0F, phase_b=0x05"""
        result = extract_capacitor_bank_telemetry(self.data)
        self.assertEqual(result["circuit_state_phase_a"], 0x0F)
        self.assertEqual(result["circuit_state_phase_b"], 0x05)
        self.assertEqual(result["circuit_state_phase_c"], 0x03)
        self.assertEqual(result["circuit_state_common_1"], 0x00)

    def test_no_jkwf_fields_returns_none(self):
        minimal = {"voltage": 220.0, "consumption": 0.0}
        result = extract_capacitor_bank_telemetry(minimal)
        self.assertIsNone(result)


class TestReactivePowerNormalization(unittest.TestCase):
    """三相无功求和归一验证（通过 normalize_compensation_measurements）。"""

    def test_reactive_power_summed_from_three_phases(self):
        data = apply_field_aliases({"q_a": -8.0, "q_b": -7.0, "q_c": -9.0})
        normalized = normalize_compensation_measurements(data)
        self.assertAlmostEqual(normalized["reactive_power"], -24.0, places=3)


class TestCapacitorBankControlProfileExtraction(unittest.TestCase):
    def test_control_profile_fields_extracted(self):
        data = apply_field_aliases(RAW_PAYLOAD)
        result = extract_capacitor_bank_control_profile(data)
        self.assertIsNotNone(result)
        self.assertEqual(result["switch_on_power_factor"], 95)
        self.assertEqual(result["switch_off_power_factor"], 105)
        self.assertEqual(result["baud_rate"], 9600)
        self.assertEqual(result["phase_a_circuit_total_count"], 3)
        self.assertEqual(result["common_2_circuit_total_count"], 4)
        self.assertEqual(result["phase_a_capacity_steps_kvar_json"], [12.0, 12.0, 24.0])
        self.assertEqual(result["common_3_capacity_steps_kvar_json"], [90.0, 90.0])
        self.assertEqual(result["common_capacity_code"], "4:1233")


class TestCapacitorBankTelemetryPersistence(unittest.TestCase):
    """验证 CapacitorBankTelemetry 在 SQLite 内存库中正确写入。"""

    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_write_and_read_telemetry_row(self):
        ts = datetime(2026, 4, 14, 10, 0, 0)
        device_id: int
        with Session(self.engine) as session:
            device = Device(
                name="JKWF 补偿柜",
                sn="JKWF-TEST-01",
                device_type="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            device_id = device.id  # 在 session 关闭前保存

            record = CapacitorBankTelemetry(
                device_id=device_id,
                timestamp=ts,
                voltage_a=220.0, voltage_b=219.5, voltage_c=221.0,
                reactive_power_a=-8.0, reactive_power_b=-7.0, reactive_power_c=-9.0,
                apparent_power_a=24.0,
                voltage_thd_a=3.2,
                voltage_harmonics_a=[{"order": 5, "value": 6.4}],
                current_harmonics_b=[{"order": 11, "value": 2.1}],
                leading_a=True, temp_alarm=True, leading_b=False,
                circuit_state_phase_a=0x0F, circuit_state_phase_b=0x05,
                circuit_state_common_1=0x00,
            )
            session.add(record)
            session.commit()

            profile = CapacitorBankControlProfile(
                device_id=device_id,
                switch_on_power_factor=95,
                source="telemetry",
                common_capacity_code="4:1233",
            )
            session.add(profile)
            session.commit()

        with Session(self.engine) as session:
            row = session.exec(
                select(CapacitorBankTelemetry)
                .where(CapacitorBankTelemetry.device_id == device_id)
            ).first()
            profile_row = session.exec(
                select(CapacitorBankControlProfile)
                .where(CapacitorBankControlProfile.device_id == device_id)
            ).first()

        self.assertIsNotNone(row)
        self.assertTrue(row.leading_a)
        self.assertTrue(row.temp_alarm)
        self.assertFalse(row.leading_b)
        self.assertEqual(row.circuit_state_phase_a, 0x0F)
        self.assertEqual(row.circuit_state_phase_b, 0x05)
        self.assertAlmostEqual(row.voltage_thd_a, 3.2, places=1)
        self.assertEqual(row.voltage_harmonics_a, [{"order": 5, "value": 6.4}])
        self.assertEqual(row.current_harmonics_b, [{"order": 11, "value": 2.1}])
        self.assertIsNotNone(profile_row)
        self.assertEqual(profile_row.switch_on_power_factor, 95)
        self.assertEqual(profile_row.source, "telemetry")

    def test_persist_device_data_creates_capacitor_bank_protocol_alarms(self):
        ts = datetime(2026, 4, 14, 10, 0, 0)
        with Session(self.engine) as session:
            device = Device(
                name="JKWF 告警柜",
                sn="JKWF-TEST-ALARM",
                device_type="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            device_id = device.id

        payload = dict(RAW_PAYLOAD)
        payload["device_code"] = "JKWF-TEST-ALARM"
        payload["temp"] = 60.0
        payload["jkwf_status"] = 0
        payload["overvoltage_threshold"] = 245.0
        payload["temperature_upper_limit"] = 55.0
        payload["thd_ua"] = 5.0
        payload["thd_ia"] = 3.5
        payload["voltage_a"] = 248.0

        data = apply_field_aliases(payload)
        normalized = normalize_compensation_measurements(data)
        normalized["temperature"] = 60.0
        normalized["voltage_a"] = 248.0
        normalized["voltage_thd_a"] = 5.0
        normalized["current_harmonic_a"] = 3.5
        normalized["temperature_upper_limit"] = 55.0
        normalized["overvoltage_threshold"] = 245.0
        normalized["voltage_harmonic_threshold"] = 4.5
        normalized["current_harmonic_threshold"] = 2.8
        data_dict = {
            "voltage": normalized["voltage"],
            "current": normalized["current"],
            "power": normalized["power"],
            "consumption": 0.0,
            "reactive_power": normalized["reactive_power"],
            "power_factor": normalized["power_factor"],
            "temperature": normalized["temperature"],
        }

        with patch("app.integrations.mqtt.processor.engine", self.engine):
            persist_device_data(device_id, data_dict, ts, raw_data=normalized)

        with Session(self.engine) as session:
            categories = {
                alarm.category
                for alarm in session.exec(select(Alarm).where(Alarm.device_id == device_id)).all()
            }

        self.assertIn("cap_temp_alarm", categories)
        self.assertIn("cap_overvoltage_a", categories)
        self.assertIn("cap_voltage_thd_a", categories)
        self.assertIn("cap_current_thd_a", categories)

    def test_persist_device_data_updates_existing_capacitor_bank_telemetry_on_same_timestamp(self):
        ts = datetime(2026, 4, 14, 10, 0, 0)
        with Session(self.engine) as session:
            device = Device(
                name="JKWF 去重柜",
                sn="JKWF-TEST-DEDUP",
                device_type="capacitor_bank_controller",
                device_category="compensation",
                energy_type="electricity",
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            device_id = device.id

        payload = dict(RAW_PAYLOAD)
        payload["device_code"] = "JKWF-TEST-DEDUP"
        normalized = normalize_compensation_measurements(apply_field_aliases(payload))
        data_dict = {
            "voltage": normalized["voltage"],
            "current": normalized["current"],
            "power": normalized["power"],
            "consumption": 0.0,
            "reactive_power": normalized["reactive_power"],
            "power_factor": normalized["power_factor"],
            "temperature": normalized["temperature"],
        }

        with patch("app.integrations.mqtt.processor.engine", self.engine):
            persist_device_data(device_id, data_dict, ts, raw_data=normalized)

            normalized_second = dict(normalized)
            normalized_second["temperature"] = 48.6
            normalized_second["frequency"] = 49.92
            persist_device_data(device_id, data_dict, ts, raw_data=normalized_second)

        with Session(self.engine) as session:
            rows = session.exec(
                select(CapacitorBankTelemetry)
                .where(CapacitorBankTelemetry.device_id == device_id)
            ).all()

        self.assertEqual(len(rows), 1)
        self.assertAlmostEqual(rows[0].temperature, 48.6, places=1)
        self.assertAlmostEqual(rows[0].frequency, 49.92, places=2)


if __name__ == "__main__":
    unittest.main()
