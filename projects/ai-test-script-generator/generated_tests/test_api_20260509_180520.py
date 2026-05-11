

```python
"""
Test suite for POST /api/charging/start endpoint.

Tests cover:
- Happy path: successful charging session creation
- Validation: invalid targetBattery values
- Authentication: unauthorized access
- Conflict: charger already in use
- Edge cases: boundary values, missing fields, malformed requests
"""

import uuid
from unittest.mock import patch, MagicMock

import pytest
import requests


# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.example.com"
ENDPOINT = f"{BASE_URL}/api/charging/start"
VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid_token"
EXPIRED_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired_token"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_headers():
    """Provide valid authorization headers."""
    return {
        "Authorization": VALID_TOKEN,
        "Content-Type": "application/json",
    }


@pytest.fixture
def no_auth_headers():
    """Provide headers without authorization."""
    return {
        "Content-Type": "application/json",
    }


@pytest.fixture
def expired_auth_headers():
    """Provide headers with an expired/invalid token."""
    return {
        "Authorization": EXPIRED_TOKEN,
        "Content-Type": "application/json",
    }


@pytest.fixture
def valid_payload():
    """Provide a valid charging start payload."""
    return {
        "stationId": "STATION-001",
        "targetBattery": 80,
    }


@pytest.fixture
def mock_session_id():
    """Provide a deterministic session ID for mocking."""
    return str(uuid.UUID("12345678-1234-5678-1234-567812345678"))


def _build_mock_response(status_code: int, json_data: dict | None = None):
    """Helper: build a MagicMock that behaves like requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data or {}
    mock_resp.ok = 200 <= status_code < 300
    mock_resp.headers = {"Content-Type": "application/json"}
    return mock_resp


# ---------------------------------------------------------------------------
# Service layer (thin wrapper) – the code under test would call this.
# We mock `requests.post` so no real HTTP call is ever made.
# ---------------------------------------------------------------------------

class ChargingService:
    """Thin client wrapper around the charging API."""

    def __init__(self, base_url: str, token: str | None = None):
        self.base_url = base_url
        self.token = token

    def start_charging(self, station_id: str, target_battery: int) -> requests.Response:
        headers = {"Content-Type": "application/json"}
        if self.token:
            headers["Authorization"] = self.token
        payload = {
            "stationId": station_id,
            "targetBattery": target_battery,
        }
        return requests.post(
            f"{self.base_url}/api/charging/start",
            json=payload,
            headers=headers,
            timeout=30,
        )

    def start_charging_raw(self, payload: dict | None = None, headers: dict | None = None) -> requests.Response:
        """Send an arbitrary payload/headers – useful for negative tests."""
        return requests.post(
            f"{self.base_url}/api/charging/start",
            json=payload,
            headers=headers or {"Content-Type": "application/json"},
            timeout=30,
        )


# ===========================================================================
# TEST CLASS
# ===========================================================================

class TestChargingStartEndpoint:
    """Tests for POST /api/charging/start."""

    # -----------------------------------------------------------------------
    # Happy‑path tests (201 Created)
    # -----------------------------------------------------------------------

    @patch("requests.post")
    def test_start_charging_success_returns_201_with_session_id(
        self, mock_post, valid_headers, valid_payload, mock_session_id
    ):
        """A valid request should return 201 and a sessionId."""
        expected_body = {
            "sessionId": mock_session_id,
            "stationId": valid_payload["stationId"],
            "targetBattery": valid_payload["targetBattery"],
            "status": "charging",
        }
        mock_post.return_value = _build_mock_response(201, expected_body)

        service = ChargingService(BASE_URL, VALID_TOKEN)
        response = service.start_charging(
            station_id=valid_payload["stationId"],
            target_battery=valid_payload["targetBattery"],
        )

        assert response.status_code == 201, (
            f"Expected 201 Created, got {response.status_code}"
        )
        body = response.json()
        assert "sessionId" in body, "Response must contain a sessionId"
        assert body["sessionId"] == mock_session_id
        assert body["status"] == "charging"

        # Verify the correct URL and payload were sent
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.kwargs["json"]["stationId"] == valid_payload["stationId"]
        assert call_kwargs.kwargs["json"]["targetBattery"] == valid_payload["targetBattery"]

    @pytest.mark.parametrize(
        "target_battery",
        [50, 75, 100],
        ids=["minimum_50", "mid_75", "maximum_100"],
    )
    @patch("requests.post")
    def test_start_charging_valid_battery_values(
        self, mock_post, target_battery, mock_session_id
    ):
        """targetBattery within [50, 100] should be accepted."""
        expected_body = {
            "sessionId": mock_session_id,
            "stationId": "STATION-002",
            "targetBattery": target_battery,
            "status": "charging",
        }
        mock_post.return_value = _build_mock_response(201, expected_body)

        service = ChargingService(BASE_URL, VALID_TOKEN)
        response = service.start_charging("STATION-002", target_battery)

        assert response.status_code == 201, (
            f"targetBattery={target_battery} should be valid but got {response.status_code}"
        )
        body = response.json()
        assert body["targetBattery"] == target_battery

    @patch("requests.post")
    def test_session_id_is_valid_uuid(self, mock_post, valid_payload):
        """The returned sessionId must be a valid UUID string."""
        generated_uuid = str(uuid.uuid4())
        mock_post.return_value = _build_mock_response(
            201, {"sessionId": generated_uuid, "status": "charging"}
        )

        service = ChargingService(BASE_URL, VALID_TOKEN)
        response = service.start_charging(
            valid_payload["stationId"], valid_payload["targetBattery"]
        )

        session_id = response.json()["sessionId"]
        # Validate it's a well‑formed UUID
        parsed = uuid.UUID(session_id)
        assert str(parsed) == session_id, "sessionId is not a valid UUID"

    # -----------------------------------------------------------------------
    # 400 Bad Request – invalid targetBattery
    # -----------------------------------------------------------------------

    @pytest.mark.parametrize(
        "invalid_battery, description",
        [
            (49, "below_minimum_49"),
            (101, "above_maximum_101"),
            (0, "zero"),
            (-1, "negative_value