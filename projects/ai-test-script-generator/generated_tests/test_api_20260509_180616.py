

```python
"""
Test suite for PUT /api/user/preferences endpoint.

Tests cover:
- Partial updates (only provided fields are updated)
- Happy path scenarios (200 OK)
- Validation errors (400 Bad Request for negative cost)
- Authentication errors (401 Unauthorized)
- Invalid data errors (422 Invalid charger type)
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from copy import deepcopy


# --- Simulated Application Layer ---
# In production, these would be imported from your actual application modules.

class AuthenticationError(Exception):
    """Raised when user is not authenticated."""
    pass


class ValidationError(Exception):
    """Raised when input validation fails."""
    def __init__(self, message, status_code=400):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


VALID_CHARGER_TYPES = ["Level1", "Level2", "DCFast", "Tesla Supercharger", "CCS", "CHAdeMO"]


class UserPreferencesService:
    """Service layer for managing user preferences."""

    def __init__(self, db_client=None):
        self.db_client = db_client

    def authenticate_user(self, token: str) -> dict:
        """Verify Bearer token and return user info."""
        if not token or not token.startswith("Bearer "):
            raise AuthenticationError("Missing or invalid authorization token")
        # In real app, this would verify JWT/token against auth service
        return {"user_id": "user_123", "email": "test@example.com"}

    def validate_preferences(self, payload: dict) -> dict:
        """Validate preference fields. Only validates fields that are present."""
        validated = {}

        if "preferredChargerTypes" in payload:
            charger_types = payload["preferredChargerTypes"]
            if not isinstance(charger_types, list):
                raise ValidationError(
                    "preferredChargerTypes must be a list",
                    status_code=422
                )
            for ct in charger_types:
                if ct not in VALID_CHARGER_TYPES:
                    raise ValidationError(
                        f"Invalid charger type: '{ct}'. Valid types: {VALID_CHARGER_TYPES}",
                        status_code=422
                    )
            validated["preferredChargerTypes"] = charger_types

        if "maxDailyChargingCost" in payload:
            cost = payload["maxDailyChargingCost"]
            if not isinstance(cost, (int, float)):
                raise ValidationError(
                    "maxDailyChargingCost must be a number",
                    status_code=400
                )
            if cost < 0:
                raise ValidationError(
                    "maxDailyChargingCost cannot be negative",
                    status_code=400
                )
            validated["maxDailyChargingCost"] = cost

        if not validated:
            raise ValidationError(
                "At least one valid field must be provided",
                status_code=400
            )

        return validated

    def update_preferences(self, user_id: str, validated_data: dict) -> dict:
        """Update only the provided preference fields in the database."""
        # Simulate fetching existing preferences
        existing_prefs = self.db_client.get_preferences(user_id)

        # Merge: only update provided fields
        updated_prefs = {**existing_prefs, **validated_data}
        self.db_client.save_preferences(user_id, updated_prefs)

        return updated_prefs


def handle_put_preferences(service: UserPreferencesService, headers: dict, body: dict) -> dict:
    """
    Request handler for PUT /api/user/preferences.
    Returns a response dict with 'status_code' and 'body'.
    """
    try:
        token = headers.get("Authorization", "")
        user = service.authenticate_user(token)
    except AuthenticationError as e:
        return {"status_code": 401, "body": {"error": str(e)}}

    try:
        validated = service.validate_preferences(body)
    except ValidationError as e:
        return {"status_code": e.status_code, "body": {"error": e.message}}

    try:
        updated = service.update_preferences(user["user_id"], validated)
        return {
            "status_code": 200,
            "body": {
                "message": "Preferences updated successfully",
                "preferences": updated
            }
        }
    except Exception as e:
        return {"status_code": 500, "body": {"error": "Internal server error"}}


# --- Test Fixtures ---

@pytest.fixture
def mock_db_client():
    """Create a mock database client with default existing preferences."""
    client = MagicMock()
    client.get_preferences.return_value = {
        "preferredChargerTypes": ["Level2", "DCFast"],
        "maxDailyChargingCost": 25.00,
        "notificationEnabled": True,  # Other existing field that shouldn't be touched
    }
    client.save_preferences.return_value = True
    return client


@pytest.fixture
def service(mock_db_client):
    """Create a UserPreferencesService instance with mocked DB."""
    return UserPreferencesService(db_client=mock_db_client)


@pytest.fixture
def valid_auth_headers():
    """Return valid authorization headers."""
    return {"Authorization": "Bearer valid_token_abc123"}


@pytest.fixture
def existing_preferences():
    """Return the default existing user preferences (for assertion reference)."""
    return {
        "preferredChargerTypes": ["Level2", "DCFast"],
        "maxDailyChargingCost": 25.00,
        "notificationEnabled": True,
    }


# --- Test Class ---

class TestPutUserPreferences:
    """Test suite for PUT /api/user/preferences endpoint."""

    # ========================
    # HAPPY PATH - 200 OK
    # ========================

    def test_update_only_preferred_charger_types_returns_200(
        self, service, valid_auth_headers, mock_db_client, existing_preferences
    ):
        """When only preferredChargerTypes is provided, only that field should be updated.
        Other fields (maxDailyChargingCost, notificationEnabled) remain unchanged."""
        body = {"preferredChargerTypes": ["CCS", "CHAdeMO"]}

        response = handle_put_preferences(service, valid_auth_headers, body)

        assert response["status_code"] == 200, (
            f"Expected 200 OK but got {response['status_code']}"
        )
        prefs = response["body"]["preferences"]
        assert prefs["preferredChargerTypes"] == ["CCS", "CHAdeMO"], (
            "preferredChargerTypes should be updated to new values"
        )
        # Verify other fields remain untouched
        assert prefs["maxDailyChargingCost"] == 25.00, (
            "maxDailyChargingCost should remain unchanged when not provided"
        )
        assert prefs["notificationEnabled"] is True, (
            "notificationEnabled should remain unchanged when not provided"
        )

    def test_update_only_max_daily_charging_cost_returns_200(
        self, service, valid_auth_headers, mock_db_client, existing_preferences
    ):
        """When only maxDailyChargingCost is provided, only that field should be updated.
        preferredChargerTypes and other fields remain unchanged."""
        body = {"maxDailyChargingCost": 50.00}

        response = handle_put_preferences(service, valid_auth_headers, body)

        assert response["status_code"] == 200
        prefs = response["body"]["preferences"]
        assert prefs["maxDailyChargingCost"] == 50.00, (
            "maxDailyChargingCost should be updated to 50.00"
        )