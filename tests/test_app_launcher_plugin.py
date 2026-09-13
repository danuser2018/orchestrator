import ast
from pathlib import Path
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import pytest

from core.host_service_client import HostServiceClient, ExecuteCommandResponse
from core.models import PluginContext, PluginResult
from core.parameter_resolution.models import ParameterDefinition
from plugins.app_launcher.main import AppLauncherPlugin


def test_app_launcher_plugin_metadata():
    plugin = AppLauncherPlugin()
    assert plugin.name == "AppLauncherPlugin"
    assert plugin.id == "open_app"
    assert plugin.priority == 60
    assert bool(plugin.description)
    assert len(plugin.parameters) == 1
    param = plugin.parameters[0]
    assert isinstance(param, ParameterDefinition)
    assert param.name == "command"
    assert param.type == "Command"
    assert param.required is True
    assert plugin.risk_policy == {
        "policy": "lookup",
        "source": "command",
        "table": "host_commands",
    }


def test_app_launcher_plugin_cold_start_and_dynamic_examples():
    plugin = AppLauncherPlugin()
    assert plugin.examples == plugin.DEFAULT_COLD_START_EXAMPLES

    # Load dynamic phrases
    plugin.load_dynamic_phrases(["calculadora", "abre la calculadora"])
    assert "calculadora" in plugin.examples
    assert "abre la calculadora" in plugin.examples
    for cold_example in plugin.DEFAULT_COLD_START_EXAMPLES:
        assert cold_example in plugin.examples

    # Test deduplication, empty string filtering, and whitespace stripping
    initial_count = len(plugin.DEFAULT_COLD_START_EXAMPLES)
    plugin.load_dynamic_phrases([
        "  calculadora  ",
        "",
        "   ",
        "calculadora",
        "abre la calculadora",
        "nueva app",
    ])
    assert "nueva app" in plugin.examples
    assert "calculadora" in plugin.examples
    assert "abre la calculadora" in plugin.examples
    assert plugin.examples.count("calculadora") == 1
    # initial cold start (10) + "calculadora" + "abre la calculadora" + "nueva app" = 13
    assert len(plugin.examples) == initial_count + 3


@pytest.mark.asyncio
async def test_host_service_client_execute_command_success():
    client = HostServiceClient(base_url="http://test-host:8007")
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "command": "calculator",
        "status": "started",
        "pid": 4321,
    }

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_response
        res = await client.execute_command("calculator")
        mock_post.assert_called_once_with(
            "http://test-host:8007/v1/commands/execute",
            json={"command": "calculator"},
        )
        assert isinstance(res, ExecuteCommandResponse)
        assert res.command == "calculator"
        assert res.status == "started"
        assert res.pid == 4321


@pytest.mark.asyncio
async def test_host_service_client_execute_command_http_status_error():
    client = HostServiceClient(base_url="http://test-host:8007")
    mock_req = httpx.Request("POST", "http://test-host:8007/v1/commands/execute")
    mock_resp_404 = httpx.Response(404, request=mock_req)
    mock_resp_500 = httpx.Response(500, request=mock_req)

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp_404
        with pytest.raises(httpx.HTTPStatusError):
            await client.execute_command("unknown-cmd")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.return_value = mock_resp_500
        with pytest.raises(httpx.HTTPStatusError):
            await client.execute_command("broken-cmd")


@pytest.mark.asyncio
async def test_host_service_client_execute_command_connection_and_timeout():
    client = HostServiceClient(base_url="http://test-host:8007")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.ConnectError("Connection refused")
        with pytest.raises(httpx.ConnectError):
            await client.execute_command("calculator")

    with patch("httpx.AsyncClient.post", new_callable=AsyncMock) as mock_post:
        mock_post.side_effect = httpx.TimeoutException("Request timed out")
        with pytest.raises(httpx.TimeoutException):
            await client.execute_command("calculator")


@pytest.mark.asyncio
async def test_app_launcher_plugin_execute_success():
    plugin = AppLauncherPlugin()
    plugin.initialize()

    mock_client = AsyncMock(spec=HostServiceClient)
    mock_client.execute_command.return_value = ExecuteCommandResponse(
        command="calculator",
        status="started",
        pid=12345,
    )
    plugin.client = mock_client

    context = PluginContext(
        raw_text="abre la calculadora",
        normalized_text="abre la calculadora",
        parameters={"command": "calculator"},
    )
    result = await plugin.execute(context)

    assert isinstance(result, PluginResult)
    assert result.success is True
    assert result.speech == "Aplicación abierta."
    assert result.data == {"command": "calculator", "status": "started", "pid": 12345}
    mock_client.execute_command.assert_called_once_with("calculator")


