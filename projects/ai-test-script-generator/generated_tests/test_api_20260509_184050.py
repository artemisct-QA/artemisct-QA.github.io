

```python
"""
Test suite for Connected Services Activation API
Endpoint: POST /api/services/activate
"""

import pytest
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta
import requests


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def base_url():
    """Base URL for the API."""
    return "https://api.example.com"


@pytest.fixture
def activate_endpoint(base_url):
    """Full URL for the service activation endpoint."""
    return f"{base_url}/api/services/activate"


@pytest.fixture
def auth_headers():
    """Standard authentication headers with Bearer token."""
    return {
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.test-token",
        "Content-Type": "application/json",
        "X-Request-ID": "test-request-id-12345",
    }


@pytest.fixture
def valid_billing_info():
    """Valid billing information payload."""
    return {
        "cardNumber": "4111111111111111",
        "expirationDate": "12/2027",
        "cvv": "123",
        "billingAddress": {
            "street": "123 Main Street",
            "city": "San Francisco",
            "state": "CA",
            "zipCode": "94105",
            "country": "US",
        },
        "cardholderName": "John Doe",
    }


@pytest.fixture
def valid_activation_payload(valid_billing_info):
    """Valid service activation request payload."""
    return {
        "serviceId": "svc_premium_streaming_001",
        "billingInfo": valid_billing_info,
    }


@pytest.fixture
def successful_activation_response():
    """Mock response for successful service activation (200)."""
    return {
        "status": "activated",
        "serviceId": "svc_premium_streaming_001",
        "activationId": "act_abc123def456",
        "activatedAt": datetime.utcnow().isoformat() + "Z",
        "expiresAt": (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z",
        "billingConfirmation": {
            "transactionId": "txn_789xyz",
            "amount": 14.99,
            "currency": "USD",
            "receiptUrl": "https://billing.example.com/receipts/txn_789xyz",
        },
        "message": "Service activated successfully.",
    }


@pytest.fixture
def mock_session():
    """Create a mock requests session."""
    with patch("requests.Session") as mock:
        session_instance = MagicMock()
        mock.return_value = session_instance
        yield session_instance


# ============================================================================
# Service Activation Client (System Under Test)
# ============================================================================

class ServiceActivationClient:
    """Client for interacting with the service activation API."""

    def __init__(self, base_url: str, auth_token: str):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json",
        })

    def activate_service(self, service_id: str, billing_info: dict) -> requests.Response:
        """Activate a connected service with billing information."""
        payload = {
            "serviceId": service_id,
            "billingInfo": billing_info,
        }
        return self.session.post(
            f"{self.base_url}/api/services/activate",
            json=payload,
        )


# ============================================================================
# Test Class: Service Activation API
# ============================================================================

class TestServiceActivation:
    """Test suite for POST /api/services/activate endpoint."""

    # ========================================================================
    # Happy Path Tests (200 OK)
    # ========================================================================

    @patch("requests.Session")
    def test_successful_activation_returns_200(
        self, mock_session_cls, base_url, valid_billing_info, successful_activation_response
    ):
        """Test that a valid activation request returns 200 with activation details."""
        # Arrange
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = successful_activation_response
        mock_response.headers = {"Content-Type": "application/json"}
        mock_session.post.return_value = mock_response

        client = ServiceActivationClient(base_url, "valid-test-token")

        # Act
        response = client.activate_service("svc_premium_streaming_001", valid_billing_info)

        # Assert
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        response_data = response.json()
        assert response_data["status"] == "activated"
        assert response_data["serviceId"] == "svc_premium_streaming_001"
        assert "activationId" in response_data
        assert "activatedAt" in response_data
        assert "expiresAt" in response_data
        assert "billingConfirmation" in response_data

    @patch("requests.Session")
    def test_successful_activation_contains_billing_confirmation(
        self, mock_session_cls, base_url, valid_billing_info, successful_activation_response
    ):
        """Test that successful activation includes complete billing confirmation."""
        # Arrange
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = successful_activation_response
        mock_session.post.return_value = mock_response

        client = ServiceActivationClient(base_url, "valid-test-token")

        # Act
        response = client.activate_service("svc_premium_streaming_001", valid_billing_info)

        # Assert
        billing = response.json()["billingConfirmation"]
        assert "transactionId" in billing, "Billing confirmation must include transactionId"
        assert "amount" in billing, "Billing confirmation must include amount"
        assert "currency" in billing, "Billing confirmation must include currency"
        assert billing["amount"] > 0, "Billing amount must be positive"
        assert billing["currency"] == "USD", "Currency should be USD"

    @patch("requests.Session")
    def test_successful_activation_sends_correct_payload(
        self, mock_session_cls, base_url, valid_billing_info
    ):
        """Test that the client sends the correct payload structure to the API."""
        # Arrange
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "activated"}
        mock_session.post.return_value = mock_response

        client = ServiceActivationClient(base_url, "valid-test-token")

        # Act
        client.activate_service("svc_premium_streaming_001", valid_billing_info)

        # Assert
        mock_session.post.assert_called_once()
        call_args = mock_session.post.call_args
        assert call_args[0][0] == f"{base_url}/api/services/activate"
        sent_payload = call_args[1]["json"]
        assert sent_payload["serviceId"] == "svc_premium_streaming_001"
        assert sent_payload["billingInfo"] == valid_billing_info

    @pytest.mark.parametrize(
        "service_id, description",
        [
            ("svc_premium_streaming_001", "premium