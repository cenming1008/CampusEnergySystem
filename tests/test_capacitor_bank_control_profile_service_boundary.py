import json
import unittest
from datetime import datetime, timedelta

from sqlmodel import Session, SQLModel, create_engine

from app.models.tables import CapacitorBankControlProfile
from app.services.devices.compensation.capacitor_bank.control_profile_service import CapacitorBankControlProfileService


class TestCapacitorBankControlProfileServiceBoundary(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        SQLModel.metadata.create_all(self.engine)

    def test_profile_upsert_source_status_and_capacity_expansion_live_in_profile_layer(self):
        now = datetime.now()
        with Session(self.engine) as session:
            profile = CapacitorBankControlProfileService.upsert_control_profile(
                session,
                16,
                {
                    "source": "ignored",
                    "switch_on_power_factor": 95,
                    "phase_a_capacity_steps_kvar_json": [12.0, 24.0],
                    "common_1_capacity_steps_kvar_json": [30.0, 60.0],
                },
                snapshot_timestamp=now,
                source="telemetry",
            )
            session.commit()
            session.refresh(profile)

            loaded = CapacitorBankControlProfileService.get_control_profile(session, 16)

        self.assertIsNotNone(loaded)
        self.assertEqual(loaded.switch_on_power_factor, 95)
        self.assertEqual(loaded.source, "telemetry")
        self.assertEqual(loaded.snapshot_timestamp, now)
        self.assertEqual(CapacitorBankControlProfileService.get_profile_source_status(loaded), "fresh")

        payload = CapacitorBankControlProfileService.build_capacity_expansion_payload(loaded)
        self.assertEqual(payload["phase_a_capacity_steps_kvar"], [12.0, 24.0])
        self.assertEqual(payload["common_capacity_expansion"]["common_1_groups"], [30.0, 60.0])

    def test_profile_source_status_detects_empty_unknown_and_stale(self):
        unknown_profile = CapacitorBankControlProfile(device_id=16, updated_at=None)
        stale_profile = CapacitorBankControlProfile(
            device_id=17,
            source="telemetry",
            snapshot_timestamp=datetime.now() - timedelta(hours=2),
        )
        direct_profile = CapacitorBankControlProfile(
            device_id=18,
            phase_b_capacity_steps_kvar_json=json.dumps([48.0, 12.0]),
        )

        self.assertEqual(CapacitorBankControlProfileService.get_profile_source_status(None), "empty")
        self.assertEqual(CapacitorBankControlProfileService.get_profile_source_status(unknown_profile), "unknown")
        self.assertEqual(CapacitorBankControlProfileService.get_profile_source_status(stale_profile), "stale")
        self.assertEqual(
            CapacitorBankControlProfileService.build_direct_capacity_steps_payload(direct_profile)["phase_b_capacity_steps_kvar"],
            [48.0, 12.0],
        )


if __name__ == "__main__":
    unittest.main()
