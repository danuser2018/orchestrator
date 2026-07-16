import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient

def test_successful_plugin_registration(client):
    # El fixture `client` ya ejecutó el lifespan y registró las capacidades.
    # Verificamos que se haya llamado a `register_capabilities`.
    client.mock_register_capabilities.assert_called_once()
    
    # Comprobar el formato de las capacidades registradas
    args, kwargs = client.mock_register_capabilities.call_args
    registered = args[0]
    
    # Deberíamos tener cargados los plugins: identity, weather, farewell, greeting, author, version, help, time, date (fallback se excluye)
    ids = [cap["id"] for cap in registered]
    assert "identity" in ids
    assert "weather" in ids
    assert "fallback" not in ids
    assert "farewell" in ids
    assert "greeting" in ids
    assert "author" in ids
    assert "version" in ids
    assert "help" in ids
    assert "time" in ids
    assert "date" in ids
    assert "coin" in ids
    assert "dice" in ids
    assert "random-number" in ids
    assert "volume-up" in ids
    assert "volume-down" in ids
    assert "volume-status" in ids
    assert "mute" in ids
    assert "unmute" in ids
    assert "today_holiday" in ids
    assert "next_holiday" in ids
    assert "days_until_next_holiday" in ids
    assert "holidays_of_year" in ids
    
    # Verificar que los campos sean strings no vacíos
    for cap in registered:
        assert isinstance(cap["id"], str)
        assert isinstance(cap["description"], str)
        assert len(cap["description"]) > 0

def test_registration_http_error_graceful():
    from main import app
    
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        # Simulamos un error HTTP de estado
        mock_reg.side_effect = httpx.HTTPStatusError(
            "500 Internal Server Error", 
            request=MagicMock(), 
            response=MagicMock()
        )
        
        with patch("main.logger") as mock_logger:
            with TestClient(app) as client:
                assert client is not None
            # Verificamos que se haya registrado una advertencia (WARNING)
            mock_logger.warning.assert_called()

def test_registration_timeout_graceful():
    from main import app
    
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        mock_reg.side_effect = httpx.TimeoutException("Connection timed out")
        
        with patch("main.logger") as mock_logger:
            with TestClient(app) as client:
                assert client is not None
            # Verificamos que se haya registrado una advertencia (WARNING)
            mock_logger.warning.assert_called()

def test_registration_unexpected_exception_graceful():
    from main import app
    
    with patch("core.system_service_client.SystemServiceClient.register_capabilities", new_callable=AsyncMock) as mock_reg:
        mock_reg.side_effect = ValueError("Unexpected database crash")
        
        with patch("main.logger") as mock_logger:
            with TestClient(app) as client:
                assert client is not None
            # Verificamos que se haya registrado un error (ERROR)
            mock_logger.error.assert_called()
