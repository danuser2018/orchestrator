import json
import re
from pathlib import Path
from unittest.mock import patch, AsyncMock, mock_open

import httpx
import pytest

from core.models import PluginContext
from core.system_service_client import Capability, CapabilityList
from plugins.capabilities.main import CapabilitiesPlugin


@pytest.fixture
def plugin():
    plugin_instance = CapabilitiesPlugin()
    plugin_instance.initialize()
    return plugin_instance


def test_capabilities_plugin_metadata(plugin):
    # Name
    assert plugin.name == "CapabilitiesPlugin"

    # Description
    assert plugin.description == (
        "Responde preguntas sobre las funciones disponibles en Nova y envía al "
        "usuario un correo con el listado completo de capacidades registradas."
    )

    # Keywords
    for kw in ["hacer", "funciones", "capacidades", "puedes", "sabes", "ayuda"]:
        assert kw in plugin.keywords

    # Regex patterns
    test_phrases = [
        "qué puedes hacer",
        "que puedes hacer",
        "qué sabes hacer",
        "que sabes hacer",
        "qué funciones tienes",
        "que funciones tienes",
        "qué eres capaz de hacer",
        "que eres capaz de hacer",
        "dime qué puedes hacer por mí",
        "quiero saber qué eres capaz de hacer hoy"
    ]
    for phrase in test_phrases:
        matched = False
        for pattern in plugin.regex_patterns:
            if re.match(pattern, phrase):
                matched = True
                break
        assert matched, f"Phrase '{phrase}' should match at least one regex pattern."


@pytest.mark.asyncio
async def test_capabilities_plugin_success(plugin, tmp_path):
    mock_caps = CapabilityList(
        capabilities=[
            Capability(id="weather", description="Consultar el tiempo"),
            Capability(id="identity", description="Información sobre Nova"),
            Capability(id="farewell", description="Despedirse del usuario")
        ]
    )

    pending_dir = tmp_path / "pending"

    # Patch system_service_client and config settings
    with patch.object(plugin.client, "get_capabilities", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_caps

        with patch("plugins.capabilities.main.settings") as mock_settings:
            mock_settings.mail_pending_dir = str(pending_dir)

            context = PluginContext(
                raw_text="¿Qué sabes hacer?",
                normalized_text="que sabes hacer"
            )

            result = await plugin.execute(context)

            # Assert execution result
            assert result.success is True
            assert "3 funciones" in result.speech
            assert "correo con el listado completo" in result.speech

            # Verify files were created
            generated_files = list(pending_dir.glob("mail-*.json"))
            assert len(generated_files) == 1

            mail_file = generated_files[0]
            with open(mail_file, "r", encoding="utf-8") as f:
                mail_data = json.load(f)

            assert "to" not in mail_data
            assert mail_data["subject"] == "Capacidades disponibles en Nova"
            assert mail_data["content_type"] == "text/plain"
            
            # Verify body format and ordering (alphabetical by description)
            # 1. FarewellPlugin ("Despedirse del usuario") -> starts with D
            # 2. WeatherPlugin ("Consultar el tiempo") -> starts with C. Wait, "Consultar el tiempo" starts with C, "Despedirse..." starts with D, "Información..." starts with I.
            # Alphabetical:
            # - Consultar el tiempo
            # - Despedirse del usuario
            # - Información sobre Nova
            body = mail_data["body"]
            assert "Actualmente puedo realizar 3 funciones." in body
            
            # Split lines and find the bullet points
            lines = [line.strip() for line in body.split("\n") if line.strip().startswith("•")]
            assert len(lines) == 3
            assert lines[0] == "• Consultar el tiempo"
            assert lines[1] == "• Despedirse del usuario"
            assert lines[2] == "• Información sobre Nova"


@pytest.mark.asyncio
async def test_capabilities_plugin_system_service_connection_error(plugin):
    with patch.object(plugin.client, "get_capabilities", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")

        context = PluginContext(
            raw_text="¿Qué sabes hacer?",
            normalized_text="que sabes hacer"
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Lo siento, ahora mismo no puedo consultar las funciones disponibles."


@pytest.mark.asyncio
async def test_capabilities_plugin_system_service_timeout(plugin):
    with patch.object(plugin.client, "get_capabilities", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Timeout")

        context = PluginContext(
            raw_text="¿Qué sabes hacer?",
            normalized_text="que sabes hacer"
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Lo siento, ahora mismo no puedo consultar las funciones disponibles."


@pytest.mark.asyncio
async def test_capabilities_plugin_system_service_http_error(plugin):
    with patch.object(plugin.client, "get_capabilities", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError(
            message="Internal Server Error",
            request=httpx.Request("GET", "http://system-service/capabilities"),
            response=httpx.Response(500)
        )

        context = PluginContext(
            raw_text="¿Qué sabes hacer?",
            normalized_text="que sabes hacer"
        )
        result = await plugin.execute(context)

        assert result.success is False
        assert result.speech == "Lo siento, ahora mismo no puedo consultar las funciones disponibles."


@pytest.mark.asyncio
async def test_capabilities_plugin_file_write_error(plugin, tmp_path):
    mock_caps = CapabilityList(
        capabilities=[
            Capability(id="weather", description="Consultar el tiempo")
        ]
    )

    pending_dir = tmp_path / "pending"

    with patch.object(plugin.client, "get_capabilities", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_caps

        with patch("plugins.capabilities.main.settings") as mock_settings:
            mock_settings.mail_pending_dir = str(pending_dir)

            # Mock file writing to raise OSError
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = OSError("Permission denied")

                context = PluginContext(
                    raw_text="¿Qué sabes hacer?",
                    normalized_text="que sabes hacer"
                )

                result = await plugin.execute(context)

                assert result.success is False
                assert result.speech == "Lo siento, ha ocurrido un problema al preparar el correo."
