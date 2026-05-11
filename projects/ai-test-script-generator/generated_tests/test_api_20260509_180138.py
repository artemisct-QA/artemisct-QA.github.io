

```python
"""
Test suite for PUT /api/user/preferences endpoint.

Tests cover:
- Happy path: updating single and multiple optional fields
- Error handling: 400 Bad Request, 401 Unauthorized, 422 Unprocessable Entity
- Edge cases: empty body, null values, boundary values
"""

import pytest
from unittest.mock import patch, MagicMock
import json
import requests


# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

BASE_URL = "https://api.example.com"
ENDPOINT = f"{BASE_URL}/api/user/preferences"

VALID_CHARGER_TYPES = ["Level1", "Level2", "DCFastCharger", "Tesla Supercharger"]
INVALID_CHARGER_TYPES = ["InvalidType", "SuperDuper", "Level99", ""]

VALID_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.valid_token"
EXPIRED_TOKEN = "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.expired_token"
MALFORMED_TOKEN = "not-a-real-token"


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def valid_auth_headers():
    """Return headers with a valid Bearer token."""
    return {
        "Authorization": VALID_TOKEN,
        "Content-Type": "application/json",
    }


@pytest.fixture
def expired_auth_headers():
    """Return headers with an expired Bearer token."""
    return {
        "Authorization": EXPIRED_TOKEN,
        "Content-Type": "application/json",
    }


@pytest.fixture
def no_auth_headers():
    """Return headers without any Authorization header."""
    return {
        "Content-Type": "application/json",
    }


@pytest.fixture
def malformed_auth_headers():
    """Return headers with a malformed Authorization token."""
    return {
        "Authorization": MALFORMED_TOKEN,
        "Content-Type": "application/json",
    }


@pytest.fixture
def existing_preferences():
    """Simulate existing user preferences stored on the server."""
    return {
        "preferredChargerTypes": ["Level2"],
        "maxDailyChargingCost": 25.00,
        "userId": "user-12345",
        "updatedAt": "2024-01-15T10:30:00Z",
    }


@pytest.fixture
def mock_response_factory():
    """Factory fixture that builds a mock requests.Response."""

    def _factory(status_code: int, json_body: dict | None = None, text: str = ""):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_body or {}
        mock_resp.text = text or json.dumps(json_body or {})
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.ok = 200 <= status_code < 300
        return mock_resp

    return _factory


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _put_preferences(headers: dict, payload: dict | None = None) -> requests.Response:
    """Thin wrapper around requests.put for the preferences endpoint."""
    return requests.put(ENDPOINT, headers=headers, json=payload)


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

class TestUpdateUserPreferences:
    """Tests for PUT /api/user/preferences"""

    # -----------------------------------------------------------------------
    # Happy-path: 200 OK
    # -----------------------------------------------------------------------

    @patch("requests.put")
    def test_update_only_preferred_charger_types_returns_200(
        self, mock_put, valid_auth_headers, existing_preferences, mock_response_factory
    ):
        """Only preferredChargerTypes is sent; maxDailyChargingCost stays unchanged."""
        payload = {"preferredChargerTypes": ["Level2", "DCFastCharger"]}

        expected_body = {
            **existing_preferences,
            "preferredChargerTypes": ["Level2", "DCFastCharger"],
        }
        mock_put.return_value = mock_response_factory(200, expected_body)

        response = _put_preferences(valid_auth_headers, payload)

        assert response.status_code == 200, (
            f"Expected 200 OK but got {response.status_code}"
        )
        body = response.json()
        assert body["preferredChargerTypes"] == ["Level2", "DCFastCharger"], (
            "preferredChargerTypes should reflect the updated value"
        )
        # maxDailyChargingCost must remain at its original value
        assert body["maxDailyChargingCost"] == existing_preferences["maxDailyChargingCost"], (
            "maxDailyChargingCost should remain unchanged when not provided in request"
        )
        mock_put.assert_called_once_with(ENDPOINT, headers=valid_auth_headers, json=payload)

    @patch("requests.put")
    def test_update_only_max_daily_charging_cost_returns_200(
        self, mock_put, valid_auth_headers, existing_preferences, mock_response_factory
    ):
        """Only maxDailyChargingCost is sent; preferredChargerTypes stays unchanged."""
        payload = {"maxDailyChargingCost": 50.00}

        expected_body = {**existing_preferences, "maxDailyChargingCost": 50.00}
        mock_put.return_value = mock_response_factory(200, expected_body)

        response = _put_preferences(valid_auth_headers, payload)

        assert response.status_code == 200
        body = response.json()
        assert body["maxDailyChargingCost"] == 50.00
        assert body["preferredChargerTypes"] == existing_preferences["preferredChargerTypes"], (
            "preferredChargerTypes should remain unchanged when not provided"
        )

    @patch("requests.put")
    def test_update_both_fields_returns_200(
        self, mock_put, valid_auth_headers, existing_preferences, mock_response_factory
    ):
        """Both optional fields are sent; both should be updated."""
        payload = {
            "preferredChargerTypes": ["Tesla Supercharger"],
            "maxDailyChargingCost": 100.00,
        }

        expected_body = {
            **existing_preferences,
            **payload,
        }
        mock_put.return_value = mock_response_factory(200, expected_body)

        response = _put_preferences(valid_auth_headers, payload)

        assert response.status_code == 200
        body = response.json()
        assert body["preferredChargerTypes"] == ["Tesla Supercharger"]
        assert body["maxDailyChargingCost"] == 100.00

    @patch("requests.put")
    def test_update_with_empty_body_returns_200_no_changes(
        self, mock_put, valid_auth_headers, existing_preferences, mock_response_factory
    ):
        """An empty body should be accepted; nothing changes (idempotent)."""
        payload = {}
        mock_put.return_value = mock_response_factory(200, existing_preferences)

        response = _put_preferences(valid_auth_headers, payload)

        assert response.status_code == 200
        body = response.json()
        assert body == existing_preferences, (
            "No fields were provided so existing preferences should be returned unchanged"
        )

    @pytest.mark.parametrize(
        "cost",
        [0, 0.0, 0.01, 999999.99],
        ids=["zero_int", "zero_float", "min_positive", "large_positive"],
    )
    @patch("requests.put")
    def test_update_max_daily_charging_cost_boundary_values_returns