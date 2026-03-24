import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoint_utils import bad_request_from_value_error, log_endpoint_exception


class TestEndpointUtils(unittest.TestCase):
    def test_bad_request_from_value_error_uses_original_message(self):
        exc = bad_request_from_value_error(ValueError("设备不存在"))

        self.assertEqual(exc.status_code, 400)
        self.assertEqual(exc.detail, "设备不存在")

    @patch("app.api.endpoint_utils.logger")
    def test_log_endpoint_exception_writes_exception_log(self, mock_logger):
        log_endpoint_exception("保存失败 device_id=1", RuntimeError("db down"))

        mock_logger.exception.assert_called_once_with("保存失败 device_id=1: db down")


if __name__ == "__main__":
    unittest.main()
