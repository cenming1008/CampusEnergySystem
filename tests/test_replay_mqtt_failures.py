import io
import json
import os
import unittest
from contextlib import redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from scripts.python import replay_mqtt_failures


class _FakeSession:
    def commit(self):
        return None


class ReplayMqttFailuresTest(unittest.TestCase):
    def test_replay_record_marks_success_only_when_message_generated(self):
        session = _FakeSession()
        record = SimpleNamespace(id=1, raw_payload='{"device_id": 7}', topic="campus/telemetry")
        refreshed = SimpleNamespace(id=1)

        with patch.object(replay_mqtt_failures, "parse_payload", return_value={"device_id": 7}):
            with patch.object(replay_mqtt_failures, "process_payload_dict", return_value={"type": "telemetry_update"}):
                with patch.object(
                    replay_mqtt_failures.MqttReliabilityService,
                    "get_record_by_id",
                    side_effect=[refreshed, refreshed],
                ):
                    with patch.object(replay_mqtt_failures.MqttReliabilityService, "mark_replayed") as mock_mark_replayed:
                        outcome = replay_mqtt_failures.replay_record(session, record)

        self.assertEqual(outcome, "replayed")
        mock_mark_replayed.assert_called_once_with(session, refreshed)

    def test_replay_record_marks_failure_when_no_event_generated(self):
        session = _FakeSession()
        record = SimpleNamespace(id=2, raw_payload='{"device_id": 8}', topic="campus/telemetry")
        refreshed = SimpleNamespace(id=2)

        with patch.object(replay_mqtt_failures, "parse_payload", return_value={"device_id": 8}):
            with patch.object(replay_mqtt_failures, "process_payload_dict", return_value=None):
                with patch.object(
                    replay_mqtt_failures.MqttReliabilityService,
                    "get_record_by_id",
                    side_effect=[refreshed, refreshed],
                ):
                    with patch.object(replay_mqtt_failures.MqttReliabilityService, "mark_failure") as mock_mark_failure:
                        outcome = replay_mqtt_failures.replay_record(session, record)

        self.assertEqual(outcome, "failed_no_event")
        mock_mark_failure.assert_called_once()

    def test_main_prints_json_summary(self):
        session = _FakeSession()
        records = [
            SimpleNamespace(id=1, raw_payload='{"device_id": 7}', topic="campus/telemetry"),
            SimpleNamespace(id=2, raw_payload=None, topic="campus/telemetry"),
        ]

        class _SessionFactory:
            def __enter__(self_inner):
                return session

            def __exit__(self_inner, exc_type, exc, tb):
                return False

        with patch.object(replay_mqtt_failures, "Session", return_value=_SessionFactory()):
            with patch.object(replay_mqtt_failures, "engine", object()):
                with patch.object(replay_mqtt_failures, "parse_args", return_value=SimpleNamespace(limit=20, device_id=None)):
                    with patch.object(
                        replay_mqtt_failures.MqttReliabilityService,
                        "list_retry_ready_records",
                        return_value=records,
                    ):
                        with patch.object(replay_mqtt_failures, "replay_record", side_effect=["replayed", "skipped_missing_payload"]):
                            stdout = io.StringIO()
                            with redirect_stdout(stdout):
                                exit_code = replay_mqtt_failures.main()

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue().strip())
        self.assertEqual(payload["requested_records"], 2)
        self.assertEqual(payload["replayed_records"], 1)
        self.assertEqual(payload["skipped_records"], 1)


if __name__ == "__main__":
    unittest.main()
