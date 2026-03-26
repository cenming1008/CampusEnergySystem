"""
运行时告警通知。
"""

from __future__ import annotations

import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage
from threading import Lock
from typing import Any, Optional

import requests

from app.core.logger import logger
from app.core.settings import settings


class NotificationService:
    def __init__(self) -> None:
        self._lock = Lock()
        self._last_sent_at: dict[str, datetime] = {}

    def notify(
        self,
        *,
        event_key: str,
        severity: str,
        title: str,
        message: str,
        details: Optional[dict[str, Any]] = None,
    ) -> bool:
        if not settings.alerting_enabled:
            logger.info("运行时告警未启用，跳过发送")
            return False
        if self._in_cooldown(event_key):
            logger.warning(f"告警通知冷却中，跳过发送: {event_key}")
            return False

        payload = {
            "project": settings.alerting_project_name,
            "severity": severity,
            "title": title,
            "message": message,
            "details": details or {},
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        if not settings.alerting_webhook_url and not settings.alerting_email_enabled:
            logger.warning("未配置任何运行时告警通知通道，跳过发送")
            return False

        sent = False
        if settings.alerting_webhook_url:
            sent = self._send_webhook(payload) or sent

        if settings.alerting_email_enabled:
            sent = self._send_email(payload) or sent

        if sent:
            self._mark_sent(event_key)
        else:
            logger.warning("告警通知未成功送达任何通道")
        return sent

    def _in_cooldown(self, event_key: str) -> bool:
        with self._lock:
            last_sent_at = self._last_sent_at.get(event_key)
        if last_sent_at is None:
            return False
        return datetime.utcnow() - last_sent_at < timedelta(seconds=max(0, settings.alerting_cooldown_seconds))

    def _mark_sent(self, event_key: str) -> None:
        with self._lock:
            self._last_sent_at[event_key] = datetime.utcnow()

    def _send_webhook(self, payload: dict[str, Any]) -> bool:
        try:
            response = requests.post(settings.alerting_webhook_url, json=payload, timeout=5)
            response.raise_for_status()
            logger.info("Webhook 告警发送成功")
            return True
        except Exception as exc:
            logger.warning(f"Webhook 告警发送失败: {exc}")
            return False

    def _send_email(self, payload: dict[str, Any]) -> bool:
        if not settings.alerting_smtp_host or not settings.alerting_email_from or not settings.alerting_email_to:
            logger.warning("邮件告警配置不完整，跳过发送")
            return False

        msg = EmailMessage()
        msg["Subject"] = f"[{payload['severity'].upper()}] {payload['project']} - {payload['title']}"
        msg["From"] = settings.alerting_email_from
        msg["To"] = ", ".join(settings.alerting_email_to)
        msg.set_content(
            "\n".join(
                [
                    f"Project: {payload['project']}",
                    f"Severity: {payload['severity']}",
                    f"Title: {payload['title']}",
                    f"Message: {payload['message']}",
                    f"Timestamp: {payload['timestamp']}",
                    f"Details: {payload['details']}",
                ]
            )
        )

        try:
            with smtplib.SMTP(settings.alerting_smtp_host, settings.alerting_smtp_port, timeout=10) as smtp:
                smtp.starttls()
                if settings.alerting_smtp_username and settings.alerting_smtp_password:
                    smtp.login(settings.alerting_smtp_username, settings.alerting_smtp_password)
                smtp.send_message(msg)
            logger.info("邮件告警发送成功")
            return True
        except Exception as exc:
            logger.warning(f"邮件告警发送失败: {exc}")
            return False


notification_service = NotificationService()
