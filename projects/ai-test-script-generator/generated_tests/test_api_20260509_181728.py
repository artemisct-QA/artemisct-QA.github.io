

```python
"""
Test suite for GET /api/status endpoint.
Tests battery percent and charging state response fields.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
import requests


# --- Configuration ---
BASE_URL = "http://localhost:8080"
ENDPOINT = "/api/status"
FULL_URL = f"{BASE_URL}{ENDPOINT}"


# --- Fixtures ---

@pytest.fixture
def mock_response_factory():
    """Factory fixture to create mock response objects with customizable attributes."""
    def _create_response(status_code=200, json_data=None, raise_for_status_effect=None):
        mock_resp = MagicMock(spec=requests.Response)
        mock_resp.status_code = status_code
        mock_resp.json.return_value = json_data or {}
        mock_resp.text = json.dumps(json_data or {})
        mock_resp.headers = {"Content-Type": "application/json"}
        mock_resp.ok = 200 <= status_code < 300

        if raise_for_status_effect:
            mock_resp.raise_for_status.side_effect = raise_for_status_effect
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


# --- Helper / Client ---

class StatusAPIClient:
    """Simple client wrapper for the status API endpoint."""

    def __init__(self, base_url=BASE_URL, headers=None):
        self.base_url = base_url
        self.headers = headers or {}

    def get_status(self):
        """Fetch the device status."""
        return requests.get(f"{self.base_url}{ENDPOINT}", headers=self.headers)


# --- Test Class: Happy Path ---

class TestGetStatusHappyPath:
    """Tests for successful GET /api/status responses."""

    @patch("requests.get")
    def test_returns_200_status_code(self, mock_get, valid_status_response):
        """Verify the endpoint returns HTTP 200 on success."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)

        assert response.status_code == 200, (
            f"Expected status code 200, got {response.status_code}"
        )
        mock_get.assert_called_once_with(FULL_URL)

    @patch("requests.get")
    def test_response_contains_battery_percent(self, mock_get, valid_status_response):
        """Verify the response JSON contains the 'batteryPercent' field."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)
        data = response.json()

        assert "batteryPercent" in data, (
            "Response JSON missing required field 'batteryPercent'"
        )

    @patch("requests.get")
    def test_response_contains_charging_state(self, mock_get, valid_status_response):
        """Verify the response JSON contains the 'chargingState' field."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)
        data = response.json()

        assert "chargingState" in data, (
            "Response JSON missing required field 'chargingState'"
        )

    @patch("requests.get")
    def test_battery_percent_is_integer(self, mock_get, valid_status_response):
        """Verify that batteryPercent is returned as an integer."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)
        data = response.json()

        assert isinstance(data["batteryPercent"], int), (
            f"Expected batteryPercent to be int, got {type(data['batteryPercent']).__name__}"
        )

    @patch("requests.get")
    def test_charging_state_is_string(self, mock_get, valid_status_response):
        """Verify that chargingState is returned as a string."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)
        data = response.json()

        assert isinstance(data["chargingState"], str), (
            f"Expected chargingState to be str, got {type(data['chargingState']).__name__}"
        )

    @patch("requests.get")
    def test_response_content_type_is_json(self, mock_get, valid_status_response):
        """Verify the response Content-Type header is application/json."""
        mock_get.return_value = valid_status_response

        response = requests.get(FULL_URL)

        assert response.headers["Content-Type"] == "application/json", (
            f"Expected Content-Type 'application/json', got '{response.headers.get('Content-Type')}'"
        )

    @patch("requests.get")
    def test_response_has_only_expected_fields(self, mock_get, mock_response_factory):
        """Verify the response JSON contains exactly the expected fields (no extras)."""
        mock_get.return_value = mock_response_factory(
            status_code=200,
            json_data={
                "batteryPercent": 50,
                "chargingState": "discharging"
            }
        )

        response = requests.get(FULL_URL)
        data = response.json()
        expected_keys = {"batteryPercent", "chargingState"}

        assert set(data.keys()) == expected_keys, (
            f"Expected keys {expected_keys}, got {set(data.keys())}"
        )


# --- Test Class: Battery Percent Boundary Values ---

class TestBatteryPercentBoundaries:
    """Tests for batteryPercent boundary and edge values."""

    @pytest.mark.parametrize("battery_value, description", [
        (0, "battery at 0% (completely empty)"),
        (1, "battery at 1% (minimum non-zero)"),
        (50, "battery at 50% (midpoint)"),
        (99, "battery at 99% (near full)"),
        (100, "battery at 100% (fully charged)"),
    ])
    @patch("requests.get")
    def test_valid_battery_percent_values(
        self, mock_get, mock_response_factory, battery_value, description
    ):
        """Verify batteryPercent accepts valid values from 0-100: {description}."""
        mock_get.return_value = mock_response_factory(
            status_code=200,
            json_data={
                "batteryPercent": battery_value,
                "chargingState": "charging"
            }
        )

        response = requests.get(FULL_URL)
        data = response.json()

        assert data["batteryPercent"] == battery_value, (
            f"Expected batteryPercent={battery_value} for {description}, "
            f"got {data['batteryPercent']}"
        )
        assert 0 <= data["batteryPercent"] <= 100, (
            f"batteryPercent {data['batteryPercent']} is out of valid range [0, 100]"
        )


# --- Test Class: Charging State Values ---

class TestChargingStateValues:
    """Tests for various chargingState values."""

    @pytest.mark.parametrize("charging