import pytest
from core.engine import Router
from core.models import UserRequest
from core.plugin_manager import PluginManager

@pytest.fixture
def router():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    return Router(plugin_manager=manager)

def test_normalize_text(router):
    assert router.normalize_text("¿Qué tiempo hace hoy, eh?") == "que tiempo hace hoy eh"
    assert router.normalize_text("¡Hola mundo!") == "hola mundo"
    assert router.normalize_text("MAYÚSCULAS") == "mayusculas"

@pytest.mark.asyncio
async def test_route_weather_request(router):
    req = UserRequest(text="¿Qué tiempo hace hoy en Madrid?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "WeatherPlugin"
    assert context.normalized_text == "que tiempo hace hoy en madrid"

@pytest.mark.asyncio
async def test_route_weather_request_by_regex(router):
    req = UserRequest(text="dime si va a llover mañana")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "WeatherPlugin"

@pytest.mark.asyncio
async def test_route_fallback_request(router):
    req = UserRequest(text="Abre el navegador por favor")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "FallbackPlugin"


from plugins.base import Plugin
from core.models import PluginContext, PluginResult

class MockExclusivePlugin(Plugin):
    @property
    def name(self) -> str:
        return "MockExclusivePlugin"
    
    @property
    def description(self) -> str:
        return "Mock exclusive plugin"
        
    @property
    def id(self) -> str:
        return "mock_exclusive"
        
    @property
    def exclusive_regex(self) -> str | None:
        return r"secreto.*revelado"
        
    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="Secreto")

@pytest.mark.asyncio
async def test_route_exclusive_regex(router):
    mock_plugin = MockExclusivePlugin()
    router.plugin_manager.plugins["MockExclusivePlugin"] = mock_plugin
    
    # Text that matches exclusive regex
    req = UserRequest(text="este es un secreto muy bien guardado y hoy es revelado")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "MockExclusivePlugin"

