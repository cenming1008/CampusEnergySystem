import unittest

from scripts.python.evaluate_capacity_baseline import evaluate_report


class CapacityBaselineEvaluationTest(unittest.TestCase):
    def test_report_passes_when_thresholds_are_met(self):
        report = {
            "requests_per_second": 52.4,
            "success_rate": 100.0,
            "failed_requests": 0,
            "status_codes": {"200": 120},
            "latency_ms": {"p95": 88.2},
        }

        passed, findings = evaluate_report(
            report,
            min_rps=40,
            max_p95_ms=120,
            min_success_rate=99,
            max_failed_requests=0,
            expected_status_codes=["200"],
        )

        self.assertTrue(passed)
        self.assertEqual(findings, [])

    def test_report_fails_when_thresholds_are_missed(self):
        report = {
            "requests_per_second": 8.0,
            "success_rate": 95.0,
            "failed_requests": 3,
            "status_codes": {"200": 97, "500": 3},
            "latency_ms": {"p95": 420.0},
        }

        passed, findings = evaluate_report(
            report,
            min_rps=10,
            max_p95_ms=200,
            min_success_rate=99,
            max_failed_requests=0,
            expected_status_codes=["200"],
        )

        self.assertFalse(passed)
        self.assertGreaterEqual(len(findings), 4)


if __name__ == "__main__":
    unittest.main()
