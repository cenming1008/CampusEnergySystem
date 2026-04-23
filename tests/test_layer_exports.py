import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app import application, domain, repositories, services


class TestLayerExports(unittest.TestCase):
    def test_application_exports_key_use_cases(self):
        self.assertTrue(callable(application.report_device_data_use_case))
        self.assertTrue(callable(application.get_device_data_use_case))
        self.assertTrue(callable(application.analyze_device_use_case))
        self.assertTrue(callable(application.ingest_telemetry_use_case))

    def test_domain_exports_key_rules(self):
        self.assertTrue(callable(domain.get_electricity_price))
        self.assertTrue(callable(domain.normalize_device_report_payload))
        self.assertIn("electricity", domain.ENERGY_UNITS)

    def test_repository_exports_key_repositories(self):
        self.assertTrue(hasattr(repositories, "DeviceRepository"))
        self.assertTrue(hasattr(repositories, "EnergyRepository"))
        self.assertTrue(hasattr(repositories, "UserRepository"))

    def test_services_exports_key_services_and_helpers(self):
        self.assertTrue(hasattr(services, "DeviceService"))
        self.assertTrue(hasattr(services, "UserService"))
        self.assertTrue(callable(services.process_payload))
        self.assertTrue(callable(services.auto_cleanup_data))


if __name__ == "__main__":
    unittest.main()
