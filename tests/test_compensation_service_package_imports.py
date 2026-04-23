from pathlib import Path

from app.services.devices.compensation.capacitor_bank.control_command_service import (
    CapacitorBankControlCommandService,
)
from app.services.devices.compensation.capacitor_bank.control_profile_service import (
    CapacitorBankControlProfileService,
)
from app.services.devices.compensation.capacitor_bank.parameter_write_service import (
    CapacitorBankParameterWriteService,
)
from app.services.devices.compensation.capacitor_bank.service import CapacitorBankService
from app.services.devices.compensation.monitor_service import CompensationMonitorService
from app.services.devices.compensation.svg.service import SVGService


def test_compensation_device_services_have_new_package_entrypoints():
    assert CapacitorBankService.__name__ == "CapacitorBankService"
    assert CapacitorBankControlCommandService.__name__ == "CapacitorBankControlCommandService"
    assert CapacitorBankControlProfileService.__name__ == "CapacitorBankControlProfileService"
    assert CapacitorBankParameterWriteService.__name__ == "CapacitorBankParameterWriteService"
    assert CompensationMonitorService.__name__ == "CompensationMonitorService"
    assert SVGService.__name__ == "SVGService"


def test_compensation_device_legacy_root_service_wrappers_are_removed():
    legacy_paths = [
        "app/services/capacitor_bank_service.py",
        "app/services/capacitor_bank_control_command_service.py",
        "app/services/capacitor_bank_control_profile_service.py",
        "app/services/capacitor_bank_control_specs.py",
        "app/services/capacitor_bank_parameter_write_service.py",
        "app/services/compensation_monitor_service.py",
        "app/services/svg_service.py",
    ]

    assert not any(Path(path).exists() for path in legacy_paths)


def test_compensation_device_endpoints_use_new_service_package_paths():
    endpoint_sources = [
        "app/api/endpoints/devices/compensation_capacitor_bank.py",
        "app/api/endpoints/devices/compensation_svg.py",
    ]

    combined_source = "\n".join(open(path, encoding="utf-8").read() for path in endpoint_sources)

    assert "from app.services.capacitor_bank_service" not in combined_source
    assert "from app.services.svg_service" not in combined_source
    assert "app.services.devices.compensation.capacitor_bank.service" in combined_source
    assert "app.services.devices.compensation.svg.service" in combined_source
