import pytest
import httpx
from unittest.mock import patch, AsyncMock, MagicMock
from core.models import PluginContext
from core.host_service_client import HostServiceClient, AudioState
from plugins.volume.main import VolumeSetPlugin


# -----------------
# HostServiceClient.set_volume Tests
# -----------------

@pytest.mark.asyncio
async def test_host_service_client_set_volume():
    client = HostServiceClient(base_url="http://localhost:8007")
    mock_response = MagicMock()
    mock_response.json.return_value = {"volume": 50, "muted": False}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        result = await client.set_volume(50)

        assert isinstance(result, AudioState)
        assert result.volume == 50
        assert result.muted is False
        mock_post.assert_called_once_with(
            "http://localhost:8007/v1/audio/volume/set",
            json={"volume": 50}
        )


# -----------------
# VolumeSetPlugin Unit Tests
# -----------------

@pytest.mark.asyncio
async def test_volume_set_plugin_success():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    mock_state = AudioState(volume=50, muted=False)
    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.return_value = mock_state
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": 50}
        )
        result = await plugin.execute(context)

        assert result.success is True
        assert result.speech == "Volumen al 50 por ciento."
        assert result.data == {"volume": 50, "muted": False}
        mock_set.assert_called_once_with(50)


@pytest.mark.asyncio
async def test_volume_set_plugin_lower_bound_zero():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    mock_state = AudioState(volume=0, muted=False)
    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.return_value = mock_state
        context = PluginContext(
            raw_text="Pon el volumen al 0",
            normalized_text="pon el volumen al 0",
            parameters={"volume": 0}
        )
        result = await plugin.execute(context)

        assert result.success is True
        assert result.speech == "Volumen al 0 por ciento."
        assert result.data == {"volume": 0, "muted": False}
        mock_set.assert_called_once_with(0)


@pytest.mark.asyncio
async def test_volume_set_plugin_upper_bound_100():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    mock_state = AudioState(volume=100, muted=False)
    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.return_value = mock_state
        context = PluginContext(
            raw_text="Pon el volumen al 100",
            normalized_text="pon el volumen al 100",
            parameters={"volume": 100}
        )
        result = await plugin.execute(context)

        assert result.success is True
        assert result.speech == "Volumen al 100 por ciento."
        assert result.data == {"volume": 100, "muted": False}
        mock_set.assert_called_once_with(100)


@pytest.mark.asyncio
async def test_volume_set_plugin_missing_parameter():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        context = PluginContext(
            raw_text="Pon el volumen",
            normalized_text="pon el volumen",
            parameters={}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Indica un nivel de volumen."
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_volume_set_plugin_out_of_range_negative():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        context = PluginContext(
            raw_text="Pon el volumen a menos diez",
            normalized_text="pon el volumen a menos diez",
            parameters={"volume": -10}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Indica un volumen entre 0 y 100."
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_volume_set_plugin_out_of_range_exceeds_max():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        context = PluginContext(
            raw_text="Pon el volumen al 120",
            normalized_text="pon el volumen al 120",
            parameters={"volume": 120}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Indica un volumen entre 0 y 100."
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_volume_set_plugin_invalid_type():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": "50"}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Indica un volumen entre 0 y 100."
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_volume_set_plugin_boolean_type_rejected():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": True}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Indica un volumen entre 0 y 100."
        mock_set.assert_not_called()


@pytest.mark.asyncio
async def test_volume_set_plugin_connection_error():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": 50}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."


@pytest.mark.asyncio
async def test_volume_set_plugin_timeout():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.side_effect = httpx.TimeoutException("Timeout")
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": 50}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."


@pytest.mark.asyncio
async def test_volume_set_plugin_generic_error():
    plugin = VolumeSetPlugin()
    plugin.initialize()

    with patch.object(plugin.client, "set_volume", new_callable=AsyncMock) as mock_set:
        mock_set.side_effect = Exception("Generic error")
        context = PluginContext(
            raw_text="Pon el volumen al 50",
            normalized_text="pon el volumen al 50",
            parameters={"volume": 50}
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "No he podido completar la operación."


def test_volume_set_plugin_metadata():
    plugin = VolumeSetPlugin()
    assert plugin.id == "volume-set"
    assert plugin.name == "VolumeSetPlugin"
    assert plugin.priority == 60
    assert len(plugin.parameters) == 1
    assert plugin.parameters[0].name == "volume"
    assert plugin.parameters[0].type == "Integer"
    assert plugin.parameters[0].required is True
    assert len(plugin.examples) > 0
