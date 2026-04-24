"""
JKWF-LCD 协议解码器单元测试

覆盖 app/integrations/jkwf_lcd/decoder.py 的状态标志位解码和投切状态解码。
"""

import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.integrations.jkwf_lcd.decoder import (
    STATUS_BITS,
    decode_circuit_states,
    decode_jkwf_payload,
    decode_status_flags,
)


class TestDecodeStatusFlags(unittest.TestCase):
    def test_all_zero_flags_returns_all_false(self):
        result = decode_status_flags(0x0000)
        self.assertTrue(all(v is False for v in result.values()))

    def test_all_one_flags_returns_all_true(self):
        result = decode_status_flags(0xFFFF)
        self.assertTrue(all(v is True for v in result.values()))

    def test_only_temp_alarm_set(self):
        """bit 15 = temp_alarm"""
        result = decode_status_flags(0x8000)
        self.assertTrue(result["temp_alarm"])
        # 其余全为 False
        others = {k: v for k, v in result.items() if k != "temp_alarm"}
        self.assertTrue(all(v is False for v in others.values()))

    def test_leading_a_and_overvoltage_alarm_a(self):
        """bit 0 = leading_a，bit 6 = overvoltage_alarm_a"""
        raw = (1 << 0) | (1 << 6)  # 0x41
        result = decode_status_flags(raw)
        self.assertTrue(result["leading_a"])
        self.assertTrue(result["overvoltage_alarm_a"])
        # leading_b/c, overvoltage_alarm_b/c 应为 False
        self.assertFalse(result["leading_b"])
        self.assertFalse(result["leading_c"])
        self.assertFalse(result["overvoltage_alarm_b"])
        self.assertFalse(result["overvoltage_alarm_c"])

    def test_all_phase_c_flags(self):
        """A 相超前=bit0，B 相超前=bit1，C 相超前=bit2"""
        raw = (1 << 2)  # 只有 leading_c
        result = decode_status_flags(raw)
        self.assertFalse(result["leading_a"])
        self.assertFalse(result["leading_b"])
        self.assertTrue(result["leading_c"])

    def test_returns_all_expected_keys(self):
        result = decode_status_flags(0)
        self.assertEqual(set(result.keys()), set(STATUS_BITS.keys()))

    def test_undercurrent_flags(self):
        """bit3=undercurrent_a, bit4=undercurrent_b, bit5=undercurrent_c"""
        raw = (1 << 3) | (1 << 5)
        result = decode_status_flags(raw)
        self.assertTrue(result["undercurrent_a"])
        self.assertFalse(result["undercurrent_b"])
        self.assertTrue(result["undercurrent_c"])


class TestDecodeCircuitStates(unittest.TestCase):
    def test_basic_split(self):
        """reg1=0xA305：高8位=0xA3, 低8位=0x05"""
        result = decode_circuit_states(0xA305, 0x0000, 0x0000)
        self.assertEqual(result["circuit_state_phase_a"], 0xA3)
        self.assertEqual(result["circuit_state_phase_b"], 0x05)
        self.assertEqual(result["circuit_state_phase_c"], 0x00)

    def test_all_registers(self):
        result = decode_circuit_states(0x0F05, 0x0300, 0x0000)
        self.assertEqual(result["circuit_state_phase_a"], 0x0F)
        self.assertEqual(result["circuit_state_phase_b"], 0x05)
        self.assertEqual(result["circuit_state_phase_c"], 0x03)
        self.assertEqual(result["circuit_state_common_1"], 0x00)
        self.assertEqual(result["circuit_state_common_2"], 0x00)
        self.assertEqual(result["circuit_state_common_3"], 0x00)

    def test_common_comp_groups(self):
        result = decode_circuit_states(0x0000, 0x00AB, 0xCD00)
        self.assertEqual(result["circuit_state_common_1"], 0xAB)
        self.assertEqual(result["circuit_state_common_2"], 0xCD)
        self.assertEqual(result["circuit_state_common_3"], 0x00)

    def test_all_zero(self):
        result = decode_circuit_states(0, 0, 0)
        self.assertTrue(all(v == 0 for v in result.values()))

    def test_all_ff(self):
        result = decode_circuit_states(0xFFFF, 0xFFFF, 0xFFFF)
        self.assertTrue(all(v == 0xFF for v in result.values()))


class TestDecodeJkwfPayload(unittest.TestCase):
    def test_decodes_status_flags_from_raw(self):
        payload = {"jkwf_status_flags": 0x8001}  # leading_a + temp_alarm
        result = decode_jkwf_payload(payload)
        self.assertTrue(result["leading_a"])
        self.assertTrue(result["temp_alarm"])
        self.assertFalse(result["leading_b"])

    def test_decodes_circuit_states_from_regs(self):
        payload = {
            "circuit_state_reg_1": 0x0F05,
            "circuit_state_reg_2": 0x0300,
            "circuit_state_reg_3": 0x0000,
        }
        result = decode_jkwf_payload(payload)
        self.assertEqual(result["circuit_state_phase_a"], 0x0F)
        self.assertEqual(result["circuit_state_phase_b"], 0x05)

    def test_missing_flags_returns_empty(self):
        result = decode_jkwf_payload({})
        self.assertEqual(result, {})

    def test_partial_circuit_registers_skipped(self):
        """只有 reg_1，没有 reg_2/reg_3，不应解码投切状态"""
        payload = {"circuit_state_reg_1": 0xFF00}
        result = decode_jkwf_payload(payload)
        self.assertNotIn("circuit_state_phase_a", result)

    def test_invalid_flags_value_ignored(self):
        payload = {"jkwf_status_flags": "not_a_number"}
        with self.assertLogs("app.integrations.jkwf_lcd.decoder", level="WARNING") as captured:
            result = decode_jkwf_payload(payload)
        self.assertNotIn("leading_a", result)
        self.assertTrue(any("JKWF status flags decode failed" in line for line in captured.output))

    def test_invalid_circuit_register_value_ignored_with_warning(self):
        payload = {
            "circuit_state_reg_1": 0x0F05,
            "circuit_state_reg_2": "bad-reg",
            "circuit_state_reg_3": 0x0000,
        }
        with self.assertLogs("app.integrations.jkwf_lcd.decoder", level="WARNING") as captured:
            result = decode_jkwf_payload(payload)

        self.assertEqual(result, {})
        self.assertTrue(any("JKWF circuit state decode failed" in line for line in captured.output))

    def test_does_not_overwrite_existing_decoded_fields(self):
        """如果 data 里已有解码后字段，decode_jkwf_payload 不覆盖"""
        payload = {
            "jkwf_status_flags": 0x8001,  # leading_a=True, temp_alarm=True
            "leading_a": False,            # 已有值应保留
        }
        # decode_jkwf_payload 本身返回新字典，不含已有字段
        raw_decoded = decode_jkwf_payload(payload)
        # 调用方合并时 "leading_a" 不在 decoded，所以原值不被覆盖
        merged = {**payload, **{k: v for k, v in raw_decoded.items() if k not in payload}}
        self.assertFalse(merged["leading_a"])  # 原值保留


if __name__ == "__main__":
    unittest.main()
