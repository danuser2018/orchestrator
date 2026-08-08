import pytest
from unittest.mock import patch
from core.models import PluginContext
from core.parameter_resolution.models import ParameterDefinition
from plugins.random.main import RandomNumberPlugin

def test_random_number_plugin_parameters_property():
    plugin = RandomNumberPlugin()
    params = plugin.parameters
    assert isinstance(params, list)
    assert len(params) == 1
    param = params[0]
    assert isinstance(param, ParameterDefinition)
    assert param.name == "max"
    assert param.type == "Integer"
    assert param.required is False
    assert param.default == 100

@pytest.mark.asyncio
async def test_random_number_plugin_execute_with_custom_max():
    plugin = RandomNumberPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "random_int") as mock_rand:
        mock_rand.return_value = 42
        context = PluginContext(
            raw_text="Dime un número menor de ochenta",
            normalized_text="dime un numero menor de ochenta",
            parameters={"max": 80}
        )
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "42."
        assert result.data == {"result": 42, "max": 80}
        mock_rand.assert_called_once_with(1, 80)

@pytest.mark.asyncio
async def test_random_number_plugin_execute_default_max():
    plugin = RandomNumberPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "random_int") as mock_rand:
        mock_rand.return_value = 73
        context = PluginContext(
            raw_text="Dime un número",
            normalized_text="dime un numero",
            parameters={}
        )
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "73."
        assert result.data == {"result": 73, "max": 100}
        mock_rand.assert_called_once_with(1, 100)

@pytest.mark.asyncio
@pytest.mark.parametrize("invalid_max", [0, -10, "invalid", None])
async def test_random_number_plugin_execute_invalid_max_fallback(invalid_max):
    plugin = RandomNumberPlugin()
    plugin.initialize()
    
    with patch.object(plugin.random_service, "random_int") as mock_rand:
        mock_rand.return_value = 15
        context = PluginContext(
            raw_text="Dime un número",
            normalized_text="dime un numero",
            parameters={"max": invalid_max}
        )
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "15."
        assert result.data == {"result": 15, "max": 100}
        mock_rand.assert_called_once_with(1, 100)
