import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.core.settings import Settings
from app.services import mqtt_publisher


class _FakePublishInfo:
    def wait_for_publish(self, timeout=None):
        self.timeout = timeout


class _FakePublisher:
    def __init__(self):
        self.published = []

    def publish(self, topic, payload, qos=0):
        self.published.append((topic, payload, qos))
        return _FakePublishInfo()


class TestMqttContracts(unittest.TestCase):
    def test_settings_defaults_use_campus_topics(self):
        with patch.dict(os.environ, {"DATABASE_URL": "postgresql://tester:secret@localhost/test_db"}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.mqtt_topic, "campus/telemetry")
        self.assertEqual(settings.mqtt_topic_wildcard, "campus/device/+/telemetry")
        self.assertEqual(settings.mqtt_control_topic_prefix, "campus/control/")

    @patch("app.services.mqtt_publisher._get_publisher")
    def test_publish_control_command_uses_campus_control_prefix(self, mock_get_publisher):
        fake_publisher = _FakePublisher()
        mock_get_publisher.return_value = fake_publisher

        with patch.object(mqtt_publisher.settings, "mqtt_control_topic_prefix", "campus/control/"):
            result = mqtt_publisher.publish_control_command(12, "stop")

        self.assertTrue(result)
        self.assertEqual(len(fake_publisher.published), 1)
        topic, payload, qos = fake_publisher.published[0]
        self.assertEqual(topic, "campus/control/12")
        self.assertEqual(qos, 1)
        self.assertIn('"command": "stop"', payload)


if __name__ == "__main__":
    unittest.main()
