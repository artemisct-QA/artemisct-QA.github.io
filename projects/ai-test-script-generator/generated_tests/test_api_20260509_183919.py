

```python
"""
Test suite for Vehicle State Machine API - POST /api/vehicle/state/update

Tests cover:
- Happy path: valid state transitions (200 OK)
- Invalid state requests (400 Bad Request)
- State conflict scenarios (409 Conflict)
- Service unavailable scenarios (503 Service Unavailable)
- Edge cases: missing fields, malformed payloads, auth failures, etc.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import requests


# ─── Domain Constants ───────────────────────────────────────────────────────────

class VehicleState(str, Enum):
    PARKED = "PARKED"
    IDLE = "IDLE"
    IN_TRANSIT = "IN_TRANSIT"
    MAINTENANCE = "MAINTENANCE"
    OUT_OF_SERVICE = "OUT_OF_SERVICE"
    CHARGING = "CHARGING"
    RESERVED = "RESERVED"


# Valid state transitions map (from_state -> set of allowed to_states)
VALID_TRANSITIONS = {
    VehicleState.PARKED: {VehicleState.IDLE, VehicleState.MAINTENANCE, VehicleState.RESERVED},
    VehicleState.IDLE: {VehicleState.IN_TRANSIT, VehicleState.PARKED, VehicleState.CHARGING},
    VehicleState.IN_TRANSIT: {VehicleState.IDLE, VehicleState.PARKED},
    VehicleState.MAINTENANCE: {VehicleState.PARKED, VehicleState.OUT_OF_SERVICE},
    VehicleState.OUT_OF_SERVICE: {VehicleState.MAINTENANCE},
    VehicleState.CHARGING: {VehicleState.IDLE, VehicleState.PARKED},
    VehicleState.RESERVED: {VehicleState.IDLE, VehicleState.PARKED},
}

BASE_URL = "https://api.fleet.example.com"
ENDPOINT = f"{BASE_URL}/api/vehicle/state/update"


# ─── API Client Under Test ──────────────────────────────────────────────────────

class VehicleStateClient:
    """Client wrapper for the Vehicle State Machine API."""

    def __init__(self, base_url: str, api_token: str, timeout: int = 30):
        self.base_url = base_url
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        })

    def update_state(
        self,
        vehicle_id: str,
        new_state: str,
        reason: str,
        operator_id: Optional[str] = None,
    ) -> requests.Response:
        """Send a state update request for a vehicle."""
        payload = {
            "vehicleId": vehicle_id,
            "newState": new_state,
            "reason": reason,
        }
        if operator_id:
            payload["operatorId"] = operator_id

        return self.session.post(
            f"{self.base_url}/api/vehicle/state/update",
            json=payload,
            timeout=self.timeout,
        )


# ─── Fixtures ────────────────────────────────────────────────────────────────────

@pytest.fixture
def api_token():
    """Provide a valid Bearer token for authenticated requests."""
    return "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.test-token-valid"


@pytest.fixture
def client(api_token):
    """Create a VehicleStateClient instance."""
    return VehicleStateClient(base_url=BASE_URL, api_token=api_token)


@pytest.fixture
def mock_session(client):
    """Patch the internal requests.Session.post so no real HTTP calls are made."""
    with patch.object(client.session, "post") as mock_post:
        yield mock_post


def _build_mock_response(status_code: int, json_body: dict, headers: Optional[dict] = None) -> MagicMock:
    """Helper: construct a mock requests.Response."""
    mock_resp = MagicMock(spec=requests.Response)
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_body
    mock_resp.text = json.dumps(json_body)
    mock_resp.headers = headers or {"Content-Type": "application/json"}
    mock_resp.ok = 200 <= status_code < 300
    mock_resp.raise_for_status.side_effect = (
        None if mock_resp.ok else requests.HTTPError(response=mock_resp)
    )
    return mock_resp


# ─── 200 OK – Happy Path Tests ──────────────────────────────────────────────────

class TestVehicleStateUpdateSuccess:
    """Tests for successful state transitions (HTTP 200)."""

    @pytest.mark.parametrize(
        "current_state, new_state, reason",
        [
            (VehicleState.PARKED, VehicleState.IDLE, "Driver starting shift"),
            (VehicleState.IDLE, VehicleState.IN_TRANSIT, "Dispatched to pickup location"),
            (VehicleState.IN_TRANSIT, VehicleState.PARKED, "Delivery completed"),
            (VehicleState.PARKED, VehicleState.MAINTENANCE, "Scheduled oil change"),
            (VehicleState.MAINTENANCE, VehicleState.PARKED, "Maintenance completed"),
            (VehicleState.IDLE, VehicleState.CHARGING, "Battery below 20%"),
            (VehicleState.CHARGING, VehicleState.IDLE, "Battery fully charged"),
            (VehicleState.PARKED, VehicleState.RESERVED, "Customer reservation #R-4421"),
            (VehicleState.RESERVED, VehicleState.IDLE, "Customer picked up vehicle"),
        ],
        ids=lambda val: val.value if isinstance(val, VehicleState) else str(val)[:30],
    )
    def test_valid_state_transition_returns_200(
        self, client, mock_session, current_state, new_state, reason
    ):
        """Verify that all legitimate state transitions return 200 with confirmed state."""
        vehicle_id = "VH-1001"
        response_body = {
            "vehicleId": vehicle_id,
            "previousState": current_state.value,
            "currentState": new_state.value,
            "reason": reason,
            "timestamp": "2024-11-15T10:30:00Z",
            "confirmed": True,
        }
        mock_session.return_value = _build_mock_response(200, response_body)

        response = client.update_state(vehicle_id, new_state.value, reason)

        assert response.status_code == 200, f"Expected 200 but got {response.status_code}"
        body = response.json()
        assert body["currentState"] == new_state.value, "Confirmed state must match requested state"
        assert body["confirmed"] is True, "Response should confirm the transition"
        assert body["vehicleId"] == vehicle_id
        assert body["reason"] == reason

        # Verify the request was made with correct payload
        mock_session.assert_called_once()
        call_kwargs = mock_session.call_args
        sent_payload = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_payload["newState"] == new_state.value
        assert sent_payload["reason"] == reason

    def test_state_update_with_operator_id(self, client, mock_session):
        """Verify that an optional operatorId is forwarded in the payload