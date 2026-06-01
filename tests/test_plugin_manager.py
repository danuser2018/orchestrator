import pytest
from core.plugin_manager import PluginManager

def test_plugin_manager_loads_plugins():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    
    plugins = manager.get_active_plugins()
    assert len(plugins) >= 2 # Fallback and Weather
    
    weather_plugin = manager.get_plugin("WeatherPlugin")
    assert weather_plugin is not None
    assert weather_plugin.name == "WeatherPlugin"
    assert "tiempo" in weather_plugin.keywords

def test_plugin_manager_fallback_plugin():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    
    fallback = manager.get_plugin("FallbackPlugin")
    assert fallback is not None
    assert fallback.name == "FallbackPlugin"
