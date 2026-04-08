import unittest

from app.core.metrics import observe_http_request, render_metrics


class MetricsTest(unittest.TestCase):
    def test_metrics_render_contains_http_series(self):
        observe_http_request("GET", "/health", 200, 0.05)
        payload, content_type = render_metrics()

        self.assertEqual(content_type.split(";")[0], "text/plain")
        text = payload.decode("utf-8")
        self.assertIn("campus_http_requests_total", text)
        self.assertIn('path="/health"', text)
