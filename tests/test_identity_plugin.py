import pytest
import httpx
import re
from unittest.mock import patch, AsyncMock
from core.models import PluginContext
from plugins.identity.main import IdentityPlugin, build_display_name, AuthorPlugin, VersionPlugin, HelpPlugin
from core.system_service_client import SystemInfo

@pytest.fixture
def plugin():
    plugin_instance = IdentityPlugin()
    plugin_instance.initialize()
    return plugin_instance

@pytest.fixture
def author_plugin():
    plugin_instance = AuthorPlugin()
    plugin_instance.initialize()
    return plugin_instance

@pytest.fixture
def version_plugin():
    plugin_instance = VersionPlugin()
    plugin_instance.initialize()
    return plugin_instance

@pytest.fixture
def help_plugin():
    plugin_instance = HelpPlugin()
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


@pytest.mark.asyncio
async def test_author_plugin_success(author_plugin):
    mock_info = SystemInfo(
        name="Nova",
        author="Xeretre Studios",
        version="2.0.0",
        description="Asistente personal de voz y automatización"
    )
    with patch.object(author_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Quién es el autor de Nova?", normalized_text="quien es el autor de nova")
        result = await author_plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Nova ha sido desarrollada por Xeretre Studios."
        assert result.data == {
            "author": "Xeretre Studios"
        }

@pytest.mark.asyncio
async def test_author_plugin_connection_error(author_plugin):
    with patch.object(author_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Quién te ha creado?", normalized_text="quien te ha creado")
        result = await author_plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_author_plugin_http_error(author_plugin):
    with patch.object(author_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("Internal Server Error", request=None, response=None)
        context = PluginContext(raw_text="¿Quién te desarrolló?", normalized_text="quien te desarrollo")
        result = await author_plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."

@pytest.mark.asyncio
async def test_author_plugin_unexpected_exception(author_plugin):
    with patch.object(author_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Unexpected error")
        context = PluginContext(raw_text="¿Quién te ha creado?", normalized_text="quien te ha creado")
        result = await author_plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."


@pytest.mark.asyncio
async def test_version_plugin_success(version_plugin):
    mock_info = SystemInfo(
        name="Nova",
        author="David",
        version="2.5.1",
        description="Asistente personal de voz y automatización"
    )
    with patch.object(version_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        context = PluginContext(raw_text="¿Qué versión de Nova es esta?", normalized_text="que version de nova es esta")
        result = await version_plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Versión 2.5.1."
        assert result.data == {
            "version": "2.5.1"
        }

@pytest.mark.asyncio
async def test_version_plugin_connection_error(version_plugin):
    with patch.object(version_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Cuál es tu versión?", normalized_text="cual es tu version")
        result = await version_plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_version_plugin_unexpected_exception(version_plugin):
    with patch.object(version_plugin.client, "get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Unexpected error")
        context = PluginContext(raw_text="¿Cuál es tu versión?", normalized_text="cual es tu version")
        result = await version_plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."


@pytest.mark.asyncio
async def test_help_plugin_success(help_plugin):
    context = PluginContext(raw_text="¿Cómo se usa Nova?", normalized_text="como se usa nova")
    result = await help_plugin.execute(context)
    
    assert result.success is True
    assert result.speech == "Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: \"¿Qué tiempo hace?\" o \"Enciende la luz del salón.\""
    assert result.data == {}


def test_new_plugins_properties(author_plugin, version_plugin, help_plugin):
    # AuthorPlugin properties
    assert author_plugin.id == "author"
    assert author_plugin.priority == 60
    assert len(author_plugin.examples) == 10
    assert "¿Quién te ha creado?" in author_plugin.examples
    assert "¿Quién es tu creador?" in author_plugin.examples

    # VersionPlugin properties
    assert version_plugin.id == "version"
    assert version_plugin.priority == 60
    assert len(version_plugin.examples) == 10
    assert "¿Qué versión eres?" in version_plugin.examples
    assert "¿Cuál es tu versión?" in version_plugin.examples

    # HelpPlugin properties
    assert help_plugin.id == "help"
    assert help_plugin.priority == 60
    assert len(help_plugin.examples) == 10
    assert "¿Cómo se usa Nova?" in help_plugin.examples
    assert "Ayuda." in help_plugin.examples

