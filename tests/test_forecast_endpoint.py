import os
import unittest
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from fastapi import HTTPException

from app.api.endpoints import forecast
from app.api.endpoints.forecast import basic as forecast_basic
from app.api.endpoints.forecast import shared as forecast_shared


class FakeExecResult:
    def __init__(self, rows):
        self._rows = rows

    def all(self):
        return self._rows


class FakeSession:
    def __init__(self, rows):
        self._rows = rows

    def exec(self, statement):
        return FakeExecResult(self._rows)


class TestForecastEndpointHelpers(unittest.TestCase):
    def test_validate_prediction_type_normalizes_case(self):
        self.assertEqual(forecast._validate_prediction_type("LOAD"), "load")

    def test_validate_prediction_type_rejects_invalid_value(self):
        with self.assertRaises(HTTPException) as ctx:
            forecast._validate_prediction_type("steam")

        self.assertEqual(ctx.exception.status_code, 400)

    @patch.object(forecast_shared, "FORECAST_AVAILABLE", False)
    def test_get_forecast_adapter_requires_forecast_module(self):
        with self.assertRaises(HTTPException) as ctx:
            forecast._get_forecast_adapter()

        self.assertEqual(ctx.exception.status_code, 503)

    def test_get_prediction_accuracy_uses_application_use_case(self):
        with patch.object(
            forecast_basic,
            "evaluate_prediction_accuracy_use_case",
            return_value={
                "prediction_type": "load",
                "count": 3,
                "mae": 1.2,
                "mape": 2.5,
                "rmse": 1.5,
            },
        ):
            result = forecast.get_prediction_accuracy("load", device_id=1, days=7, session=object())

        self.assertTrue(result["success"])
        self.assertEqual(result["data"]["count"], 3)


class TestForecastAdapterAccuracy(unittest.TestCase):
    def test_evaluate_prediction_accuracy_returns_metrics(self):
        from app.services.forecast_adapter import ForecastAdapter

        adapter = ForecastAdapter.__new__(ForecastAdapter)
        now = datetime.now()
        rows = [
            SimpleNamespace(
                prediction_type="load",
                device_id=1,
                predicted_value=10.0,
                actual_value=8.0,
                created_at=now - timedelta(days=1),
            ),
            SimpleNamespace(
                prediction_type="load",
                device_id=1,
                predicted_value=14.0,
                actual_value=16.0,
                created_at=now - timedelta(days=2),
            ),
        ]

        result = adapter.evaluate_prediction_accuracy(FakeSession(rows), "load", device_id=1, days=7)

        self.assertEqual(result["count"], 2)
        self.assertEqual(result["mae"], 2.0)
        self.assertEqual(result["rmse"], 2.0)
        self.assertEqual(result["mape"], 18.75)

    def test_evaluate_prediction_accuracy_returns_empty_metrics_without_data(self):
        from app.services.forecast_adapter import ForecastAdapter

        adapter = ForecastAdapter.__new__(ForecastAdapter)

        result = adapter.evaluate_prediction_accuracy(FakeSession([]), "solar", device_id=None, days=7)

        self.assertEqual(result["count"], 0)
        self.assertIsNone(result["mae"])
        self.assertIsNone(result["mape"])
        self.assertIsNone(result["rmse"])


if __name__ == "__main__":
    unittest.main()
