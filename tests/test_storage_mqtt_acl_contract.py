from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_storage_simulator_has_device_scoped_mqtt_acl():
    acl = (PROJECT_ROOT / "mosquitto/config/acl").read_text(encoding="utf-8")

    assert "user sto-001" in acl
    assert "topic write campus/device/STO-001/telemetry" in acl
    assert "topic read  campus/control/STO-001" in acl
    assert "topic read  campus/control/STO-001/+" in acl
    assert "topic read  campus/simulation/STO-001/control" in acl
    assert "topic write campus/simulation/+/control" in acl


def test_dev_mqtt_generator_provisions_storage_device_credentials():
    generator = (PROJECT_ROOT / "scripts/shell/gen_dev_mqtt_certs.sh").read_text(
        encoding="utf-8"
    )

    assert "STO001_PWD=$(random_secret)" in generator
    assert "mosquitto_passwd -b /mosquitto/config/passwd sto-001" in generator
    assert "MQTT_STORAGE_USERNAME=sto-001" in generator
    assert "MQTT_STORAGE_PASSWORD=$STO001_PWD" in generator
