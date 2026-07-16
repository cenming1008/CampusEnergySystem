"""Verify Alembic migrations against three isolated PostgreSQL databases."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from contextlib import closing
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Protocol

import psycopg2
from psycopg2 import sql
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from sqlalchemy.engine import make_url

if __package__:
    from scripts.python.migration_schema import (
        MigrationVerificationError,
        collect_schema_fingerprint,
        compare_fingerprints,
        validate_temporary_database_name,
    )
else:  # Support direct execution from the repository root.
    from migration_schema import (  # type: ignore[no-redef]
        MigrationVerificationError,
        collect_schema_fingerprint,
        compare_fingerprints,
        validate_temporary_database_name,
    )


REPOSITORY_ROOT = Path(__file__).resolve().parents[2]


class MigrationPath(str, Enum):
    FRESH = "fresh"
    OFFLINE = "offline"
    ROUNDTRIP = "roundtrip"


PATH_DATABASES = {
    MigrationPath.FRESH: "ces_migration_fresh",
    MigrationPath.OFFLINE: "ces_migration_offline",
    MigrationPath.ROUNDTRIP: "ces_migration_roundtrip",
}


@dataclass(frozen=True)
class PathResult:
    path: MigrationPath
    database_name: str
    success: bool
    fingerprint: dict[str, object] | None
    failed_step: str | None = None


@dataclass(frozen=True)
class VerificationResult:
    paths: tuple[PathResult, ...]

    @property
    def success(self) -> bool:
        return all(item.success for item in self.paths)


class MigrationBackend(Protocol):
    def create_database(self, name: str) -> None: ...

    def drop_database(self, name: str) -> None: ...

    def upgrade(self, name: str) -> None: ...

    def downgrade_to_base(self, name: str) -> None: ...

    def generate_offline_sql(self) -> str: ...

    def apply_offline_sql(self, name: str, sql_text: str) -> None: ...

    def fingerprint(self, name: str) -> dict[str, object]: ...


def build_database_url(admin_url: str, database_name: str) -> str:
    """Replace only the database component while retaining real credentials."""
    validate_temporary_database_name(database_name)
    return make_url(admin_url).set(database=database_name).render_as_string(
        hide_password=False
    )


def build_psycopg2_url(
    admin_url: str, database_name: str | None = None
) -> str:
    """Render a driverless URL accepted directly by psycopg2."""
    parsed = make_url(admin_url)
    if database_name is not None:
        validate_temporary_database_name(database_name)
        parsed = parsed.set(database=database_name)
    return parsed.set(drivername="postgresql").render_as_string(
        hide_password=False
    )


class PostgresBackend:
    """Own the safe database lifecycle and Alembic subprocess boundaries."""

    def __init__(self, admin_url: str):
        self._admin_url = admin_url

    def _target_url(self, name: str) -> str:
        return build_database_url(self._admin_url, name)

    def _psycopg2_url(self, name: str | None = None) -> str:
        return build_psycopg2_url(self._admin_url, name)

    def _run_alembic(self, name: str, arguments: list[str]) -> subprocess.CompletedProcess[str]:
        environment = os.environ.copy()
        environment["DATABASE_URL"] = self._target_url(name)
        return subprocess.run(
            [sys.executable, "-m", "alembic", *arguments],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=environment,
            cwd=REPOSITORY_ROOT,
        )

    def create_database(self, name: str) -> None:
        validate_temporary_database_name(name)
        with closing(psycopg2.connect(self._psycopg2_url())) as connection:
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with connection.cursor() as cursor:
                cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))

    def drop_database(self, name: str) -> None:
        validate_temporary_database_name(name)
        with closing(psycopg2.connect(self._psycopg2_url())) as connection:
            connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            with connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT pg_terminate_backend(pid)
                    FROM pg_stat_activity
                    WHERE datname = %s AND pid <> pg_backend_pid()
                    """,
                    (name,),
                )
                cursor.execute(
                    sql.SQL("DROP DATABASE IF EXISTS {}").format(sql.Identifier(name))
                )

    def upgrade(self, name: str) -> None:
        self._run_alembic(name, ["upgrade", "head"])

    def downgrade_to_base(self, name: str) -> None:
        self._run_alembic(name, ["downgrade", "base"])

    def generate_offline_sql(self) -> str:
        completed = self._run_alembic(
            PATH_DATABASES[MigrationPath.OFFLINE],
            ["upgrade", "head", "--sql"],
        )
        return completed.stdout

    def apply_offline_sql(self, name: str, sql_text: str) -> None:
        target_url = self._psycopg2_url(name)
        with closing(psycopg2.connect(target_url)) as connection:
            with connection:
                with connection.cursor() as cursor:
                    cursor.execute(sql_text)

    def fingerprint(self, name: str) -> dict[str, object]:
        target_url = self._psycopg2_url(name)
        with closing(psycopg2.connect(target_url)) as connection:
            with connection:
                return collect_schema_fingerprint(connection)


def cleanup_databases(backend: MigrationBackend) -> None:
    """Drop only the three exact temporary database names."""
    failures: list[str] = []
    for database_name in PATH_DATABASES.values():
        validate_temporary_database_name(database_name)
        try:
            backend.drop_database(database_name)
        except Exception as error:
            failures.append(f"{database_name} ({type(error).__name__})")
    if failures:
        raise MigrationVerificationError(
            "could not drop fixed migration databases: " + ", ".join(failures)
        )


def _not_started(path: MigrationPath) -> PathResult:
    return PathResult(
        path=path,
        database_name=PATH_DATABASES[path],
        success=False,
        fingerprint=None,
        failed_step="not_started",
    )


