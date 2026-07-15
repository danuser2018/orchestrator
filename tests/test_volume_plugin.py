import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from core.models import PluginContext
from core.host_service_client import HostServiceClient, AudioState
from plugins.volume.main import (
    VolumeUpPlugin,
    VolumeDownPlugin,
    VolumeStatusPlugin,
    MutePlugin,
    UnmutePlugin
)

# -----------------
# HostServiceClient Tests
# -----------------

@pytest.mark.asyncio
async def test_host_service_client_get_volume():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 60, "muted": False}
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get_volume()
        
        assert isinstance(result, AudioState)
        assert result.volume == 60
        assert result.muted is False
        mock_get.assert_called_once_with("http://localhost:8007/v1/audio/volume")

@pytest.mark.asyncio
async def test_host_service_client_volume_up():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 70, "muted": False}
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.volume_up(10)
        
        assert isinstance(result, AudioState)
        assert result.volume == 70
        assert result.muted is False
        mock_post.assert_called_once_with("http://localhost:8007/v1/audio/volume/up", json={"step": 10})

@pytest.mark.asyncio
async def test_host_service_client_volume_down():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 50, "muted": False}
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.volume_down(10)
        
        assert isinstance(result, AudioState)
        assert result.volume == 50
        assert result.muted is False
        mock_post.assert_called_once_with("http://localhost:8007/v1/audio/volume/down", json={"step": 10})

@pytest.mark.asyncio
async def test_host_service_client_mute():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 60, "muted": True}
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.mute()
        
        assert isinstance(result, AudioState)
        assert result.volume == 60
        assert result.muted is True
        mock_post.assert_called_once_with("http://localhost:8007/v1/audio/mute")

@pytest.mark.asyncio
async def test_host_service_client_unmute():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 60, "muted": False}
    mock_response.raise_for_status = MagicMock()
    
    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.unmute()
        
        assert isinstance(result, AudioState)
        assert result.volume == 60
        assert result.muted is False
        mock_post.assert_called_once_with("http://localhost:8007/v1/audio/unmute")


# -----------------
# VolumeUpPlugin Tests
# -----------------

@pytest.mark.asyncio
async def test_volume_up_plugin_success():
    plugin = VolumeUpPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=50, muted=False)
    with patch.object(plugin.client, "volume_up", new_callable=AsyncMock) as mock_up:
        mock_up.return_value = mock_state
        context = PluginContext(raw_text="Sube el volumen", normalized_text="sube el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al 50 por ciento."
        assert result.data == {"volume": 50, "muted": False}
        mock_up.assert_called_once_with(10)

@pytest.mark.asyncio
async def test_volume_up_plugin_maximum():
    plugin = VolumeUpPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=100, muted=False)
    with patch.object(plugin.client, "volume_up", new_callable=AsyncMock) as mock_up:
        mock_up.return_value = mock_state
        context = PluginContext(raw_text="Sube el volumen", normalized_text="sube el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al máximo."
        assert result.data == {"volume": 100, "muted": False}

@pytest.mark.asyncio
async def test_volume_up_plugin_connection_error():
    plugin = VolumeUpPlugin()
    plugin.initialize()
    
    with patch.object(plugin.client, "volume_up", new_callable=AsyncMock) as mock_up:
        mock_up.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="Sube el volumen", normalized_text="sube el volumen")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_volume_up_plugin_timeout():
    plugin = VolumeUpPlugin()
    plugin.initialize()
    
    with patch.object(plugin.client, "volume_up", new_callable=AsyncMock) as mock_up:
        mock_up.side_effect = httpx.TimeoutException("Timeout")
        context = PluginContext(raw_text="Sube el volumen", normalized_text="sube el volumen")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "Servicio no disponible."

@pytest.mark.asyncio
async def test_volume_up_plugin_generic_error():
    plugin = VolumeUpPlugin()
    plugin.initialize()
    
    with patch.object(plugin.client, "volume_up", new_callable=AsyncMock) as mock_up:
        mock_up.side_effect = Exception("Generic error")
        context = PluginContext(raw_text="Sube el volumen", normalized_text="sube el volumen")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido completar la operación."


# -----------------
# VolumeDownPlugin Tests
# -----------------

