import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.domain.energy_rules import (
    calculate_period_delta,
    calculate_energy_cost,
    calculate_manual_carbon,
    get_energy_semantics,
    get_electricity_price,
    parse_hour_ranges,
    summarize_carbon_by_energy_type,
    summarize_energy_statistics,
)


class TestEnergyDomainRules(unittest.TestCase):
    def test_parse_hour_ranges_ignores_invalid_segments(self):
        self.assertEqual(parse_hour_ranges("8-12, bad, 18-23"), [(8, 12), (18, 23)])

    @patch("app.domain.energy_rules.settings")
    def test_get_electricity_price_uses_peak_flat_valley(self, mock_settings):
        mock_settings.electricity_peak_hours = "8-12"
        mock_settings.electricity_flat_hours = "12-18"
        mock_settings.peak_price = 1.2
        mock_settings.flat_price = 0.8
        mock_settings.valley_price = 0.4

        self.assertEqual(get_electricity_price(9), 1.2)
        self.assertEqual(get_electricity_price(13), 0.8)
        self.assertEqual(get_electricity_price(3), 0.4)

    @patch("app.domain.energy_rules.get_electricity_price", return_value=1.1)
    def test_calculate_energy_cost_for_electricity_uses_time_of_use_price(self, mock_get_price):
        cost = calculate_energy_cost("electricity", 10, datetime(2026, 3, 24, 9, 0, 0))

        self.assertEqual(cost, 11.0)
        mock_get_price.assert_called_once()

    def test_summarize_energy_statistics_handles_empty_input(self):
        result = summarize_energy_statistics([])

        self.assertEqual(result["data_count"], 0)
        self.assertEqual(result["total_consumption"], 0)

    def test_summarize_energy_statistics_calculates_metrics(self):
        rows = [
            SimpleNamespace(timestamp=datetime(2026, 3, 24, 8, 0, 0), energy_type="electricity", consumption=10.0, flow_rate=2.0),
            SimpleNamespace(timestamp=datetime(2026, 3, 24, 9, 0, 0), energy_type="electricity", consumption=14.0, flow_rate=4.0),
            SimpleNamespace(timestamp=datetime(2026, 3, 24, 10, 0, 0), energy_type="electricity", consumption=16.0, flow_rate=None),
        ]

        result = summarize_energy_statistics(rows)

        self.assertEqual(result["total_consumption"], 6.0)
        self.assertEqual(result["avg_consumption"], 2.0)
        self.assertEqual(result["avg_flow_rate"], 3.0)
        self.assertEqual(result["peak_flow_rate"], 4.0)
        self.assertEqual(result["consumption_stat_basis"], "period_delta_from_cumulative_reading")

    def test_summarize_carbon_by_energy_type_builds_units(self):
        result = summarize_carbon_by_energy_type([("water", 1.234, 9.876)])

        self.assertEqual(result["total_carbon"], 1.23)
        self.assertEqual(result["by_energy_type"]["water"]["unit"], "m³")
        self.assertEqual(result["boundary"], "display_estimate")

    def test_calculate_manual_carbon_returns_display_payload(self):
        result = calculate_manual_carbon("water", 10)

        self.assertEqual(result["carbon_factor"], 0.167)
        self.assertEqual(result["carbon_emission"], 1.67)
        self.assertFalse(result["is_accounting_grade"])

    def test_calculate_period_delta_flags_meter_reset(self):
        delta, meter_reset_suspected = calculate_period_delta([
            SimpleNamespace(timestamp=datetime(2026, 3, 24, 8, 0, 0), consumption=20.0),
            SimpleNamespace(timestamp=datetime(2026, 3, 24, 9, 0, 0), consumption=3.0),
        ])

        self.assertEqual(delta, 0.0)
        self.assertTrue(meter_reset_suspected)

    def test_get_energy_semantics_exposes_units_and_labels(self):
        result = get_energy_semantics("heat")

        self.assertEqual(result["label"], "热")
        self.assertEqual(result["consumption_unit"], "GJ")
        self.assertEqual(result["flow_unit"], "GJ/h")


if __name__ == "__main__":
    unittest.main()
