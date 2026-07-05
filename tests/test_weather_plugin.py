import pytest
import httpx
from unittest.mock import patch, AsyncMock
from core.models import PluginContext
from plugins.weather.main import WeatherPlugin
from core.weather_service_client import WeatherInfo

@pytest.fixture
def plugin():
    plugin_instance = WeatherPlugin()
    plugin_instance.initialize()
    return plugin_instance

@pytest.mark.asyncio
async def test_weather_plugin_success_low_rain(plugin):
    mock_info = WeatherInfo(temperature=27.4, precipitation_probability=15)
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Qué tiempo hace?", normalized_text="que tiempo hace")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "27 grados. No parece que vaya a llover."
        assert result.data == {
            "temperature": 27.4,
            "precipitation_probability": 15
        }

@pytest.mark.asyncio
async def test_weather_plugin_success_high_rain(plugin):
    mock_info = WeatherInfo(temperature=18.6, precipitation_probability=75)
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Va a llover hoy?", normalized_text="va a llover hoy")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "19 grados. Es probable que llueva."
        assert result.data == {
            "temperature": 18.6,
            "precipitation_probability": 75
        }

@pytest.mark.asyncio
async def test_weather_plugin_success_all_precipitation_ranges(plugin):
    ranges = [
        (10, "No parece que vaya a llover."),
        (30, "Hay poca probabilidad de lluvia."),
        (50, "Podría llover."),
        (70, "Es probable que llueva."),
        (90, "Es muy probable que llueva.")
    ]
    for prob, expected_msg in ranges:
        mock_info = WeatherInfo(temperature=20.0, precipitation_probability=prob)
        with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_info
            context = PluginContext(raw_text="¿Qué clima hace?", normalized_text="que clima hace")
            result = await plugin.execute(context)
            assert result.success is True
            assert result.speech == f"20 grados. {expected_msg}"

@pytest.mark.asyncio
async def test_weather_plugin_connection_error(plugin):
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Qué tiempo hace?", normalized_text="que tiempo hace")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_weather_plugin_timeout(plugin):
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        context = PluginContext(raw_text="¿Qué tiempo hace?", normalized_text="que tiempo hace")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_weather_plugin_http_error(plugin):
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPError("Internal Server Error")
        context = PluginContext(raw_text="¿Qué tiempo hace?", normalized_text="que tiempo hace")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."

@pytest.mark.asyncio
async def test_weather_plugin_generic_error(plugin):
    with patch.object(plugin.client, "get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = ValueError("Some unexpected error")
        context = PluginContext(raw_text="¿Qué tiempo hace?", normalized_text="que tiempo hace")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."

def test_weather_plugin_properties(plugin):
    assert plugin.id == "weather"
    assert plugin.priority == 80
    assert len(plugin.examples) > 0
    assert "¿Qué tiempo hace?" in plugin.examples
