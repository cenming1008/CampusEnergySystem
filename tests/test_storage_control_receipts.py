import os
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.integrations.mqtt.control_receipts import process_device_control_receipt


def test_dispatches_storage_receipt_to_storage_control_service():
    session = MagicMock()
    session.get.return_value = SimpleNamespace(device_category="storage")

    with patch(
        "app.services.devices.storage.control_command_service.StorageControlCommandService.apply_control_receipt"
    ) as apply_storage, patch(
        "app.services.devices.compensation.capacitor_bank.control_command_service."
        "CapacitorBankControlCommandService.apply_control_receipt"
    ) as apply_compensation:
        expected = object()
        apply_storage.return_value = expected
        result = process_device_control_receipt(
            session,
            {"command_id": "21", "result": "success", "detail": "执行完成"},
            device_id=7,
        )

    assert result is expected
    apply_storage.assert_called_once()
    assert apply_storage.call_args.kwargs["command_id"] == "21"
    assert apply_storage.call_args.kwargs["result"] == "success"
    apply_compensation.assert_not_called()


def test_dispatches_non_storage_receipt_to_existing_compensation_service():
    session = MagicMock()
    session.get.return_value = SimpleNamespace(device_category="compensation")

    with patch(
        "app.services.devices.storage.control_command_service.StorageControlCommandService.apply_control_receipt"
    ) as apply_storage, patch(
        "app.services.devices.compensation.capacitor_bank.control_command_service."
        "CapacitorBankControlCommandService.apply_control_receipt"
    ) as apply_compensation:
        expected = object()
        apply_compensation.return_value = expected
        result = process_device_control_receipt(
            session,
            {"command_id": "88", "result": "refused", "reason": "设备处于就地模式"},
            device_id=16,
        )

    assert result is expected
    apply_storage.assert_not_called()
    apply_compensation.assert_called_once()
    assert apply_compensation.call_args.kwargs["result"] == "rejected"
