import os
import unittest
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from sqlmodel import Session, SQLModel, create_engine

from app.models.tables import Alarm, Device, DeviceIngestionHealth, EnergyData, Location
from app.services.analysis_service import AnalysisService


class TestAnalysisService(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

        with Session(self.engine) as session:
            campus = Location(id=1, name="智慧园区", code="CAMPUS", location_type="campus")
            north_area = Location(id=2, name="北区", location_type="area", parent_id=1, full_path="智慧园区/北区")
            north_building = Location(
                id=3,
                name="1号楼",
                location_type="building",
                parent_id=2,
                full_path="智慧园区/北区/1号楼",
            )
            south_area = Location(id=4, name="南区", location_type="area", parent_id=1, full_path="智慧园区/南区")
            south_building = Location(
                id=5,
                name="2号楼",
                location_type="building",
                parent_id=4,
                full_path="智慧园区/南区/2号楼",
            )
            session.add(campus)
            session.add(north_area)
            session.add(north_building)
            session.add(south_area)
            session.add(south_building)

            device_1 = Device(
                id=1,
                name="北区主配电",
                sn="D-001",
                device_type="load",
                device_category="load",
                energy_type="electricity",
                location_id=3,
                is_active=True,
            )
            device_2 = Device(
                id=2,
                name="北区生活水表",
                sn="D-002",
                device_type="water_meter",
                device_category="water_meter",
                energy_type="water",
                location_id=3,
                is_active=True,
            )
            device_3 = Device(
                id=3,
                name="南区燃气表",
                sn="D-003",
                device_type="gas_meter",
                device_category="gas_meter",
                energy_type="gas",
                location_id=5,
                is_active=False,
            )
            session.add(device_1)
            session.add(device_2)
            session.add(device_3)

            rows = [
                EnergyData(device_id=1, timestamp=datetime(2026, 3, 25, 0, 0), energy_type="electricity", consumption=40, flow_rate=25),
                EnergyData(device_id=1, timestamp=datetime(2026, 4, 1, 0, 0), energy_type="electricity", consumption=70, flow_rate=30),
                EnergyData(device_id=1, timestamp=datetime(2026, 4, 4, 12, 0), energy_type="electricity", consumption=130, flow_rate=50),
                EnergyData(device_id=1, timestamp=datetime(2026, 4, 8, 0, 0), energy_type="electricity", consumption=160, flow_rate=45),
                EnergyData(device_id=2, timestamp=datetime(2026, 3, 25, 0, 0), energy_type="water", consumption=10, flow_rate=1.5),
                EnergyData(device_id=2, timestamp=datetime(2026, 4, 1, 0, 0), energy_type="water", consumption=20, flow_rate=2),
                EnergyData(device_id=2, timestamp=datetime(2026, 4, 8, 0, 0), energy_type="water", consumption=35, flow_rate=4),
                EnergyData(device_id=3, timestamp=datetime(2026, 3, 25, 0, 0), energy_type="gas", consumption=20, flow_rate=1),
                EnergyData(device_id=3, timestamp=datetime(2026, 4, 1, 0, 0), energy_type="gas", consumption=35, flow_rate=1.2),
                EnergyData(device_id=3, timestamp=datetime(2026, 4, 8, 0, 0), energy_type="gas", consumption=55, flow_rate=3),
            ]
            for row in rows:
                session.add(row)

            session.add(
                DeviceIngestionHealth(
                    device_id=1,
                    last_message_at=datetime(2026, 4, 8, 0, 0),
                    last_success_at=datetime(2026, 4, 8, 0, 0),
                    consecutive_failures=0,
                )
            )
            session.add(
                DeviceIngestionHealth(
                    device_id=2,
                    last_message_at=datetime(2026, 4, 7, 18, 0),
                    last_success_at=datetime(2026, 4, 7, 18, 0),
                    consecutive_failures=0,
                )
            )
            session.add(
                DeviceIngestionHealth(
                    device_id=3,
                    last_message_at=datetime(2026, 4, 7, 23, 30),
                    last_success_at=datetime(2026, 4, 7, 22, 0),
                    last_failure_at=datetime(2026, 4, 7, 23, 30),
                    last_failure_reason="燃气网关连续超时",
                    consecutive_failures=4,
                )
            )
            session.add(
                Alarm(
                    id=1,
                    device_id=1,
                    message="北区主配电功率波动告警",
                    severity="critical",
                    category="threshold",
                    timestamp=datetime(2026, 4, 7, 20, 0),
                    is_resolved=False,
                )
            )
            session.commit()

    def test_get_energy_analysis_overview_returns_first_batch_operational_aggregates(self):
        with Session(self.engine) as session:
            result = AnalysisService.get_energy_analysis_overview(
                session=session,
                start_time=datetime(2026, 4, 1, 0, 0),
                end_time=datetime(2026, 4, 8, 0, 0),
                allowed_device_ids={1, 2, 3},
                top_n=5,
            )

        self.assertEqual(result["time_window"]["granularity"], "day")
        self.assertAlmostEqual(result["summary"]["total_consumption"], 125.0)
        self.assertEqual(result["summary"]["device_count"], 3)
        self.assertEqual(result["summary"]["active_device_count"], 2)
        self.assertEqual(result["comparison"]["period_over_period"]["previous_total_consumption"], 55.0)
        self.assertAlmostEqual(result["comparison"]["period_over_period"]["delta_consumption"], 70.0)
        self.assertEqual(result["comparison"]["energy_categories"][0]["energy_category"], "electricity")
        self.assertEqual(result["ranking"]["areas"][0]["name"], "北区")
        self.assertEqual(result["ranking"]["buildings"][0]["name"], "1号楼")
        self.assertEqual(result["ranking"]["devices"][0]["name"], "北区主配电")
        self.assertEqual(result["anomaly"]["boundary"], "operational_signal_first_batch")
        self.assertEqual(result["anomaly"]["summary"]["active_alarm_count"], 1)
        self.assertGreaterEqual(result["anomaly"]["summary"]["data_gap_count"], 1)
        self.assertGreaterEqual(len(result["trend"]["items"]), 2)
        self.assertGreaterEqual(len(result["insights"]), 2)

    def test_get_energy_analysis_overview_supports_location_scope_filter(self):
        with Session(self.engine) as session:
            result = AnalysisService.get_energy_analysis_overview(
                session=session,
                start_time=datetime(2026, 4, 1, 0, 0),
                end_time=datetime(2026, 4, 8, 0, 0),
                allowed_device_ids={1, 2, 3},
                location_id=4,
                top_n=5,
            )

        self.assertEqual(result["scope"]["location_id"], 4)
        self.assertEqual(result["scope"]["location_type"], "area")
        self.assertAlmostEqual(result["summary"]["total_consumption"], 20.0)
        self.assertEqual(result["ranking"]["areas"][0]["name"], "南区")
        self.assertEqual(result["ranking"]["buildings"][0]["name"], "2号楼")
        self.assertEqual(result["ranking"]["devices"][0]["name"], "南区燃气表")

    def test_get_energy_analysis_overview_supports_explicit_granularity(self):
        with Session(self.engine) as session:
            result = AnalysisService.get_energy_analysis_overview(
                session=session,
                start_time=datetime(2026, 4, 1, 0, 0),
                end_time=datetime(2026, 4, 8, 0, 0),
                allowed_device_ids={1, 2, 3},
                top_n=5,
                granularity="hour",
            )

        self.assertEqual(result["time_window"]["granularity"], "hour")

    def test_get_energy_analysis_overview_intersects_device_and_location_scope(self):
        with Session(self.engine) as session:
            result = AnalysisService.get_energy_analysis_overview(
                session=session,
                start_time=datetime(2026, 4, 1, 0, 0),
                end_time=datetime(2026, 4, 8, 0, 0),
                allowed_device_ids={1, 2, 3},
                location_id=4,
                device_id=1,
                top_n=5,
            )

        self.assertEqual(result["summary"]["total_consumption"], 0.0)
        self.assertEqual(result["ranking"]["areas"], [])
        self.assertEqual(result["ranking"]["buildings"], [])
        self.assertEqual(result["ranking"]["devices"], [])
