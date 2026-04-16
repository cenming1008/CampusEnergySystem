import unittest

from app.integrations.jkwf_lcd.capacity import (
    build_common_stage_slot_kvar,
    build_split_phase_slot_kvar,
    expand_capacity_slots,
)


class TestJkwfCapacity(unittest.TestCase):
    def test_expand_capacity_slots_uses_capacity_code_pattern(self):
        slots = expand_capacity_slots("4:1233", 30.0, 12)

        self.assertEqual(slots[:8], [30.0, 60.0, 90.0, 90.0, 30.0, 60.0, 90.0, 90.0])
        self.assertEqual(len(slots), 12)

    def test_build_split_phase_slot_kvar_distributes_from_capacity_code(self):
        split_slots = build_split_phase_slot_kvar("7:1124", 12.0, 8)

        self.assertEqual(split_slots["phase_a_groups"], [12.0, 48.0, 24.0])
        self.assertEqual(split_slots["phase_b_groups"], [12.0, 12.0, 48.0])
        self.assertEqual(split_slots["phase_c_groups"], [24.0, 12.0])

    def test_build_common_stage_slot_kvar_segments_by_protocol_banks(self):
        common_slots = build_common_stage_slot_kvar("4:1233", 30.0, 12)

        self.assertEqual(common_slots["common_1_groups"], [30.0, 60.0, 90.0, 90.0, 30.0, 60.0, 90.0, 90.0])
        self.assertEqual(common_slots["common_2_groups"], [30.0, 60.0, 90.0, 90.0])
        self.assertEqual(common_slots["common_3_groups"], [])


if __name__ == "__main__":
    unittest.main()
