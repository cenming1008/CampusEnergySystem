import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import analysis
from app.api.endpoints.devices import data as device_data


class TestEndpointApplicationConvergence(unittest.TestCase):
    @patch("app.api.endpoints.devices.data.report_device_data_use_case")
    def test_report_device_data_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="admin", role="admin")
        request = SimpleNamespace(
            model_dump=lambda exclude_none=True: {"consumption": 3.2, "power": 1.5},
            timestamp=datetime(2026, 3, 27, 10, 0, 0),
        )
        expected = SimpleNamespace(device_id=1)
        mock_use_case.return_value = expected

        result = device_data.report_device_data(
            device_id=1,
            req=request,
            session=session,
            current_user=current_user,
            _=None,
        )

        self.assertIs(result, expected)
        mock_use_case.assert_called_once_with(
            session=session,
            current_user=current_user,
            device_id=1,
            data={"consumption": 3.2, "power": 1.5},
            timestamp=request.timestamp,
        )

    @patch("app.api.endpoints.analysis.analyze_device_use_case")
    def test_analysis_endpoint_delegates_to_application(self, mock_use_case):
        session = object()
        current_user = SimpleNamespace(username="viewer", role="viewer")
        mock_use_case.return_value = {"device_id": 7, "today_energy": 1.23}

        result = analysis.analyze_device(
            device_id=7,
            session=session,
            current_user=current_user,
        )

        self.assertEqual(result["device_id"], 7)
        mock_use_case.assert_called_once_with(session, current_user, 7)


if __name__ == "__main__":
    unittest.main()