def _failed(path: MigrationPath, step: str) -> PathResult:
    return PathResult(
        path=path,
        database_name=PATH_DATABASES[path],
        success=False,
        fingerprint=None,
        failed_step=f"{path.value}.{step}",
    )


def _run_fresh(backend: MigrationBackend) -> PathResult:
    path = MigrationPath.FRESH
    name = PATH_DATABASES[path]
    try:
        backend.create_database(name)
    except Exception:
        return _failed(path, "create_database")
    try:
        backend.upgrade(name)
    except Exception:
        return _failed(path, "upgrade")
    try:
        fingerprint = backend.fingerprint(name)
    except Exception:
        return _failed(path, "fingerprint")
    return PathResult(path, name, True, fingerprint)


def _run_offline(backend: MigrationBackend) -> PathResult:
    path = MigrationPath.OFFLINE
    name = PATH_DATABASES[path]
    try:
        backend.create_database(name)
    except Exception:
        return _failed(path, "create_database")
    try:
        sql_text = backend.generate_offline_sql()
    except Exception:
        return _failed(path, "generate_offline_sql")
    try:
        backend.apply_offline_sql(name, sql_text)
    except Exception:
        return _failed(path, "apply_offline_sql")
    try:
        fingerprint = backend.fingerprint(name)
    except Exception:
        return _failed(path, "fingerprint")
    return PathResult(path, name, True, fingerprint)


def _run_roundtrip(backend: MigrationBackend) -> PathResult:
    path = MigrationPath.ROUNDTRIP
    name = PATH_DATABASES[path]
    try:
        backend.create_database(name)
    except Exception:
        return _failed(path, "create_database")
    try:
        backend.upgrade(name)
    except Exception:
        return _failed(path, "upgrade")
    try:
        backend.downgrade_to_base(name)
    except Exception:
        return _failed(path, "downgrade_to_base")
    try:
        backend.upgrade(name)
    except Exception:
        return _failed(path, "reupgrade")
    try:
        fingerprint = backend.fingerprint(name)
    except Exception:
        return _failed(path, "fingerprint")
    return PathResult(path, name, True, fingerprint)


def _cleanup_successful_result(
    backend: MigrationBackend, result: VerificationResult
) -> VerificationResult:
    paths = list(result.paths)
    for index, item in enumerate(paths):
        try:
            backend.drop_database(item.database_name)
        except Exception:
            paths[index] = replace(
                item,
                success=False,
                failed_step=f"{item.path.value}.drop_database",
            )
    return VerificationResult(tuple(paths))


def execute_verification(
    backend: MigrationBackend, *, keep_success: bool = False
) -> VerificationResult:
    """Execute fixed migration paths and preserve all databases after any failure."""
    runners = {
        MigrationPath.FRESH: _run_fresh,
        MigrationPath.OFFLINE: _run_offline,
        MigrationPath.ROUNDTRIP: _run_roundtrip,
    }
    results: list[PathResult] = []
    for path in MigrationPath:
        item = runners[path](backend)
        results.append(item)
        if not item.success:
            results.extend(_not_started(pending) for pending in list(MigrationPath)[len(results) :])
            return VerificationResult(tuple(results))

    result = VerificationResult(tuple(results))
    fresh = results[0].fingerprint
    offline = results[1].fingerprint
    roundtrip = results[2].fingerprint
    if fresh is None or offline is None or roundtrip is None:
        raise MigrationVerificationError("completed path has no fingerprint")

    for index, candidate in ((1, offline), (2, roundtrip)):
        try:
            compare_fingerprints(fresh, candidate)
        except MigrationVerificationError:
            failed = replace(
                results[index],
                success=False,
                failed_step=f"{results[index].path.value}.compare_fingerprints",
            )
            compared = [*results]
            compared[index] = failed
            return VerificationResult(tuple(compared))

    if keep_success:
        return result
    return _cleanup_successful_result(backend, result)


def _result_payload(result: VerificationResult) -> dict[str, object]:
    return {
        "success": result.success,
        "paths": [
            {
                "path": item.path.value,
                "database_name": item.database_name,
                "success": item.success,
                "fingerprint": item.fingerprint,
                "failed_step": item.failed_step,
            }
            for item in result.paths
        ],
    }


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Verify Alembic migrations in three fixed temporary databases."
    )
    parser.add_argument(
        "--admin-url",
        help="administrative PostgreSQL URL (or set MIGRATION_ADMIN_URL)",
    )
    parser.add_argument(
        "--keep-success",
        action="store_true",
        help="preserve successful temporary databases",
    )
    parser.add_argument(
        "--cleanup",
        action="store_true",
        help="drop the three fixed temporary databases and exit",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        help="write the normalized verification result JSON",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    arguments = parser.parse_args(argv)
    admin_url = arguments.admin_url or os.environ.get("MIGRATION_ADMIN_URL")
    if not admin_url:
        parser.error("--admin-url is required unless MIGRATION_ADMIN_URL is set")

    backend = PostgresBackend(admin_url)
    if arguments.cleanup:
        try:
            cleanup_databases(backend)
        except MigrationVerificationError as error:
            print(f"cleanup failed: {error}", file=sys.stderr)
            return 1
        else:
            return 0

    result = execute_verification(backend, keep_success=arguments.keep_success)
    payload = _result_payload(result)
    if arguments.json_output:
        arguments.json_output.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )

    if not result.success:
        for item in result.paths:
            if not item.success:
                print(
                    f"{item.database_name}: {item.failed_step}",
                    file=sys.stderr,
                )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
