"""
JKWF-LCD 字段别名单元测试

验证 MQTT Processor 的 FIELD_ALIASES 已正确映射 JKWF-LCD 网关字段。
"""

import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.integrations.mqtt.processor import apply_field_aliases


class TestJkwfLcdFieldAliases(unittest.TestCase):
    # ── 视在功率 ────────────────────────────────────────────────────────────────

    def test_s_a_maps_to_apparent_power_a(self):
        result = apply_field_aliases({"s_a": 24.0})
        self.assertEqual(result["apparent_power_a"], 24.0)

    def test_s_b_maps_to_apparent_power_b(self):
        result = apply_field_aliases({"s_b": 23.0})
        self.assertEqual(result["apparent_power_b"], 23.0)

    def test_s_c_maps_to_apparent_power_c(self):
        result = apply_field_aliases({"s_c": 25.0})
        self.assertEqual(result["apparent_power_c"], 25.0)

    # ── 电压 THD ────────────────────────────────────────────────────────────────

    def test_thd_ua_maps_to_voltage_thd_a(self):
        result = apply_field_aliases({"thd_ua": 32})
        self.assertEqual(result["voltage_thd_a"], 32)

    def test_thd_va_maps_to_voltage_thd_a(self):
        result = apply_field_aliases({"thd_va": 31})
        self.assertEqual(result["voltage_thd_a"], 31)

    def test_thd_ub_maps_to_voltage_thd_b(self):
        result = apply_field_aliases({"thd_ub": 30})
        self.assertEqual(result["voltage_thd_b"], 30)

    def test_thd_vc_maps_to_voltage_thd_c(self):
        result = apply_field_aliases({"thd_vc": 29})
        self.assertEqual(result["voltage_thd_c"], 29)

    # ── 谐波电流幅值 ─────────────────────────────────────────────────────────────

    def test_thd_ia_maps_to_current_harmonic_a(self):
        result = apply_field_aliases({"thd_ia": 15})
        self.assertEqual(result["current_harmonic_a"], 15)

    def test_thd_ib_maps_to_current_harmonic_b(self):
        result = apply_field_aliases({"thd_ib": 14})
        self.assertEqual(result["current_harmonic_b"], 14)

    def test_thd_ic_maps_to_current_harmonic_c(self):
        result = apply_field_aliases({"thd_ic": 16})
        self.assertEqual(result["current_harmonic_c"], 16)

    # ── 状态标志位寄存器 ───────────────────────────────────────────────────────

    def test_jkwf_status_maps_to_jkwf_status_flags(self):
        result = apply_field_aliases({"jkwf_status": 0x8001})
        self.assertEqual(result["jkwf_status_flags"], 0x8001)

    # ── 投切状态寄存器 ──────────────────────────────────────────────────────────

    def test_circuit_state_1_maps_to_circuit_state_reg_1(self):
        result = apply_field_aliases({"circuit_state_1": 0x0F05})
        self.assertEqual(result["circuit_state_reg_1"], 0x0F05)

    def test_circuit_state_2_maps_to_circuit_state_reg_2(self):
        result = apply_field_aliases({"circuit_state_2": 0x0300})
        self.assertEqual(result["circuit_state_reg_2"], 0x0300)

    def test_circuit_state_3_maps_to_circuit_state_reg_3(self):
        result = apply_field_aliases({"circuit_state_3": 0x0000})
        self.assertEqual(result["circuit_state_reg_3"], 0x0000)

    # ── 别名不覆盖已有规范字段 ─────────────────────────────────────────────────

    def test_alias_does_not_override_existing_canonical_field(self):
        """若 apparent_power_a 已存在，s_a 别名不应覆盖"""
        result = apply_field_aliases({"s_a": 99.0, "apparent_power_a": 24.0})
        self.assertEqual(result["apparent_power_a"], 24.0)

    def test_alias_does_not_override_voltage_thd(self):
        result = apply_field_aliases({"thd_ua": 99, "voltage_thd_a": 32})
        self.assertEqual(result["voltage_thd_a"], 32)

    # ── 完整 JKWF-LCD payload 别名批量映射 ────────────────────────────────────

    def test_full_jkwf_payload_aliases(self):
        raw = {
            "s_a": 24.0, "s_b": 23.0, "s_c": 25.0,
            "thd_ua": 32, "thd_ub": 30, "thd_uc": 31,
            "thd_ia": 15, "thd_ib": 14, "thd_ic": 16,
            "jkwf_status": 0x8001,
            "circuit_state_1": 0x0F05,
            "circuit_state_2": 0x0300,
            "circuit_state_3": 0x0000,
        }
        result = apply_field_aliases(raw)
        self.assertEqual(result["apparent_power_a"], 24.0)
        self.assertEqual(result["apparent_power_b"], 23.0)
        self.assertEqual(result["apparent_power_c"], 25.0)
        self.assertEqual(result["voltage_thd_a"], 32)
        self.assertEqual(result["voltage_thd_b"], 30)
        self.assertEqual(result["voltage_thd_c"], 31)
        self.assertEqual(result["current_harmonic_a"], 15)
        self.assertEqual(result["current_harmonic_b"], 14)
        self.assertEqual(result["current_harmonic_c"], 16)
        self.assertEqual(result["jkwf_status_flags"], 0x8001)
        self.assertEqual(result["circuit_state_reg_1"], 0x0F05)
        self.assertEqual(result["circuit_state_reg_2"], 0x0300)
        self.assertEqual(result["circuit_state_reg_3"], 0x0000)


if __name__ == "__main__":
    unittest.main()
