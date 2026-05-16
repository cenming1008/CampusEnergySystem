"""
Unit tests for replay_mqtt_ingestion_record_use_case.

Coverage:
  1. Record not found → ResourceNotFoundException
  2. Wrong status → ValidationException
  3. Missing raw_payload → ValidationException
  4. Corrupted payload (parse_payload returns None) → ValidationException
  5. Happy path → returns expected dict, side-effects called
"""

import os
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch, call

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.application.telemetry_ingestion import replay_mqtt_ingestion_record_use_case
from app.core.exceptions import ResourceNotFoundException, ValidationException
from app.models.tables import MqttIngestionStatus


def _make_record(**overrides):
    """Return a SimpleNamespace that looks like a valid FAILED MqttIngestionRecord."""
    defaults = dict(
        status=MqttIngestionStatus.FAILED,
        raw_payload='{"device_id": 1, "voltage": 220}',
        topic="campus/device/1/telemetry",
        device_id=1,
        replay_count=0,
        retry_count=2,
    )
    defaults.update(overrides)
    return SimpleNamespace(**defaults)


class TestReplayMqttIngestionRecordUseCase(unittest.TestCase):

    # ------------------------------------------------------------------ #
    # 1. Record not found
    # ------------------------------------------------------------------ #
    @patch("app.application.telemetry_ingestion.MqttReliabilityService")
    def test_record_not_found_raises_resource_not_found(self, mock_svc):
        mock_svc.get_record_by_id.return_value = None
        session = MagicMock()

        with self.assertRaises(ResourceNotFoundException) as ctx:
            replay_mqtt_ingestion_record_use_case(session, record_id=999, operator_username="admin")

        self.assertIn("999", ctx.exception.message)

    # ------------------------------------------------------------------ #
    # 2. Wrong status
    # ------------------------------------------------------------------ #
    @patch("app.application.telemetry_ingestion.MqttReliabilityService")
    def test_wrong_status_raises_validation_exception(self, mock_svc):
        mock_svc.get_record_by_id.return_value = _make_record(
            status=MqttIngestionStatus.SUCCESS
        )
        session = MagicMock()

        with self.assertRaises(ValidationException) as ctx:
            replay_mqtt_ingestion_record_use_case(session, record_id=1, operator_username="admin")

        self.assertIn("仅失败或死信状态的消息允许人工重放", ctx.exception.message)

    # ------------------------------------------------------------------ #
    # 3. Missing raw_payload
    # ------------------------------------------------------------------ #
    @patch("app.application.telemetry_ingestion.MqttReliabilityService")
    def test_missing_raw_payload_raises_validation_exception(self, mock_svc):
        mock_svc.get_record_by_id.return_value = _make_record(raw_payload=None)
        session = MagicMock()

        with self.assertRaises(ValidationException) as ctx:
            replay_mqtt_ingestion_record_use_case(session, record_id=1, operator_username="admin")

        self.assertIn("该消息未保存原始 payload，无法重放", ctx.exception.message)

    # ------------------------------------------------------------------ #
    # 4. Corrupted payload (parse_payload returns None)
    # ------------------------------------------------------------------ #
    @patch("app.integrations.mqtt.processor.parse_payload", return_value=None)
    @patch("app.application.telemetry_ingestion.MqttReliabilityService")
    def test_corrupted_payload_raises_validation_exception(self, mock_svc, _mock_parse):
        mock_svc.get_record_by_id.return_value = _make_record()
        session = MagicMock()

        with self.assertRaises(ValidationException) as ctx:
            replay_mqtt_ingestion_record_use_case(session, record_id=1, operator_username="admin")

        self.assertIn("原始 payload 已损坏，无法重放", ctx.exception.message)

    # ------------------------------------------------------------------ #
    # 5. Success path
    # ------------------------------------------------------------------ #
    @patch("app.application.telemetry_ingestion.audit_log")
    @patch("app.integrations.mqtt.processor.process_payload_dict")
    @patch("app.integrations.mqtt.processor.parse_payload")
    @patch("app.application.telemetry_ingestion.MqttReliabilityService")
    def test_success_path_returns_expected_dict(
        self, mock_svc, mock_parse, mock_process, mock_audit
    ):
        record = _make_record(replay_count=1, retry_count=3)
        mock_svc.get_record_by_id.return_value = record

        parsed = {"device_id": 1, "voltage": 220}
        mock_parse.return_value = parsed

        broadcast_dict = {"device_id": 1, "voltage": 220.0}
        mock_message = MagicMock()
        mock_message.to_dict.return_value = broadcast_dict
        mock_process.return_value = mock_message

        session = MagicMock()

        result = replay_mqtt_ingestion_record_use_case(
            session, record_id=42, operator_username="operator1"
        )

        # --- return value ---
        self.assertEqual(result["record_id"], 42)
        self.assertTrue(result["replayed"])
        self.assertEqual(result["broadcast"], broadcast_dict)

        # --- side-effects ---
        mock_svc.mark_replayed.assert_called_once_with(session, record)
        session.commit.assert_called_once()
        mock_audit.assert_called_once()
        first_positional_arg = mock_audit.call_args[0][0]
        self.assertEqual(first_positional_arg, "mqtt.replay_record")


if __name__ == "__main__":
    unittest.main()
