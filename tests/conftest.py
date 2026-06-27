import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        with TestClient(app) as client:
            # Adjuntamos el mock al cliente por si algún test necesita verificar llamadas
            client.mock_register_capabilities = mock_reg
            yield client
