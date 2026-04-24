from sqlmodel import SQLModel

from app.models import compensation
from app.models import tables


def test_compensation_models_are_reexported_from_tables():
    assert tables.SVGTelemetry is compensation.SVGTelemetry
    assert tables.CapacitorBankTelemetry is compensation.CapacitorBankTelemetry


def test_compensation_tables_are_registered_in_sqlmodel_metadata():
    expected_tables = {
        "svg_telemetry",
        "capacitor_bank_telemetry",
        "capacitor_bank_control_profile",
        "svg_asset_profile",
    }

    assert expected_tables.issubset(SQLModel.metadata.tables.keys())
