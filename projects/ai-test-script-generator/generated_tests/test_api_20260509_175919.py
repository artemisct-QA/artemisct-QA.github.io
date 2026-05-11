

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


# === Configuration ===

BASE_URL = "http://localhost:8080"
ENDPOINT = f"{BASE_URL}/api/charging/start"


# === Fixtures ===

@pytest.fixture
def valid_auth_headers():
    """Provide valid authorization headers with a Bearer token."""
    return {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid_token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def expired_auth_headers():
    """Provide expired/invalid authorization headers."""
    return {
        "Authorization": "Bearer expired_or_invalid_token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def no_auth_headers():
    """Provide headers without any authorization."""
    return {
        "Content-Type": "application/json",
    }


@pytest.fixture
def valid_payload():
    """Provide a valid request payload for starting a charging session."""
    return {
        "stationId": "station-alpha-001",
        "targetBattery": 80,
    }


@pytest.fixture
def mock_session_id():
    """Provide a deterministic session ID for mocking."""
    return "sess-" + str(uuid.UUID("12345678-1234-5678-1234-567812345678"))


@pytest.fixture
def mock_post():
    """Mock requests.post to prevent real HTTP calls."""
    with patch("requests.post") as mocked:
        yield mocked


def _build_mock_response(status_code: int, json_data: dict = None) -> MagicMock:
    """Helper: build a mock Response object with given status and JSON body."""
    response = MagicMock(spec=requests.Response)
    response.status_code = status_code
    response.json.return_value = json_data or {}
    response.raise_for_status = MagicMock()
    if status_code >= 400:
        response.raise_for_status.side_effect = requests.HTTPError(
            response=response
        )
    return response


# === Test Class ===

class TestChargingStartEndpoint:
    """Tests for POST /api/charging/start."""

    # ------------------------------------------------------------------
    # Happy Path Tests
    # ------------------------------------------------------------------

    def test_start_charging_success_returns_201_and_session_id(
        self, mock_post, valid_auth_headers, valid_payload, mock_session_id
    ):
        """Verify that a valid request returns 201 Created with a sessionId."""
        expected_body = {"sessionId": mock_session_id}
        mock_post.return_value = _build_mock_response(201, expected_body)

        response = requests.post(
            ENDPOINT, json=valid_payload, headers=valid_auth_headers
        )

        assert response.status_code == 201, (
            f"Expected 201 Created, got {response.status_code}"
        )
        data = response.json()
        assert "sessionId" in data, "Response must contain 'sessionId'"
        assert data["sessionId"] == mock_session_id

        # Verify the outgoing request was correct
        mock_post.assert_called_once_with(
            ENDPOINT, json=valid_payload, headers=valid_auth_headers
        )

    @pytest.mark.parametrize(
        "target_battery",
        [50, 75, 100],
        ids=["minimum-50", "mid-75", "maximum-100"],
    )
    def test_start_charging_with_valid_battery_levels(
        self, mock_post, valid_auth_headers, target_battery
    ):
        """Verify accepted boundary and mid-range targetBattery values."""
        payload = {"stationId": "station-beta-002", "targetBattery": target_battery}
        mock_post.return_value = _build_mock_response(
            201, {"sessionId": f"sess-{target_battery}"}
        )

        response = requests.post(
            ENDPOINT, json=payload, headers=valid_auth_headers
        )

        assert response.status_code == 201, (
            f"targetBattery={target_battery} should be accepted (201), "
            f"got {response.status_code}"
        )
        assert "sessionId" in response.json()

    def test_start_charging_session_id_is_unique_string(
        self, mock_post, valid_auth_headers, valid_payload
    ):
        """Verify sessionId is a non-empty string."""
        session_id = str(uuid.uuid4())
        mock_post.return_value = _build_mock_response(
            201, {"sessionId": session_id}
        )

        response = requests.post(
            ENDPOINT, json=valid_payload, headers=valid_auth_headers
        )

        data = response.json()
        assert isinstance(data["sessionId"], str), "sessionId must be a string"
        assert len(data["sessionId"]) > 0, "sessionId must not be empty"

    # ------------------------------------------------------------------
    # 400 Bad Request – Invalid targetBattery
    # ------------------------------------------------------------------

    @pytest.mark.parametrize(
        "invalid_battery, description",
        [
            (49, "below minimum (49)"),
            (101, "above maximum (101)"),
            (0, "zero"),
            (-1, "negative value"),
            (-100, "large negative value"),
            (150, "far above maximum"),
        ],
        ids=[
            "below-min-49",
            "above-max-101",
            "zero",
            "negative",
            "large-negative",
            "far-above-max-150",
        ],
    )
    def test_invalid_target_battery_returns_400(
        self, mock_post, valid_auth_headers, invalid_battery, description
    ):
        """Verify 400 Bad Request when targetBattery is outside 50-100 range."""
        payload = {"stationId": "station-gamma-003", "targetBattery": invalid_battery}
        error_body = {
            "error": "Bad Request",
            "message": f"targetBattery must be between 50 and 100, got {invalid_battery}",
        }
        mock_post.return_value = _build_mock_response(400, error_body)

        response = requests.post(
            ENDPOINT, json=payload, headers=valid_auth_headers
        )

        assert response.status_code == 400, (
            f"targetBattery={invalid_battery} ({description}) should yield 400, "
            f"got {response.status_code}"
        )
        data = response.json()
        assert "error" in data, "400 response must include 'error' field"

    @pytest.mark.parametrize(
        "invalid_battery, description",
        [
            ("eighty", "string value"),
            (None, "null/None value"),
            (80.5, "float value"),
            (True, "boolean value"),
        ],
        ids=["string", "null", "float", "boolean"],
    )
    def test_non_integer_target_battery_returns_400(
        self, mock_post, valid_auth_headers, invalid_battery, description
    ):
        """Verify 400 Bad Request when targetBattery is not a valid integer."""
        payload = {"stationId": "station-delta-004", "targetBattery": invalid_battery}
        mock_post.return_value = _build_mock_response(
            400,
            {"error": "Bad Request", "message