import time
import jwt
import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app
from core.config import settings

@pytest.fixture(autouse=True)
def mock_nats_event_bus():
    with patch("nova_event_bus.NatsEventBus.connect", new_callable=AsyncMock) as mock_connect, \
         patch("nova_event_bus.NatsEventBus.disconnect", new_callable=AsyncMock) as mock_disconnect:
        yield mock_connect, mock_disconnect

@pytest.fixture(autouse=True)
def mock_security_client_registration():
    with patch("core.security_client.SecurityClient.register_actions", new_callable=AsyncMock):
        yield

@pytest.fixture(autouse=True)
def auto_sign_test_tokens(request):
    if "test_token_enforcement" in request.node.name or "enforce_security" in request.keywords:
        yield
        return

    from core.token_verifier import verify_step_token as orig_verify
    def flex_verify(token, expected_correlation_id, expected_action_id, secret=None):
        if not token:
            now = int(time.time())
            payload = {
                "execution_id": expected_correlation_id,
                "action_id": expected_action_id,
                "audience": "nova-orchestrator",
                "issued_at": now,
                "expires_at": now + 300,
                "nonce": "test-nonce"
            }
            token = jwt.encode(payload, settings.security_hmac_secret, algorithm="HS256")
        return orig_verify(token, expected_correlation_id, expected_action_id, secret)

    with patch("core.engine.verify_step_token", side_effect=flex_verify):
        yield

@pytest.fixture
def client(mock_nats_event_bus):
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        with TestClient(app) as client:
            client.mock_register_capabilities = mock_reg
            client.mock_connect = mock_nats_event_bus[0]
            client.mock_disconnect = mock_nats_event_bus[1]
            yield client
