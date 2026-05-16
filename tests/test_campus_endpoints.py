import os
import unittest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import HTTPException
from sqlmodel import Session, SQLModel, create_engine

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints import campus
from app.application import campus as campus_application
from app.models.tables import Device, EnergyData, Location
from app.services.campus_service import CampusService


class TestCampusEndpoints(unittest.TestCase):
    def test_get_campus_overview_delegates_to_application(self):
        fake_user = SimpleNamespace(role="admin")
        fake_session = object()
        fake_payload = {"campus_entities": []}
        start_time = datetime(2026, 3, 1, 0, 0, 0)
        end_time = datetime(2026, 3, 2, 0, 0, 0)

        with patch.object(campus, "get_campus_overview_use_case", return_value=fake_payload) as mock_use_case:
            result = campus.get_campus_overview(
                start_time=start_time,
                end_time=end_time,
                session=fake_session,
                current_user=fake_user,
            )

        self.assertIs(result, fake_payload)
        mock_use_case.assert_called_once_with(
            session=fake_session,
            current_user=fake_user,
            start_time=start_time,
            end_time=end_time,
        )

    def test_get_alarm_summary_delegates_to_application(self):
        fake_user = SimpleNamespace(role="admin")
        fake_session = object()
        fake_payload = {
            "time_window": {
                "start_time": datetime(2026, 3, 1, 0, 0, 0),
                "end_time": datetime(2026, 3, 2, 0, 0, 0),
            },
            "total_count": 0,
            "unresolved_count": 0,
            "resolved_count": 0,
            "by_severity": {},
            "top_locations": [],
            "latest": [],
        }

        with patch.object(campus, "get_alarm_summary_use_case", return_value=fake_payload) as mock_use_case:
            result = campus.get_alarm_summary(
                start_time=None,
                end_time=datetime(2026, 3, 2, 0, 0, 0),
                session=fake_session,
                current_user=fake_user,
            )

        self.assertEqual(result["total_count"], 0)
        mock_use_case.assert_called_once_with(
            session=fake_session,
            current_user=fake_user,
            start_time=None,
            end_time=datetime(2026, 3, 2, 0, 0, 0),
        )

    def test_get_energy_category_share_returns_400_for_invalid_window(self):
        fake_user = SimpleNamespace(role="admin")

        with self.assertRaises(HTTPException) as ctx:
            campus.get_energy_category_share(
                start_time=datetime(2026, 3, 2, 0, 0, 0),
                end_time=datetime(2026, 3, 1, 0, 0, 0),
                session=object(),
                current_user=fake_user,
            )

        self.assertEqual(ctx.exception.status_code, 400)
        self.assertEqual(ctx.exception.detail, "start_time 不能晚于 end_time")


class TestCampusApplicationUseCases(unittest.TestCase):
    def test_overview_use_case_resolves_window_scope_and_calls_service(self):
        session = object()
        current_user = SimpleNamespace(role="admin")
        start_time = datetime(2026, 3, 1, 0, 0, 0)
        end_time = datetime(2026, 3, 2, 0, 0, 0)
        payload = {"campus_entities": []}

        with patch.object(campus_application, "get_allowed_device_ids", return_value={1, 2}) as mock_allowed:
            with patch.object(
                campus_application.CampusService,
                "normalize_time_window",
                return_value=(start_time, end_time),
            ) as mock_window:
                with patch.object(
                    campus_application.CampusService,
                    "get_campus_overview",
                    return_value=payload,
                ) as mock_service:
                    result = campus_application.get_campus_overview_use_case(
                        session=session,
                        current_user=current_user,
                        start_time=None,
                        end_time=end_time,
                    )

        self.assertIs(result, payload)
        mock_window.assert_called_once_with(None, end_time, 24)
        mock_allowed.assert_called_once_with(session, current_user)
        mock_service.assert_called_once_with(
            session=session,
            start_time=start_time,
            end_time=end_time,
            allowed_device_ids={1, 2},
        )

    def test_energy_category_use_case_raises_value_error_for_invalid_window(self):
        with self.assertRaisesRegex(ValueError, "start_time 不能晚于 end_time"):
            campus_application.get_energy_category_share_use_case(
                session=object(),
                current_user=SimpleNamespace(role="admin"),
                start_time=datetime(2026, 3, 2, 0, 0, 0),
                end_time=datetime(2026, 3, 1, 0, 0, 0),
            )


