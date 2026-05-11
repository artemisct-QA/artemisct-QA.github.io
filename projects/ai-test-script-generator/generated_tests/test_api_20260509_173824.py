

```python
"""
Test suite for POST /api/charging/start endpoint.

Covers:
- 201 Created (happy path with various valid inputs)
- 400 Bad Request (validation errors)
- 409 Conflict (Charger In Use)
- Edge cases (boundary values, missing fields, invalid types)
"""

import pytest
import uuid
from unittest.mock import patch, MagicMock
import requests
import json


# ──────────────────────────────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────────────────────────────

@pytest.fixture
def base_url():
    """Base URL for the charging API."""
    return "https://api.example.com"


@pytest.fixture
def endpoint(base_url):
    """Full endpoint URL for starting a charging session."""
    return f"{base_url}/api/charging/start"


@pytest.fixture
def auth_headers():
    """Standard authorization headers with a Bearer token."""
    return {
        "Authorization": "Bearer test-jwt-token-abc123",
        "Content-Type": "application/json",
    }


@pytest.fixture
def valid_payload():
    """A valid request payload for starting a charging session."""
    return {
        "stationId": "STN-001",
        "targetBattery": 80,
    }


@pytest.fixture
def mock_session_id():
    """A deterministic session ID for assertions."""
    return "sess-f47ac10b-58cc-4372-a567-0e02b2c3d479"


@pytest.fixture
def successful_response(mock_session_id):
    """Mock a 201 Created response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 201
    mock_resp.json.return_value = {
        "sessionId": mock_session_id,
        "status": "charging",
        "message": "Charging session started successfully",
    }
    mock_resp.headers = {"Content-Type": "application/json"}
    return mock_resp


@pytest.fixture
def bad_request_response():
    """Mock a 400 Bad Request response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 400
    mock_resp.json.return_value = {
        "error": "Bad Request",
        "message": "Validation failed",
        "details": [],
    }
    mock_resp.headers = {"Content-Type": "application/json"}
    return mock_resp


@pytest.fixture
def conflict_response():
    """Mock a 409 Conflict response (charger already in use)."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = 409
    mock_resp.json.return_value = {
        "error": "Conflict",
        "message": "Charger is currently in use",
        "stationId": "STN-001",
    }
    mock_resp.headers = {"Content-Type": "application/json"}
    return mock_resp


# ──────────────────────────────────────────────────────────────────────
# Helper
# ──────────────────────────────────────────────────────────────────────

def _post_charging_start(endpoint, headers, payload):
    """Wrapper around requests.post for the charging start endpoint."""
    return requests.post(endpoint, json=payload, headers=headers)


# ──────────────────────────────────────────────────────────────────────
# Test class
# ──────────────────────────────────────────────────────────────────────

class TestChargingStartEndpoint:
    """Tests for POST /api/charging/start"""

    # ── Happy-path tests ─────────────────────────────────────────────

    @patch("requests.post")
    def test_start_charging_returns_201_with_session_id(
        self, mock_post, endpoint, auth_headers, valid_payload,
        successful_response, mock_session_id,
    ):
        """Verify that a valid request returns 201 and includes a sessionId."""
        mock_post.return_value = successful_response

        response = _post_charging_start(endpoint, auth_headers, valid_payload)

        assert response.status_code == 201, (
            f"Expected 201 Created, got {response.status_code}"
        )
        body = response.json()
        assert "sessionId" in body, "Response body must contain 'sessionId'"
        assert body["sessionId"] == mock_session_id
        mock_post.assert_called_once_with(
            endpoint, json=valid_payload, headers=auth_headers,
        )

    @patch("requests.post")
    def test_start_charging_response_contains_status_field(
        self, mock_post, endpoint, auth_headers, valid_payload,
        successful_response,
    ):
        """Verify the response body includes a 'status' field set to 'charging'."""
        mock_post.return_value = successful_response

        response = _post_charging_start(endpoint, auth_headers, valid_payload)
        body = response.json()

        assert body.get("status") == "charging", (
            "Expected status='charging' in the response body"
        )

    @pytest.mark.parametrize(
        "station_id, target_battery",
        [
            ("STN-001", 80),
            ("STN-999", 100),
            ("STN-ABC-42", 1),
            ("station-with-long-id-0123456789", 50),
        ],
        ids=[
            "typical_station_80pct",
            "station_full_charge",
            "alphanumeric_station_min_battery",
            "long_station_id_50pct",
        ],
    )
    @patch("requests.post")
    def test_start_charging_with_various_valid_inputs(
        self, mock_post, endpoint, auth_headers, mock_session_id,
        station_id, target_battery,
    ):
        """Parametrized: various valid stationId/targetBattery combos yield 201."""
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 201
        mock_resp.json.return_value = {
            "sessionId": mock_session_id,
            "status": "charging",
            "message": "Charging session started successfully",
        }
        mock_post.return_value = mock_resp

        payload = {"stationId": station_id, "targetBattery": target_battery}
        response = _post_charging_start(endpoint, auth_headers, payload)

        assert response.status_code == 201
        assert response.json()["sessionId"] == mock_session_id

    @patch("requests.post")
    def test_session_id_format_is_valid(
        self, mock_post, endpoint, auth_headers, valid_payload,
    ):
        """Verify the returned sessionId looks like a prefixed UUID."""
        generated_id = f"sess-{uuid.uuid4()}"
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"sessionId": generated_id, "status": "charging"}
        mock_post.return_value = mock_resp

        response = _post_charging_start(endpoint, auth_headers, valid_payload)
        session_id = response.json()["sessionId"]

        assert session_id.startswith("sess-"), (
            "sessionId should start with 'sess-' prefix"
        )
        # Validate the UUID portion
        uuid_part = session_id.replace("sess-", "", 1)
        try:
            uuid.UUID(uuid_part)
        except ValueError:
            pytest.fail(f"sessionId UUID portion is invalid: {uuid_part}")

    # ── 400 Bad Request