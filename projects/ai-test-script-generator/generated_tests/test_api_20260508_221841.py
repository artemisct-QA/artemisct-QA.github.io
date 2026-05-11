

```python
"""
Test suite for GET /api/status endpoint.

This module contains comprehensive tests for the status API endpoint,
covering happy path, error cases, edge cases, and various response scenarios.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, timezone
import requests


# --- Simulated API Client ---

class APIClient:
    """Simple API client for the status endpoint."""

    def __init__(self, base_url: str, api_key: str = None, timeout: int = 30):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout
        self.session = requests.Session()

    def get_status(self, headers: dict = None, params: dict = None, timeout: int = None):
        """Send GET request to /api/status endpoint."""
        url = f"{self.base_url}/api/status"
        request_headers = {}

        if self.api_key:
            request_headers["Authorization"] = f"Bearer {self.api_key}"

        if headers:
            request_headers.update(headers)

        return self.session.get(
            url,
            headers=request_headers,
            params=params,
            timeout=timeout or self.timeout,
        )


# --- Fixtures ---

@pytest.fixture
def base_url():
    """Base URL for the API."""
    return "https://api.example.com"


@pytest.fixture
def valid_api_key():
    """Valid API key for authentication."""
    return "test-valid-api-key-12345"


@pytest.fixture
def invalid_api_key():
    """Invalid API key for negative testing."""
    return "invalid-key-00000"


@pytest.fixture
def api_client(base_url, valid_api_key):
    """Authenticated API client instance."""
    return APIClient(base_url=base_url, api_key=valid_api_key)


@pytest.fixture
def unauthenticated_client(base_url):
    """API client without authentication."""
    return APIClient(base_url=base_url, api_key=None)


@pytest.fixture
def healthy_status_response():
    """Standard healthy status response payload."""
    return {
        "status": "healthy",
        "version": "2.5.1",
        "uptime": 86400,
        "timestamp": "2024-01-15T12:00:00Z",
        "services": {
            "database": {"status": "connected", "latency_ms": 5},
            "cache": {"status": "connected", "latency_ms": 2},
            "queue": {"status": "connected", "latency_ms": 8},
        },
        "environment": "production",
    }


@pytest.fixture
def degraded_status_response():
    """Degraded status response payload (partial service failure)."""
    return {
        "status": "degraded",
        "version": "2.5.1",
        "uptime": 43200,
        "timestamp": "2024-01-15T12:00:00Z",
        "services": {
            "database": {"status": "connected", "latency_ms": 5},
            "cache": {"status": "disconnected", "latency_ms": None},
            "queue": {"status": "connected", "latency_ms": 8},
        },
        "environment": "production",
    }


@pytest.fixture
def unhealthy_status_response():
    """Unhealthy status response payload (critical failure)."""
    return {
        "status": "unhealthy",
        "version": "2.5.1",
        "uptime": 0,
        "timestamp": "2024-01-15T12:00:00Z",
        "services": {
            "database": {"status": "disconnected", "latency_ms": None},
            "cache": {"status": "disconnected", "latency_ms": None},
            "queue": {"status": "disconnected", "latency_ms": None},
        },
        "environment": "production",
    }


def _build_mock_response(
    status_code: int,
    json_body: dict = None,
    text_body: str = None,
    headers: dict = None,
    elapsed_seconds: float = 0.05,
):
    """Helper to build a fully-configured mock Response object."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.headers = headers or {"Content-Type": "application/json"}

    if json_body is not None:
        mock_resp.json.return_value = json_body
        mock_resp.text = json.dumps(json_body)
    elif text_body is not None:
        mock_resp.json.side_effect = json.JSONDecodeError("Expecting value", text_body, 0)
        mock_resp.text = text_body
    else:
        mock_resp.json.return_value = {}
        mock_resp.text = "{}"

    # Simulate elapsed time
    elapsed_mock = MagicMock()
    elapsed_mock.total_seconds.return_value = elapsed_seconds
    mock_resp.elapsed = elapsed_mock

    mock_resp.ok = 200 <= status_code < 300
    mock_resp.url = "https://api.example.com/api/status"
    mock_resp.reason = requests.status_codes._codes.get(status_code, ("unknown",))[0].replace("_", " ").title() if hasattr(requests.status_codes, '_codes') else "OK"

    return mock_resp


# ===========================================================================
# TEST CLASS: Happy Path / Success Scenarios
# ===========================================================================

class TestGetStatusHappyPath:
    """Tests for successful GET /api/status responses."""

    @patch.object(requests.Session, "get")
    def test_status_returns_200_when_all_services_healthy(
        self, mock_get, api_client, healthy_status_response
    ):
        """Verify 200 OK is returned when all services are healthy."""
        mock_get.return_value = _build_mock_response(200, healthy_status_response)

        response = api_client.get_status()

        assert response.status_code == 200, (
            f"Expected 200 OK but got {response.status_code}"
        )

    @patch.object(requests.Session, "get")
    def test_status_response_contains_required_fields(
        self, mock_get, api_client, healthy_status_response
    ):
        """Verify the response body contains all required top-level fields."""
        mock_get.return_value = _build_mock_response(200, healthy_status_response)

        response = api_client.get_status()
        data = response.json()

        required_fields = ["status", "version", "uptime", "timestamp", "services"]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"

    @patch.object(requests.Session, "get")
    def test_status_healthy_value_is_correct(
        self, mock_get, api_client, healthy_status_response
    ):
        """Verify the 'status' field is 'healthy' when all services are up."""
        mock_get.return_value = _build_mock_response(200, healthy_status_response)

        response = api_client.get_status()
        data = response.json()

        assert data["status"] == "healthy", (
            f"Expected status 'healthy' but got '{data['status']}'"
        )

    @patch.object(requests.Session, "get")
    def test_status_response_content_type_is_json(
        self, mock_get, api_client, healthy_status_response
    ):
        """Verify the Content-Type header is application/json."""
        mock_get.return_value = _build_mock_response(
            200,
            healthy_status_response,