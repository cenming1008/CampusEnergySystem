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
