import os
import unittest
from datetime import datetime

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.models.tables import MqttIngestionRecord, MqttIngestionStatus
from app.services.mqtt_reliability_service import MqttReliabilityService


class FakeExecResult:
    def __init__(self, value):
        self._value = value

    def first(self):
        return self._value


class FakeSession:
    def __init__(self, record=None):
        self.record = record
        self.added = []
        self.flushed = False

    def exec(self, _statement):
        return FakeExecResult(self.record)

    def add(self, record):
        self.record = record
        self.added.append(record)

    def flush(self):
        self.flushed = True


class TestMqttReliabilityService(unittest.TestCase):
    def test_claim_message_creates_processing_record_for_new_message(self):
        session = FakeSession()

        record, should_skip = MqttReliabilityService.claim_message(
            session,
            fingerprint="fp-1",
            payload_hash="hash-1",
            raw_payload='{"device_id":7,"power":1.2}',
            device_id=7,
            topic="mine/device/7/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
        )

        self.assertFalse(should_skip)
        self.assertEqual(record.status, MqttIngestionStatus.PROCESSING)
        self.assertEqual(record.duplicate_count, 0)
        self.assertTrue(session.flushed)

    def test_claim_message_skips_existing_successful_record(self):
        existing = MqttIngestionRecord(
            fingerprint="fp-2",
            payload_hash="hash-2",
            device_id=7,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
            status=MqttIngestionStatus.SUCCESS,
        )
        session = FakeSession(existing)

        record, should_skip = MqttReliabilityService.claim_message(
            session,
            fingerprint="fp-2",
            payload_hash="hash-2",
            raw_payload='{"device_id":7,"power":1.2}',
            device_id=7,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
        )

        self.assertTrue(should_skip)
        self.assertEqual(record.duplicate_count, 1)

    def test_mark_failure_updates_status_and_reason(self):
        session = FakeSession()
        record = MqttIngestionRecord(
            fingerprint="fp-3",
            payload_hash="hash-3",
            device_id=9,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
            status=MqttIngestionStatus.PROCESSING,
        )

        MqttReliabilityService.mark_failure(session, record, "bad payload")

        self.assertEqual(record.status, MqttIngestionStatus.FAILED)
        self.assertEqual(record.error_reason, "bad payload")
        self.assertEqual(record.retry_count, 1)
        self.assertIsNotNone(record.next_retry_at)

    def test_mark_failure_moves_record_to_dead_letter_after_max_retries(self):
        session = FakeSession()
        record = MqttIngestionRecord(
            fingerprint="fp-dead",
            payload_hash="hash-dead",
            device_id=9,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
            status=MqttIngestionStatus.FAILED,
            retry_count=2,
        )

        MqttReliabilityService.mark_failure(session, record, "still failing")

        self.assertEqual(record.status, MqttIngestionStatus.DEAD_LETTER)
        self.assertEqual(record.retry_count, 3)
        self.assertIsNone(record.next_retry_at)

    def test_claim_message_persists_raw_payload(self):
        session = FakeSession()

        record, should_skip = MqttReliabilityService.claim_message(
            session,
            fingerprint="fp-raw",
            payload_hash="hash-raw",
            raw_payload='{"device_id":7}',
            device_id=7,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
        )

        self.assertFalse(should_skip)
        self.assertEqual(record.raw_payload, '{"device_id":7}')

    def test_mark_replayed_increments_counter(self):
        session = FakeSession()
        record = MqttIngestionRecord(
            fingerprint="fp-r",
            payload_hash="hash-r",
            device_id=7,
            topic="campus/telemetry",
            telemetry_timestamp=datetime(2026, 3, 25, 10, 0, 0),
            status=MqttIngestionStatus.FAILED,
        )

        MqttReliabilityService.mark_replayed(session, record)

        self.assertEqual(record.replay_count, 1)
        self.assertEqual(record.retry_count, 1)
        self.assertIsNotNone(record.last_replayed_at)


if __name__ == "__main__":
    unittest.main()
