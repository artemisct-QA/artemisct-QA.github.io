

```python
"""
Test suite for Plug & Charge (PnC) Authorization API endpoint.

Covers:
  - POST /api/pnc/authorize
  - 200 OK: successful authorization with authCode returned
  - 401 Unauthorized: invalid VIN
  - 403 Forbidden: PnC not enabled for vehicle/account
  - 409 Conflict: active charging session already exists
  - Edge cases: missing fields, malformed payloads, expired tokens, etc.
"""

import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import requests


# ---------------------------------------------------------------------------
# Production helper / client that would normally live in src/
# ---------------------------------------------------------------------------
class PnCAuthClient:
    """Thin wrapper around the PnC authorization endpoint."""

    def __init__(self, base_url: str, bearer_token: str | None = None):
        self.base_url = base_url.rstrip("/")
        self.bearer_token = bearer_token

    def authorize(self, vin: str | None = None, pnc_token: str | None = None,
                  extra_payload: dict | None = None) -> requests.Response:
        """POST /api/pnc/authorize with the given VIN and pncToken."""
        url = f"{self.base_url}/api/pnc/authorize"
        headers = {"Content-Type": "application/json"}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        payload: dict = {}
        if vin is not None:
            payload["vin"] = vin
        if pnc_token is not None:
            payload["pncToken"] = pnc_token
        if extra_payload:
            payload.update(extra_payload)

        return requests.post(url, json=payload, headers=headers, timeout=10)


# ---------------------------------------------------------------------------
# Test data factories
# ---------------------------------------------------------------------------
def _valid_vin() -> str:
    """Return a realistic 17-char VIN."""
    return "1HGCM82633A004352"


def _valid_pnc_token() -> str:
    """Return a realistic PnC token (UUID-based for tests)."""
    return str(uuid.uuid4())


def _auth_code() -> str:
    """Return a realistic authorization code."""
    return f"AUTH-{uuid.uuid4().hex[:12].upper()}"


def _success_response_body(auth_code: str | None = None) -> dict:
    return {
        "status": "AUTHORIZED",
        "authCode": auth_code or _auth_code(),
        "expiresAt": (datetime.utcnow() + timedelta(minutes=15)).isoformat() + "Z",
    }


def _error_response_body(code: str, message: str) -> dict:
    return {
        "error": code,
        "message": message,
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def base_url():
    return "https://pnc.example.com"


@pytest.fixture
def bearer_token():
    return "test-bearer-token-abc123"


@pytest.fixture
def client(base_url, bearer_token):
    """Return a PnCAuthClient wired to the test base_url."""
    return PnCAuthClient(base_url=base_url, bearer_token=bearer_token)


@pytest.fixture
def mock_post():
    """Patch requests.post so no real HTTP calls are made."""
    with patch("requests.post") as mocked:
        yield mocked


def _build_mock_response(status_code: int, json_body: dict) -> MagicMock:
    """Create a MagicMock that behaves like a requests.Response."""
    resp = MagicMock(spec=requests.Response)
    resp.status_code = status_code
    resp.json.return_value = json_body
    resp.ok = 200 <= status_code < 300
    resp.text = str(json_body)
    resp.headers = {"Content-Type": "application/json"}
    return resp


# ---------------------------------------------------------------------------
# TEST CLASS
# ---------------------------------------------------------------------------
class TestPnCAuthorize:
    """Tests for POST /api/pnc/authorize."""

    # ---- Happy-path tests ------------------------------------------------

    def test_successful_authorization_returns_200_and_auth_code(
        self, client, mock_post
    ):
        """A valid VIN + pncToken should return 200 with an authCode."""
        expected_auth_code = _auth_code()
        body = _success_response_body(auth_code=expected_auth_code)
        mock_post.return_value = _build_mock_response(200, body)

        response = client.authorize(vin=_valid_vin(), pnc_token=_valid_pnc_token())

        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}"
        )
        data = response.json()
        assert "authCode" in data, "Response body must contain 'authCode'"
        assert data["authCode"] == expected_auth_code
        assert data["status"] == "AUTHORIZED"

    def test_successful_authorization_contains_expiry(self, client, mock_post):
        """200 response must include an expiresAt timestamp."""
        body = _success_response_body()
        mock_post.return_value = _build_mock_response(200, body)

        response = client.authorize(vin=_valid_vin(), pnc_token=_valid_pnc_token())

        data = response.json()
        assert "expiresAt" in data, "Response must include 'expiresAt'"
        # Verify the timestamp is parseable
        expiry = datetime.fromisoformat(data["expiresAt"].replace("Z", "+00:00"))
        assert expiry > datetime.now(expiry.tzinfo), "expiresAt should be in the future"

    def test_request_sends_correct_headers_and_payload(
        self, client, mock_post, base_url, bearer_token
    ):
        """Verify the client sends the right URL, headers, and JSON body."""
        mock_post.return_value = _build_mock_response(200, _success_response_body())
        vin = _valid_vin()
        token = _valid_pnc_token()

        client.authorize(vin=vin, pnc_token=token)

        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs.args[0] == f"{base_url}/api/pnc/authorize" or \
               call_kwargs.kwargs.get("url") == f"{base_url}/api/pnc/authorize" or \
               call_kwargs[0][0] == f"{base_url}/api/pnc/authorize"

        # Check JSON payload
        sent_json = call_kwargs.kwargs.get("json") or call_kwargs[1].get("json")
        assert sent_json["vin"] == vin
        assert sent_json["pncToken"] == token

        # Check Authorization header
        sent_headers = call_kwargs.kwargs.get("headers") or call_kwargs[1].get("headers")
        assert sent_headers["Authorization"] == f"Bearer {bearer_token}"

    # ---- 401 Invalid VIN -------------------------------------------------

    @pytest.mark.parametrize(
        "invalid_vin, description",
        [
            ("INVALID_VIN_12345", "wrong-format VIN"),
            ("", "empty string VIN"),
            ("1234567890ABCDEFG", "unregistered VIN"),
            ("00000000000000000", "all-zeros VIN"),
        ],
        ids=["wrong-format", "empty-string", "unregistered", "all-zeros"],
    )
    def test_invalid_