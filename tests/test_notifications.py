import unittest
from unittest.mock import patch

from app.core.notifications import NotificationService


class NotificationServiceTest(unittest.TestCase):
    @patch("app.core.notifications.settings")
    @patch("app.core.notifications.requests.post")
    def test_webhook_notification_sent(self, mock_post, mock_settings):
        mock_settings.alerting_enabled = True
        mock_settings.alerting_project_name = "MineEnergySystem"
        mock_settings.alerting_cooldown_seconds = 0
        mock_settings.alerting_webhook_url = "https://hooks.example.com"
        mock_settings.alerting_email_enabled = False

        service = NotificationService()
        mock_post.return_value.raise_for_status.return_value = None

        service.notify(
            event_key="scheduler:test",
            severity="warning",
            title="Job failed",
            message="A scheduled job failed",
            details={"job_id": "test"},
        )

        mock_post.assert_called_once()

    @patch("app.core.notifications.settings")
    @patch("app.core.notifications.requests.post")
    def test_notification_cooldown_prevents_duplicate_send(self, mock_post, mock_settings):
        mock_settings.alerting_enabled = True
        mock_settings.alerting_project_name = "MineEnergySystem"
        mock_settings.alerting_cooldown_seconds = 3600
        mock_settings.alerting_webhook_url = "https://hooks.example.com"
        mock_settings.alerting_email_enabled = False

        service = NotificationService()
        mock_post.return_value.raise_for_status.return_value = None

        payload = dict(
            event_key="mqtt:connect_failed",
            severity="critical",
            title="MQTT failed",
            message="MQTT failed",
            details={},
        )
        service.notify(**payload)
        service.notify(**payload)

        mock_post.assert_called_once()
