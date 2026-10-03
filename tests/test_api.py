import io
import os
import socket
from unittest.mock import MagicMock

# Use localhost:5432 when PostgreSQL is running (GitHub Actions), otherwise local SQLite
def _configure_test_db_env():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    localhost_pg_up = sock.connect_ex(("127.0.0.1", 5432)) == 0
    sock.close()

    if localhost_pg_up:
        os.environ["POSTGRES_HOST"] = "localhost"
        os.environ["POSTGRES_PORT"] = "5432"
    else:
        os.environ["TEST_DATABASE_URL"] = "sqlite:///./test_local.db"

_configure_test_db_env()

import pytest
from fastapi.testclient import TestClient

from main import app
from app.database import get_db, Base, engine
from app.models.api_key import ApiKey
from app.auth import get_valid_api_key

Base.metadata.create_all(bind=engine)
client = TestClient(app)


def test_root_and_health_endpoints():
    """1. Verify public endpoints return 200 without requiring an API key."""
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "running"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"


def test_docs_and_openapi_schema():
    """2. Verify Swagger UI and OpenAPI schema generate cleanly."""
    docs_res = client.get("/docs")
    assert docs_res.status_code == 200

    openapi_res = client.get("/openapi.json")
    assert openapi_res.status_code == 200
    assert "paths" in openapi_res.json()


def test_auth_missing_api_key():
    """3. Missing X-API-Key header must return 401 UNAUTHORIZED."""
    response = client.post("/api/v1/predict")
    assert response.status_code == 401

    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNAUTHORIZED"
    assert "Missing X-API-Key header" in payload["error"]["message"]


def test_auth_invalid_api_key():
    """4. An unregistered X-API-Key must return 401 UNAUTHORIZED."""
    headers = {"X-API-Key": "non-existent-fake-key-9999"}
    response = client.post("/api/v1/predict", headers=headers)
    assert response.status_code == 401

    payload = response.json()
    assert payload["success"] is False
    assert payload["error"]["code"] == "UNAUTHORIZED"
    assert "invalid API Key" in payload["error"]["message"]


def test_file_validation_missing_and_invalid_files():
    """5. Sending missing files or a non-image .txt file must be rejected (400 or 422)."""
    dummy_key = ApiKey(id=999, user_id=1, name="test-key", key_hash="mock", is_active=True)
    app.dependency_overrides[get_valid_api_key] = lambda: dummy_key

    try:
        # Case A: Missing file payload entirely -> FastAPI returns 422
        missing_res = client.post("/api/v1/predict")
        assert missing_res.status_code in (400, 422)

        # Case B: Uploading a plain text file instead of an image -> returns 400 or 422
        invalid_file = [("files", ("not_an_image.txt", io.BytesIO(b"hello world"), "text/plain"))]
        invalid_res = client.post("/api/v1/predict", files=invalid_file)
        assert invalid_res.status_code in (400, 422)
    finally:
        app.dependency_overrides.clear()


def test_rate_limit_exceeded_returns_429():
    """6. Verify that 5 or more recent requests in the last minute trigger HTTP 429."""
    dummy_key = ApiKey(id=999, user_id=1, name="rate-limit-key", key_hash="mock", is_active=True)

    # Mock the DB query count inside verify_rate_limit to return 5 requests in the last minute
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.count.return_value = 5

    app.dependency_overrides[get_valid_api_key] = lambda: dummy_key
    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        response = client.post("/api/v1/predict")
        assert response.status_code == 429

        payload = response.json()
        assert payload["success"] is False
        assert payload["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "Rate limit exceeded" in payload["error"]["message"]
    finally:
        app.dependency_overrides.clear()
