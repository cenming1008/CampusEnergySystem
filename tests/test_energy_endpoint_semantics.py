import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.energy import carbon, data


class TestEnergyEndpointSemantics(unittest.TestCase):
    def test_get_energy_types_includes_units_and_semantics(self):
        result = data.get_energy_types()

        electricity = next(item for item in result["energy_types"] if item["value"] == "electricity")
        self.assertEqual(electricity["unit"], "kWh")
        self.assertEqual(electricity["flow_unit"], "kW")
        self.assertEqual(electricity["consumption_semantics"], "cumulative_meter_reading")
        self.assertIn("supported_device_types", electricity)
        self.assertEqual(result["device_object_boundary"], "Device 仍是统一对象；meter/point 语义本轮通过 device_type registry 和接口元信息兼容表达。")

    @patch("app.api.endpoints.energy.data.EnergyService.get_carbon_summary")
    @patch("app.api.endpoints.energy.data.EnergyService.get_statistics_by_type")
    @patch("app.api.endpoints.energy.data.get_allowed_device_ids", return_value=None)
    def test_get_energy_overview_returns_boundary_metadata(
        self,
        mock_allowed_ids,
        mock_statistics,
        mock_carbon_summary,
    ):
        mock_statistics.return_value = {"electricity": {"total_consumption": 5.0, "data_count": 2}}
        mock_carbon_summary.return_value = {"total_carbon": 2.3, "by_energy_type": {}}

        result = data.get_energy_overview(
            start_time=datetime(2026, 3, 1),
            end_time=datetime(2026, 3, 2),
            device_id=None,
            location_id=None,
            energy_type=None,
            top_n=5,
            include_analysis=False,
            session=object(),
            current_user=SimpleNamespace(role="admin", username="admin"),
        )

        self.assertEqual(result["overview_boundary"], "multi_energy_first_batch")
        self.assertFalse(result["cross_energy_mix_allowed"])
        self.assertIn("field_boundary_rule", result)
        self.assertNotIn("summary", result)

    def test_get_carbon_factors_marks_display_boundary(self):
        result = carbon.get_carbon_factors()

        self.assertEqual(result["carbon_factors"]["electricity"]["boundary"], "display_estimate")
        self.assertIn("展示级估算", result["description"])


if __name__ == "__main__":
    unittest.main()