class TestCampusServiceStatistics(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_energy_category_summary_uses_period_delta_not_cumulative_sum(self):
        with Session(self.engine) as session:
            location = Location(name="A栋", location_type="building")
            session.add(location)
            session.commit()
            session.refresh(location)
            device = Device(
                name="A栋总表",
                sn="MTR-A",
                device_type="electric_meter",
                device_category="load",
                energy_type="electricity",
                location_id=location.id,
            )
            session.add(device)
            session.commit()
            session.refresh(device)
            session.add(
                EnergyData(
                    device_id=device.id,
                    timestamp=datetime(2026, 3, 1, 0, 0, 0),
                    energy_type="electricity",
                    consumption=100,
                    flow_rate=10,
                )
            )
            session.add(
                EnergyData(
                    device_id=device.id,
                    timestamp=datetime(2026, 3, 1, 1, 0, 0),
                    energy_type="electricity",
                    consumption=130,
                    flow_rate=20,
                )
            )
            session.commit()

            result = CampusService.get_energy_category_share(
                session=session,
                start_time=datetime(2026, 3, 1, 0, 0, 0),
                end_time=datetime(2026, 3, 1, 1, 0, 0),
            )

        self.assertEqual(result["items"][0]["total_consumption"], 30.0)
        self.assertEqual(result["items"][0]["avg_load"], 15.0)

    def test_location_rankings_use_period_delta_and_meter_reset_never_goes_negative(self):
        with Session(self.engine) as session:
            area = Location(name="一区", location_type="area")
            building = Location(name="A栋", location_type="building")
            session.add(area)
            session.add(building)
            session.commit()
            session.refresh(area)
            session.refresh(building)
            building.parent_id = area.id
            electricity = Device(
                name="A栋电表",
                sn="ELE-A",
                device_type="electric_meter",
                device_category="load",
                energy_type="electricity",
                location_id=building.id,
            )
            water = Device(
                name="A栋水表",
                sn="WTR-A",
                device_type="water_meter",
                device_category="water_meter",
                energy_type="water",
                location_id=building.id,
            )
            session.add(electricity)
            session.add(water)
            session.commit()
            session.refresh(electricity)
            session.refresh(water)
            rows = [
                EnergyData(
                    device_id=electricity.id,
                    timestamp=datetime(2026, 3, 1, 0, 0, 0),
                    energy_type="electricity",
                    consumption=200,
                    flow_rate=30,
                ),
                EnergyData(
                    device_id=electricity.id,
                    timestamp=datetime(2026, 3, 1, 1, 0, 0),
                    energy_type="electricity",
                    consumption=260,
                    flow_rate=50,
                ),
                EnergyData(
                    device_id=water.id,
                    timestamp=datetime(2026, 3, 1, 0, 0, 0),
                    energy_type="water",
                    consumption=80,
                    flow_rate=3,
                ),
                EnergyData(
                    device_id=water.id,
                    timestamp=datetime(2026, 3, 1, 1, 0, 0),
                    energy_type="water",
                    consumption=70,
                    flow_rate=5,
                ),
            ]
            session.add_all(rows)
            session.commit()

            overview = CampusService.get_campus_overview(
                session=session,
                start_time=datetime(2026, 3, 1, 0, 0, 0),
                end_time=datetime(2026, 3, 1, 1, 0, 0),
            )

        self.assertEqual(overview["analysis_summary"]["total_consumption"], 60.0)
        self.assertEqual(overview["location_rankings"]["areas"][0]["total_consumption"], 60.0)
        self.assertEqual(overview["location_rankings"]["buildings"][0]["total_consumption"], 60.0)
        self.assertEqual(overview["subitem_statistics"][0]["total_consumption"], 60.0)
        self.assertEqual(
            overview["energy_category_summary"],
            [
                {
                    "energy_category": "electricity",
                    "label": "电",
                    "total_consumption": 60.0,
                    "avg_load": 40.0,
                    "ratio": 1.0,
                    "estimated_carbon": 47.1,
                },
                {
                    "energy_category": "water",
                    "label": "水",
                    "total_consumption": 0.0,
                    "avg_load": 4.0,
                    "ratio": 0.0,
                    "estimated_carbon": 0.0,
                },
            ],
        )


if __name__ == "__main__":
    unittest.main()