@pytest.mark.asyncio
async def test_app_launcher_plugin_execute_missing_or_invalid_command():
    plugin = AppLauncherPlugin()
    plugin.initialize()
    mock_client = AsyncMock(spec=HostServiceClient)
    plugin.client = mock_client

    # Empty parameters dict
    context_none = PluginContext(raw_text="abre algo", normalized_text="abre algo", parameters={})
    result_none = await plugin.execute(context_none)
    assert result_none.success is False
    assert result_none.speech == "No he podido abrir la aplicación."

    # None value for command parameter
    context_none_val = PluginContext(raw_text="abre algo", normalized_text="abre algo", parameters={"command": None})
    result_none_val = await plugin.execute(context_none_val)
    assert result_none_val.success is False
    assert result_none_val.speech == "No he podido abrir la aplicación."

    # Empty string parameter
    context_empty = PluginContext(raw_text="abre algo", normalized_text="abre algo", parameters={"command": "   "})
    result_empty = await plugin.execute(context_empty)
    assert result_empty.success is False
    assert result_empty.speech == "No he podido abrir la aplicación."

    # Missing command key
    context_missing = PluginContext(raw_text="abre algo", normalized_text="abre algo", parameters={"other": 123})
    result_missing = await plugin.execute(context_missing)
    assert result_missing.success is False
    assert result_missing.speech == "No he podido abrir la aplicación."

    mock_client.execute_command.assert_not_called()


@pytest.mark.asyncio
async def test_app_launcher_plugin_execute_connection_error_and_timeout():
    plugin = AppLauncherPlugin()
    plugin.initialize()
    mock_client = AsyncMock(spec=HostServiceClient)
    plugin.client = mock_client

    # ConnectError
    mock_client.execute_command.side_effect = httpx.ConnectError("Connection refused")
    context = PluginContext(raw_text="abre la calculadora", normalized_text="abre la calculadora", parameters={"command": "calculator"})
    result_conn = await plugin.execute(context)
    assert result_conn.success is False
    assert result_conn.speech == "Servicio no disponible."

    # TimeoutException
    mock_client.execute_command.side_effect = httpx.TimeoutException("Timeout")
    result_timeout = await plugin.execute(context)
    assert result_timeout.success is False
    assert result_timeout.speech == "Servicio no disponible."


@pytest.mark.asyncio
async def test_app_launcher_plugin_execute_http_status_error():
    plugin = AppLauncherPlugin()
    plugin.initialize()
    mock_client = AsyncMock(spec=HostServiceClient)
    plugin.client = mock_client

    mock_req = httpx.Request("POST", "http://test-host:8007/v1/commands/execute")
    mock_resp_404 = httpx.Response(404, request=mock_req)
    mock_client.execute_command.side_effect = httpx.HTTPStatusError(
        "Not Found", request=mock_req, response=mock_resp_404
    )

    context = PluginContext(raw_text="abre unknown", normalized_text="abre unknown", parameters={"command": "unknown"})
    result = await plugin.execute(context)
    assert result.success is False
    assert result.speech == "No he podido abrir la aplicación."


@pytest.mark.asyncio
async def test_app_launcher_plugin_execute_unexpected_exception():
    plugin = AppLauncherPlugin()
    plugin.initialize()
    mock_client = AsyncMock(spec=HostServiceClient)
    plugin.client = mock_client

    mock_client.execute_command.side_effect = RuntimeError("Something unexpected")
    context = PluginContext(raw_text="abre calc", normalized_text="abre calc", parameters={"command": "calc"})
    result = await plugin.execute(context)
    assert result.success is False
    assert result.speech == "No he podido abrir la aplicación."


def test_app_launcher_zero_shell_audit():
    """Ensure AppLauncherPlugin does not import subprocess, os.system, or shutil (RNF-01)."""
    target_file = Path(__file__).parent.parent / "plugins" / "app_launcher" / "main.py"
    with open(target_file, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(target_file))

    forbidden_modules = {"subprocess", "shutil"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name not in forbidden_modules, f"Forbidden import: {alias.name}"
        elif isinstance(node, ast.ImportFrom):
            assert node.module not in forbidden_modules, f"Forbidden from-import: {node.module}"
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id == "os" and node.attr == "system":
                pytest.fail("Forbidden usage of os.system")
