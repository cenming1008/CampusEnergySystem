import os
import unittest
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.services import scheduler_jobs, scheduler_registry
from app.services.devices.storage.control_command_service import StorageControlCommandService


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

    @patch("app.services.scheduler_jobs.CapacitorBankService.expire_pending_control_logs")
    @patch("app.services.scheduler_jobs.Session")
    @patch("app.services.scheduler_jobs.logger")
    def test_expire_compensation_control_timeouts_logs_processed_count(
        self,
        mock_logger,
        mock_session_cls,
        mock_expire_pending,
    ):
        mock_session = mock_session_cls.return_value.__enter__.return_value
        mock_expire_pending.return_value = [object(), object()]

        scheduler_jobs.expire_compensation_control_timeouts()

        mock_logger.info.assert_any_call("开始扫描补偿控制待定日志超时状态...")
        mock_expire_pending.assert_called_once_with(
            mock_session,
            control_event_notifier=scheduler_jobs.CapacitorBankService.publish_control_log_update_event,
        )
        mock_logger.info.assert_any_call("✅ 补偿控制超时收口完成：共更新 2 条控制日志")

    @patch("app.services.scheduler_jobs.StorageControlCommandService.expire_pending_control_logs")
    @patch("app.services.scheduler_jobs.Session")
    @patch("app.services.scheduler_jobs.logger")
    def test_expire_storage_control_timeouts_logs_processed_count(
        self,
        mock_logger,
        mock_session_cls,
        mock_expire_pending,
    ):
        mock_session = mock_session_cls.return_value.__enter__.return_value
        mock_expire_pending.return_value = [object()]

        scheduler_jobs.expire_storage_control_timeouts()

        mock_logger.info.assert_any_call("开始扫描储能控制待定日志超时状态...")
        mock_expire_pending.assert_called_once_with(
            mock_session,
            control_event_notifier=StorageControlCommandService.publish_control_log_update_event,
        )
        mock_logger.info.assert_any_call("✅ 储能控制超时收口完成：共更新 1 条控制日志")

    @patch("app.services.scheduler_jobs.StorageEmsService.evaluate_all")
    @patch("app.services.scheduler_jobs.Session")
    @patch("app.services.scheduler_jobs.logger")
    def test_evaluate_storage_ems_rules_logs_evaluated_and_queued_counts(
        self,
        mock_logger,
        mock_session_cls,
        mock_evaluate_all,
    ):
        mock_session = mock_session_cls.return_value.__enter__.return_value
        mock_evaluate_all.return_value = [{"status": "queued"}, {"status": "skipped"}]

        scheduler_jobs.evaluate_storage_ems_rules()

        mock_evaluate_all.assert_called_once_with(mock_session)
        mock_logger.info.assert_any_call("✅ 储能实时 EMS 完成：评估 2 台设备，下发 1 条命令")

    @patch("app.services.scheduler_jobs.IngestionHealthService.sync_platform_comm_alarms")
    @patch("app.services.scheduler_jobs.Session")
    @patch("app.services.scheduler_jobs.logger")
    def test_sync_platform_comm_alarms_logs_processed_count(
        self,
        mock_logger,
        mock_session_cls,
        mock_sync_platform_comm,
    ):
        mock_session = mock_session_cls.return_value.__enter__.return_value
        mock_sync_platform_comm.return_value = {"created": 1, "recovered": 2, "checked": 3}

        scheduler_jobs.sync_platform_comm_alarms()

        mock_logger.info.assert_any_call("开始扫描平台通讯告警状态...")
        mock_sync_platform_comm.assert_called_once_with(mock_session)
        mock_logger.info.assert_any_call("✅ 平台通讯告警同步完成：检查 3 台设备，新增 1 条，恢复 2 条")

    def test_scheduler_registry_only_registers_cleanup_job(self):
        with patch.object(scheduler_registry.settings, "enable_auto_cleanup", True):
            with patch.object(scheduler_registry.settings, "storage_ems_enabled", False):
                jobs = list(scheduler_registry.get_enabled_job_definitions())

        self.assertEqual(
            [job.id for job in jobs],
            [
                "auto_cleanup_data",
                "expire_compensation_control_timeouts",
                "expire_storage_control_timeouts",
                "sync_platform_comm_alarms",
            ],
        )

    def test_scheduler_registry_registers_storage_ems_only_when_enabled(self):
        with patch.object(scheduler_registry.settings, "enable_auto_cleanup", False), patch.object(
            scheduler_registry.settings,
            "storage_ems_enabled",
            True,
        ):
            jobs = list(scheduler_registry.get_enabled_job_definitions())

        storage_job = next(job for job in jobs if job.id == "evaluate_storage_ems_rules")
        self.assertEqual(str(storage_job.trigger), "cron[minute='*']")

if __name__ == "__main__":
    unittest.main()
