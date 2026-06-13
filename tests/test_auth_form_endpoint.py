import os
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient


def test_login_endpoint_parses_urlencoded_oauth2_form():
    os.environ.setdefault(
        "DATABASE_URL",
        "postgresql://tester:secret@localhost/test_db",
    )
    from app.api.endpoints import auth

    app = FastAPI()
    app.include_router(auth.router, prefix="/auth")
    app.dependency_overrides[auth.get_session] = lambda: object()
    client = TestClient(app)

    with patch(
        "app.api.endpoints.auth.login_use_case",
        return_value={"access_token": "token", "token_type": "bearer"},
    ) as login_use_case:
        response = client.post(
            "/auth/login",
            data={"username": "alice", "password": "secret"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "access_token": "token",
        "token_type": "bearer",
    }
    assert login_use_case.call_args.kwargs["username"] == "alice"
    assert login_use_case.call_args.kwargs["password"] == "secret"
