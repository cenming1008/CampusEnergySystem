import os
import unittest

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.locations import get_location_types


class TestLocationTypes(unittest.TestCase):
    def test_location_types_include_park_hierarchy(self):
        response = get_location_types()
        values = {item["value"] for item in response["data"]}

        self.assertIn("park", values)
        self.assertIn("campus", values)
        self.assertIn("site", values)


if __name__ == "__main__":
    unittest.main()
