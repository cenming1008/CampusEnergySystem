"""
统一安全响应头。
"""

from __future__ import annotations

from app.core.settings import Settings


def build_security_headers(settings: Settings) -> dict[str, str]:
    headers = {
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": settings.security_referrer_policy,
        "Permissions-Policy": settings.security_permissions_policy,
        "Content-Security-Policy": settings.security_content_security_policy,
        "Cross-Origin-Opener-Policy": "same-origin",
        "Cross-Origin-Resource-Policy": "same-origin",
    }

    if settings.force_https or settings.is_production:
        headers["Strict-Transport-Security"] = (
            f"max-age={max(0, settings.security_hsts_seconds)}; includeSubDomains"
        )

    return headers
