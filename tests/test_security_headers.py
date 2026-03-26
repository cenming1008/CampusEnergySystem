import unittest
from types import SimpleNamespace

from app.core.security_headers import build_security_headers


class SecurityHeadersTest(unittest.TestCase):
    def test_build_security_headers_includes_transport_header_for_production(self):
        settings = SimpleNamespace(
            security_referrer_policy="strict-origin-when-cross-origin",
            security_permissions_policy="geolocation=()",
            security_content_security_policy="default-src 'self'",
            force_https=False,
            is_production=True,
            security_hsts_seconds=31536000,
        )

        headers = build_security_headers(settings)

        self.assertEqual(headers["X-Frame-Options"], "DENY")
        self.assertIn("Strict-Transport-Security", headers)

    def test_build_security_headers_skips_hsts_for_non_tls_dev(self):
        settings = SimpleNamespace(
            security_referrer_policy="strict-origin-when-cross-origin",
            security_permissions_policy="geolocation=()",
            security_content_security_policy="default-src 'self'",
            force_https=False,
            is_production=False,
            security_hsts_seconds=31536000,
        )

        headers = build_security_headers(settings)

        self.assertNotIn("Strict-Transport-Security", headers)
