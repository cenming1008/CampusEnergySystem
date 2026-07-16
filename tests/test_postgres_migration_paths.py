import os

import pytest

from scripts.python.verify_postgres_migrations import (
    PostgresBackend,
    execute_verification,
)

ADMIN_URL = os.getenv("MIGRATION_ADMIN_URL")


@pytest.mark.skipif(not ADMIN_URL, reason="MIGRATION_ADMIN_URL is required")
def test_online_offline_and_roundtrip_fingerprints_match():
    result = execute_verification(PostgresBackend(ADMIN_URL))

    assert result.success
    fingerprints = [item.fingerprint for item in result.paths]
    assert fingerprints[0] == fingerprints[1] == fingerprints[2]
    assert fingerprints[0]["objects"]["hypertable.energydata"]["num_dimensions"] == 1


@pytest.mark.skipif(not ADMIN_URL, reason="MIGRATION_ADMIN_URL is required")
def test_second_real_backend_is_rejected_while_verification_lock_is_held(
    monkeypatch,
):
    from scripts.python.migration_schema import MigrationVerificationError

    first = PostgresBackend(ADMIN_URL)
    second = PostgresBackend(ADMIN_URL)
    temporary_database_calls = []

    monkeypatch.setattr(
        second,
        "create_database",
        lambda name: temporary_database_calls.append(("create", name)),
    )
    monkeypatch.setattr(
        second,
        "drop_database",
        lambda name: temporary_database_calls.append(("drop", name)),
    )

    with first.verification_lock():
        with pytest.raises(MigrationVerificationError, match="already running"):
            execute_verification(second)

    assert temporary_database_calls == []

    with pytest.raises(RuntimeError, match="release probe"):
        with first.verification_lock():
            raise RuntimeError("release probe")
    with second.verification_lock():
        pass
