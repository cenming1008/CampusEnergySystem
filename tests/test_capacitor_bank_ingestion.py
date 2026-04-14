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
    extract_capacitor_bank_telemetry,
    normalize_compensation_measurements,
)
from app.models.tables import CapacitorBankTelemetry, Device


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
                leading_a=True, temp_alarm=True, leading_b=False,
                circuit_state_phase_a=0x0F, circuit_state_phase_b=0x05,
                circuit_state_common_1=0x00,
            )
            session.add(record)
            session.commit()

        with Session(self.engine) as session:
            row = session.exec(
                select(CapacitorBankTelemetry)
                .where(CapacitorBankTelemetry.device_id == device_id)
            ).first()

        self.assertIsNotNone(row)
        self.assertTrue(row.leading_a)
        self.assertTrue(row.temp_alarm)
        self.assertFalse(row.leading_b)
        self.assertEqual(row.circuit_state_phase_a, 0x0F)
        self.assertEqual(row.circuit_state_phase_b, 0x05)
        self.assertAlmostEqual(row.voltage_thd_a, 3.2, places=1)


if __name__ == "__main__":
    unittest.main()