@pytest.mark.asyncio
async def test_volume_down_plugin_success():
    plugin = VolumeDownPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=30, muted=False)
    with patch.object(plugin.client, "volume_down", new_callable=AsyncMock) as mock_down:
        mock_down.return_value = mock_state
        context = PluginContext(raw_text="Baja el volumen", normalized_text="baja el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al 30 por ciento."
        assert result.data == {"volume": 30, "muted": False}
        mock_down.assert_called_once_with(10)

@pytest.mark.asyncio
async def test_volume_down_plugin_minimum():
    plugin = VolumeDownPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=0, muted=False)
    with patch.object(plugin.client, "volume_down", new_callable=AsyncMock) as mock_down:
        mock_down.return_value = mock_state
        context = PluginContext(raw_text="Baja el volumen", normalized_text="baja el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al mínimo."
        assert result.data == {"volume": 0, "muted": False}


# -----------------
# VolumeStatusPlugin Tests
# -----------------

@pytest.mark.asyncio
async def test_volume_status_plugin_active():
    plugin = VolumeStatusPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=60, muted=False)
    with patch.object(plugin.client, "get_volume", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_state
        context = PluginContext(raw_text="Dime el volumen", normalized_text="dime el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al 60 por ciento."
        assert result.data == {"volume": 60, "muted": False}
        mock_get.assert_called_once()

@pytest.mark.asyncio
async def test_volume_status_plugin_muted():
    plugin = VolumeStatusPlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=60, muted=True)
    with patch.object(plugin.client, "get_volume", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_state
        context = PluginContext(raw_text="Dime el volumen", normalized_text="dime el volumen")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Volumen al 60 por ciento y silenciado."
        assert result.data == {"volume": 60, "muted": True}


# -----------------
# MutePlugin Tests
# -----------------

@pytest.mark.asyncio
async def test_mute_plugin_success():
    plugin = MutePlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=60, muted=True)
    with patch.object(plugin.client, "mute", new_callable=AsyncMock) as mock_mute:
        mock_mute.return_value = mock_state
        context = PluginContext(raw_text="Silencio", normalized_text="silencio")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Hecho."
        assert result.data == {"volume": 60, "muted": True}
        mock_mute.assert_called_once()


# -----------------
# UnmutePlugin Tests
# -----------------

@pytest.mark.asyncio
async def test_unmute_plugin_success():
    plugin = UnmutePlugin()
    plugin.initialize()
    
    mock_state = AudioState(volume=60, muted=False)
    with patch.object(plugin.client, "unmute", new_callable=AsyncMock) as mock_unmute:
        mock_unmute.return_value = mock_state
        context = PluginContext(raw_text="Desmutéate", normalized_text="desmuteate")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Sonido activado."
        assert result.data == {"volume": 60, "muted": False}
        mock_unmute.assert_called_once()


# -----------------
# Metadata Tests
# -----------------

def test_volume_plugins_metadata():
    vup = VolumeUpPlugin()
    vdown = VolumeDownPlugin()
    vstatus = VolumeStatusPlugin()
    mute = MutePlugin()
    unmute = UnmutePlugin()
    
    assert vup.id == "volume-up"
    assert vup.name == "VolumeUpPlugin"
    assert vup.priority == 60
    assert len(vup.examples) > 0
    
    assert vdown.id == "volume-down"
    assert vdown.name == "VolumeDownPlugin"
    assert vdown.priority == 60
    assert len(vdown.examples) > 0
    
    assert vstatus.id == "volume-status"
    assert vstatus.name == "VolumeStatusPlugin"
    assert vstatus.priority == 60
    assert len(vstatus.examples) > 0
    
    assert mute.id == "mute"
    assert mute.name == "MutePlugin"
    assert mute.priority == 60
    assert len(mute.examples) > 0
    
    assert unmute.id == "unmute"
    assert unmute.name == "UnmutePlugin"
    assert unmute.priority == 60
    assert len(unmute.examples) > 0
    
    assert set(vup.examples).isdisjoint(set(vdown.examples))
    assert set(vup.examples).isdisjoint(set(vstatus.examples))
    assert set(vup.examples).isdisjoint(set(mute.examples))
    assert set(vup.examples).isdisjoint(set(unmute.examples))
