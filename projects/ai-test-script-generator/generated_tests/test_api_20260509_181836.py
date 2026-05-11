

```python
"""
Test suite for GET /api/status endpoint.

This module tests the /api/status endpoint which returns battery status information
including batteryPercent and chargingState fields.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import requests


# --- Configuration & Constants ---
BASE_URL = "http://localhost:8080"
STATUS_ENDPOINT = f"{BASE_URL}/api/status"
DEFAULT_TIMEOUT = 5


# --- Fixtures ---

@pytest.fixture
def mock_response_factory():
    """Factory fixture to create mock response objects with customizable attributes."""
    def _create_response(
        status_code=200,
        json_data=None,
        raise_for_status_error=None,
        headers=None,
        text="",
        raise_on_call=None,
    ):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = status_code
        mock_resp.headers = headers or {"Content-Type": "application/json"}
        mock_resp.text = text or (json.dumps(json_data) if json_data else "")

        if json_data is not None:
            mock_resp.json.return_value = json_data
        else:
            mock_resp.json.side_effect = json.JSONDecodeError("No JSON", "", 0)

        if raise_for_status_error:
            mock_resp.raise_for_status.side_effect = raise_for_status_error
        else:
            mock_resp.raise_for_status.return_value = None

        return mock_resp

    return _create_response


@pytest.fixture
def valid_status_response(mock_response_factory):
    """Fixture providing a standard valid status response."""
    return mock_response_factory(
        status_code=200,
        json_data={
            "batteryPercent": 75,
            "chargingState": "charging"
        }
    )


@pytest.fixture
def auth_headers():
    """Fixture providing standard authentication headers."""
    return {
        "Authorization": "Bearer test-token-abc123",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }


# --- Test Class: Happy Path ---

class TestGetStatusHappyPath:
    """Tests for successful responses from GET /api/status."""

    @patch("requests.get")
    def test_returns_200_status_code(self, mock_get, valid_status_response):
        """Verify the endpoint returns HTTP 200 on a successful request."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)

        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}"
        )
        mock_get.assert_called_once_with(STATUS_ENDPOINT)

    @patch("requests.get")
    def test_response_contains_battery_percent(self, mock_get, valid_status_response):
        """Verify the response JSON contains the 'batteryPercent' field."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert "batteryPercent" in data, (
            "Response JSON missing required field 'batteryPercent'"
        )

    @patch("requests.get")
    def test_response_contains_charging_state(self, mock_get, valid_status_response):
        """Verify the response JSON contains the 'chargingState' field."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert "chargingState" in data, (
            "Response JSON missing required field 'chargingState'"
        )

    @patch("requests.get")
    def test_battery_percent_is_integer(self, mock_get, valid_status_response):
        """Verify batteryPercent is returned as an integer type."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert isinstance(data["batteryPercent"], int), (
            f"Expected batteryPercent to be int, got {type(data['batteryPercent']).__name__}"
        )

    @patch("requests.get")
    def test_charging_state_is_string(self, mock_get, valid_status_response):
        """Verify chargingState is returned as a string type."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert isinstance(data["chargingState"], str), (
            f"Expected chargingState to be str, got {type(data['chargingState']).__name__}"
        )

    @patch("requests.get")
    def test_response_content_type_is_json(self, mock_get, valid_status_response):
        """Verify the response Content-Type header is application/json."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)

        assert response.headers["Content-Type"] == "application/json", (
            f"Expected Content-Type 'application/json', got '{response.headers.get('Content-Type')}'"
        )

    @patch("requests.get")
    def test_authenticated_request_succeeds(self, mock_get, mock_response_factory, auth_headers):
        """Verify that an authenticated request returns 200 with valid data."""
        mock_get.return_value = mock_response_factory(
            status_code=200,
            json_data={"batteryPercent": 90, "chargingState": "full"}
        )

        response = requests.get(STATUS_ENDPOINT, headers=auth_headers)

        assert response.status_code == 200
        mock_get.assert_called_once_with(STATUS_ENDPOINT, headers=auth_headers)


# --- Test Class: Battery Percent Boundary Values ---

class TestBatteryPercentBoundaries:
    """Tests for various batteryPercent values including boundary conditions."""

    @pytest.mark.parametrize(
        "battery_percent, description",
        [
            (0, "empty battery"),
            (1, "minimum non-zero battery"),
            (25, "quarter battery"),
            (50, "half battery"),
            (75, "three-quarter battery"),
            (99, "near-full battery"),
            (100, "full battery"),
        ],
        ids=lambda val: val if isinstance(val, str) else f"battery_{val}%"
    )
    @patch("requests.get")
    def test_valid_battery_percent_values(
        self, mock_get, mock_response_factory, battery_percent, description
    ):
        """Verify batteryPercent is correctly returned for valid percentage values."""
        mock_get.return_value = mock_response_factory(
            status_code=200,
            json_data={
                "batteryPercent": battery_percent,
                "chargingState": "discharging"
            }
        )

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert data["batteryPercent"] == battery_percent, (
            f"Expected batteryPercent={battery_percent} for {description}, "
            f"got {data['batteryPercent']}"
        )

    @patch("requests.get")
    def test_battery_percent_within_valid_range(self, mock_get, valid_status_response):
        """Verify batteryPercent falls within the valid 0-100 range."""
        mock_get.return_value = valid_status_response

        response = requests.get(STATUS_ENDPOINT)
        data = response.json()

        assert 0 <= data["batteryPercent"] <= 100, (
            f"batteryPercent {data['batteryPercent']} is outside valid range