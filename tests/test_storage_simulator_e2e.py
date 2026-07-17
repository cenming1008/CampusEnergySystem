import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine, select

os.environ.setdefault("DATABASE_URL", "postgresql://tester:secret@localhost/test_db")

from app.api.endpoints.devices.storage import router as storage_router
from app.integrations.mqtt.device_extensions import persist_device_extensions
from app.models.storage import StorageTelemetry
from app.models.tables import Device
from app.services.devices.storage.monitor_service import StorageMonitorService
from scripts.python.run_storage_demo import run_demo

ROOT = Path(__file__).resolve().parents[1]


def test_sunny_workday_demo_and_real_adapter_keep_one_platform_contract(tmp_path):
    summary = run_demo(
        scenario="sunny_workday",
        speed=5760.0,
        seed=20260716,
        output_dir=tmp_path,
    )

    assert summary["scenario"] == "sunny_workday"
    assert summary["invariants"] == {
        "midday_charge": True,
        "evening_discharge": True,
        "soc_hard_bounds": True,
        "safety_rejection": True,
        "terminal_receipt": True,
        "calculated_comparison": True,
        "persistent_simulated_label": True,
    }
    assert set(summary["comparison"]["strategies"]) == {"baseline", "rule", "day_ahead"}
    assert summary["comparison"]["data_source"] == "calculated"
    assert summary["min_soc"] >= 10.0
    assert summary["max_soc"] <= 90.0
    assert (tmp_path / "storage-demo-raw.json").exists()
    assert (tmp_path / "storage-demo-raw.csv").exists()
    assert json.loads((tmp_path / "storage-demo-summary.json").read_text())["seed"] == 20260716

    engine = create_engine("sqlite://")
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        device = Device(
            name="可替换适配器储能柜",
            sn="STO-ADAPTER-001",
            device_type="storage",
            device_subtype="battery_energy_storage_system",
            device_category="storage",
            energy_type="electricity",
        )
        session.add(device)
        session.commit()
        session.refresh(device)
        simulated_time = datetime.now() - timedelta(seconds=1)
        persist_device_extensions(
            session,
            device.id,
            simulated_time,
            {
                **summary["last_payload"],
                "data_source": "simulated",
            },
        )
        session.commit()
        simulated_response = StorageMonitorService.build_storage_monitor(session, device.id)

        real_time = datetime.now()
        real_payload = {
            **summary["last_payload"],
            "device_code": device.sn,
            "timestamp": real_time.isoformat(),
            "data_source": "real",
        }
        real_payload.pop("simulation_run_id", None)
        persist_device_extensions(session, device.id, real_time, real_payload)
        session.commit()
        real_response = StorageMonitorService.build_storage_monitor(session, device.id)

        rows = session.exec(
            select(StorageTelemetry)
            .where(StorageTelemetry.device_id == device.id)
            .order_by(StorageTelemetry.timestamp)
        ).all()

    assert [row.data_source for row in rows] == ["simulated", "real"]
    assert rows[0].device_id == rows[1].device_id == device.id
    assert simulated_response.keys() == real_response.keys()
    assert simulated_response["key_metrics"].keys() == real_response["key_metrics"].keys()
    assert simulated_response["key_metrics"]["data_source"]["value"] == "simulated"
    assert real_response["key_metrics"]["data_source"]["value"] == "real"
    route_paths = {route.path for route in storage_router.routes}
    assert "/{device_id}/storage/telemetry/latest" in route_paths


def test_demo_entrypoint_runs_without_external_database_configuration(tmp_path):
    environment = os.environ.copy()
    environment.pop("DATABASE_URL", None)

    result = subprocess.run(
        [
            sys.executable,
            "scripts/python/run_storage_demo.py",
            "--scenario",
            "sunny_workday",
            "--seed",
            "20260716",
            "--output-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert (tmp_path / "storage-demo-summary.json").exists()


def test_demo_artifacts_are_deterministic_for_the_same_inputs(tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"

    run_demo(
        scenario="sunny_workday",
        speed=5760.0,
        seed=20260716,
        output_dir=first_dir,
    )
    run_demo(
        scenario="sunny_workday",
        speed=5760.0,
        seed=20260716,
        output_dir=second_dir,
    )

    for filename in (
        "storage-demo-raw.json",
        "storage-demo-raw.csv",
        "storage-demo-summary.json",
    ):
        assert (first_dir / filename).read_bytes() == (second_dir / filename).read_bytes()
