import pytest
import httpx
import re
from unittest.mock import patch, AsyncMock
from core.models import PluginContext
from plugins.identity.main import IdentityPlugin, build_display_name
from core.system_service_client import SystemInfo

@pytest.fixture
def plugin():
    plugin_instance = IdentityPlugin()
    plugin_instance.initialize()
    return plugin_instance

@pytest.mark.asyncio
async def test_identity_plugin_success(plugin):
    mock_info = SystemInfo(
        name="Nova",
        author="David",
        version="2.5.0",
        description="Asistente personal de voz y automatización"
    )
    with patch.object(plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Quién eres?", normalized_text="quien eres")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Soy Nova-2, tu sistema local de automatización."
        assert result.data == {
            "name": "Nova",
            "version": "2.5.0",
            "display_name": "Nova-2"
        }

@pytest.mark.asyncio
async def test_identity_plugin_different_name_and_version(plugin):
    mock_info = SystemInfo(
        name="Nova Enterprise",
        author="David",
        version="3.12.8",
        description="Asistente personal de voz y automatización"
    )
    with patch.object(plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Quién eres?", normalized_text="quien eres")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Soy Nova Enterprise-3, tu sistema local de automatización."
        assert result.data == {
            "name": "Nova Enterprise",
            "version": "3.12.8",
            "display_name": "Nova Enterprise-3"
        }

@pytest.mark.asyncio
async def test_identity_plugin_connection_error(plugin):
    with patch.object(plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Quién eres?", normalized_text="quien eres")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_identity_plugin_timeout(plugin):
    with patch.object(plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")
        context = PluginContext(raw_text="¿Quién eres?", normalized_text="quien eres")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_identity_plugin_invalid_version_format(plugin):
    invalid_versions = ["2", "2.5", "2.5.0.0", "a.b.c", "2.5.a"]
    for version in invalid_versions:
        mock_info = SystemInfo(
            name="Nova",
            author="David",
            version=version,
            description="Asistente personal de voz y automatización"
        )
        with patch.object(plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_info
            context = PluginContext(raw_text="¿Quién eres?", normalized_text="quien eres")
            result = await plugin.execute(context)
            
            assert result.success is False
            assert result.speech == "No he podido obtener la información."



def test_identity_plugin_properties(plugin):
    assert plugin.id == "identity"
    assert plugin.priority == 60
    assert len(plugin.examples) == 10
    assert "¿Quién eres?" in plugin.examples
    assert "Dime quién eres." in plugin.examples
