import pytest
import httpx
from unittest.mock import patch, AsyncMock
from core.models import PluginContext
from plugins.repeat.main import RepeatPlugin
from core.context_service_client import LastResponseInfo, ContextServiceClient

@pytest.fixture
def plugin():
    plugin_instance = RepeatPlugin()
    plugin_instance.initialize()
    return plugin_instance

def test_repeat_plugin_properties(plugin):
    assert plugin.id == "repeat"
    assert plugin.priority == 70
    assert plugin.name == "RepeatPlugin"
    assert "Repite." in plugin.examples
    assert "¿Puedes repetir?" in plugin.examples
    assert len(plugin.examples) == 8

@pytest.mark.asyncio
async def test_repeat_plugin_success(plugin):
    mock_info = LastResponseInfo(response="Hoy es lunes.", plugin="weather", timestamp="2026-07-19T07:52:25Z")
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Hoy es lunes."
        assert result.data == {
            "repeated_plugin": "weather",
            "repeated_timestamp": "2026-07-19T07:52:25Z"
        }

@pytest.mark.asyncio
async def test_repeat_plugin_no_context(plugin):
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "No hay respuestas anteriores."
        assert result.data is None

@pytest.mark.asyncio
async def test_repeat_plugin_connection_error(plugin):
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_repeat_plugin_timeout(plugin):
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_repeat_plugin_http_error(plugin):
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Internal Server Error")
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."

@pytest.mark.asyncio
async def test_repeat_plugin_generic_error(plugin):
    with patch.object(plugin.client, "get_last_response", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ValueError("Some unexpected error")
        context = PluginContext(raw_text="Repite.", normalized_text="repite")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."

@pytest.mark.asyncio
async def test_context_client_success():
    client = ContextServiceClient(base_url="http://test-service")
    
    mock_response = httpx.Response(200, json={
        "response": "Hola",
        "plugin": "greeting",
        "timestamp": "2026-07-19"
    }, request=httpx.Request("GET", "http://test-service/v1/context/last-response"))
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get_last_response()
        assert result is not None
        assert result.response == "Hola"
        assert result.plugin == "greeting"
        assert result.timestamp == "2026-07-19"

@pytest.mark.asyncio
async def test_context_client_404():
    client = ContextServiceClient(base_url="http://test-service")
    
    mock_response = httpx.Response(404, request=httpx.Request("GET", "http://test-service/v1/context/last-response"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get_last_response()
        assert result is None

@pytest.mark.asyncio
async def test_context_client_error():
    client = ContextServiceClient(base_url="http://test-service")
    
    mock_response = httpx.Response(500, request=httpx.Request("GET", "http://test-service/v1/context/last-response"))
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(httpx.HTTPStatusError):
            await client.get_last_response()
