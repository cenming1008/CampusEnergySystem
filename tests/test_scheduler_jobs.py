import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services import scheduler_jobs


class TestSchedulerJobs(unittest.TestCase):
    @patch("app.services.scheduler_jobs.cleanup_old_data")
    @patch("app.services.scheduler_jobs.logger")
    def test_auto_cleanup_logs_successful_cleanup(self, mock_logger, mock_cleanup_old_data):
        mock_cleanup_old_data.return_value = {"status": "success", "total_deleted": 5}

        scheduler_jobs.auto_cleanup_data()

        mock_logger.info.assert_any_call("开始自动清理过期数据...")
        mock_logger.info.assert_any_call("✅ 自动清理完成：共清理 5 条记录")

    @patch("app.services.scheduler_jobs.cleanup_old_data")
    @patch("app.services.scheduler_jobs.logger")
    def test_auto_cleanup_logs_disabled(self, mock_logger, mock_cleanup_old_data):
        mock_cleanup_old_data.return_value = {"status": "disabled"}

        scheduler_jobs.auto_cleanup_data()

        mock_logger.debug.assert_called_with("自动数据清理已禁用")

    @patch("app.services.scheduler_jobs.logger")
    def test_auto_update_forecasts_skips_when_forecast_unavailable(self, mock_logger):
        with patch.object(scheduler_jobs, "FORECAST_AVAILABLE", False):
            scheduler_jobs.auto_update_forecasts()

        mock_logger.warning.assert_called_with("预测模块不可用，跳过自动更新")

    @patch("app.services.scheduler_jobs.logger")
    def test_auto_train_lstm_skips_when_lstm_unavailable(self, mock_logger):
        with patch.object(scheduler_jobs, "LSTM_AVAILABLE", False):
            scheduler_jobs.auto_train_lstm_models()

        mock_logger.warning.assert_called_with("LSTM服务不可用，跳过自动训练")


if __name__ == "__main__":
    unittest.main()
