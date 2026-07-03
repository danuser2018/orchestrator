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
    assert weather_plugin.id == "weather"
    assert weather_plugin.priority == 80
    assert len(weather_plugin.examples) == 10

def test_plugin_manager_fallback_plugin():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    
    fallback = manager.get_plugin("FallbackPlugin")
    assert fallback is not None
    assert fallback.name == "FallbackPlugin"
    assert fallback.id == "fallback"
    assert fallback.priority == 0
    assert fallback.examples == []

def test_plugin_manager_duplicate_id():
    import types
    from plugins.base import Plugin
    
    manager = PluginManager(plugins_dir="plugins")
    mock_module = types.ModuleType("mock_module")
    
    class PluginA(Plugin):
        @property
        def name(self): return "PluginA"
        @property
        def description(self): return "Desc A"
        @property
        def id(self): return "duplicate_id"
        async def execute(self, context): pass

    class PluginB(Plugin):
        @property
        def name(self): return "PluginB"
        @property
        def description(self): return "Desc B"
        @property
        def id(self): return "duplicate_id"
        async def execute(self, context): pass

    mock_module.PluginA = PluginA
    mock_module.PluginB = PluginB
    
    with pytest.raises(ValueError) as excinfo:
        manager._register_plugins_from_module(mock_module)
    assert "Duplicate plugin ID" in str(excinfo.value)

def test_plugin_manager_invalid_priority():
    import types
    from plugins.base import Plugin
    
    manager = PluginManager(plugins_dir="plugins")
    mock_module = types.ModuleType("mock_module")
    
    class InvalidPriorityPlugin(Plugin):
        @property
        def name(self): return "InvalidPriorityPlugin"
        @property
        def description(self): return "Desc Invalid"
        @property
        def id(self): return "invalid_prio"
        @property
        def priority(self): return 120
        async def execute(self, context): pass
        
    mock_module.InvalidPriorityPlugin = InvalidPriorityPlugin
    
    with pytest.raises(ValueError) as excinfo:
        manager._register_plugins_from_module(mock_module)
    assert "Plugin priority must be between 0 and 100" in str(excinfo.value)

def test_plugin_examples_filtering():
    from plugins.base import Plugin
    
    class ExampleFilterPlugin(Plugin):
        @property
        def name(self): return "ExampleFilterPlugin"
        @property
        def description(self): return "Filter"
        @property
        def id(self): return "filter"
        @property
        def examples(self):
            return ["Valid phrase", "", "   ", "Another valid phrase"]
        async def execute(self, context): pass
        
    plugin_instance = ExampleFilterPlugin()
    assert plugin_instance.examples == ["Valid phrase", "Another valid phrase"]

def test_plugin_legacy_properties_removed():
    from plugins.weather.main import WeatherPlugin
    plugin = WeatherPlugin()
    
    with pytest.raises(AttributeError):
        _ = plugin.keywords
        
    with pytest.raises(AttributeError):
        _ = plugin.regex_patterns
        
    with pytest.raises(AttributeError):
        _ = plugin.exclusive_regex
