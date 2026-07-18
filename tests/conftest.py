import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

@pytest.fixture(autouse=True)
def mock_nats_event_bus():
    with patch("nova_event_bus.NatsEventBus.connect", new_callable=AsyncMock) as mock_connect, \
         patch("nova_event_bus.NatsEventBus.disconnect", new_callable=AsyncMock) as mock_disconnect:
        yield mock_connect, mock_disconnect

@pytest.fixture
def client(mock_nats_event_bus):
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        with TestClient(app) as client:
            # Adjuntamos los mocks al cliente por si algún test necesita verificar llamadas
            client.mock_register_capabilities = mock_reg
            client.mock_connect = mock_nats_event_bus[0]
            client.mock_disconnect = mock_nats_event_bus[1]
            yield client
