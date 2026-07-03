import pytest
import logging
from unittest.mock import MagicMock
from core.engine import Router
from core.models import UserRequest, PluginResult, PluginContext
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine
from plugins.base import Plugin

@pytest.fixture
def router():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    return Router(plugin_manager=manager, similarity_engine=similarity_engine)

def test_normalize_text(router):
    assert router.normalize_text("¿Qué tiempo hace hoy, eh?") == "que tiempo hace hoy eh"
    assert router.normalize_text("¡Hola mundo!") == "hola mundo"
    assert router.normalize_text("MAYÚSCULAS") == "mayusculas"

@pytest.mark.asyncio
async def test_route_request_successful_match(router):
    req = UserRequest(text="Hola Nova qué tal te va hoy")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "GreetingPlugin"
    assert context.normalized_text == "hola nova que tal te va hoy"

@pytest.mark.asyncio
async def test_route_request_below_threshold_fallback(router):
    req = UserRequest(text="dibuja un dinosaurio azul")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "FallbackPlugin"

class MockPluginA(Plugin):
    @property
    def name(self) -> str:
        return "MockPluginA"
    @property
    def description(self) -> str:
        return "Mock A"
    @property
    def id(self) -> str:
        return "mock_a"
    @property
    def priority(self) -> int:
        return 80
    @property
    def examples(self) -> list:
        return ["activar sistema de alarma"]
    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="A")

class MockPluginB(Plugin):
    @property
    def name(self) -> str:
        return "MockPluginB"
    @property
    def description(self) -> str:
        return "Mock B"
    @property
    def id(self) -> str:
        return "mock_b"
    @property
    def priority(self) -> int:
        return 60
    @property
    def examples(self) -> list:
        return ["activar sistema de alarmas"]
    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="B")

@pytest.mark.asyncio
async def test_route_request_tie_breaker_by_priority(router):
    mock_a = MockPluginA()
    mock_b = MockPluginB()
    router.plugin_manager.plugins["MockPluginA"] = mock_a
    router.plugin_manager.plugins["MockPluginB"] = mock_b
    
    # Text is highly similar to both
    req = UserRequest(text="activar sistema de alarma")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "MockPluginA"

class MockPluginAEqualPriority(MockPluginA):
    @property
    def priority(self) -> int:
        return 80

class MockPluginBEqualPriority(MockPluginB):
    @property
    def priority(self) -> int:
        return 80

@pytest.mark.asyncio
async def test_route_request_persistent_tie_fallback(router):
    mock_a = MockPluginAEqualPriority()
    mock_b = MockPluginBEqualPriority()
    router.plugin_manager.plugins["MockPluginA"] = mock_a
    router.plugin_manager.plugins["MockPluginB"] = mock_b
    
    req = UserRequest(text="activar sistema de alarma")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "FallbackPlugin"

@pytest.mark.asyncio
async def test_route_request_empty_input_fallback(router):
    req = UserRequest(text="   ")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "FallbackPlugin"

@pytest.mark.asyncio
async def test_route_request_normalization_coherence(router):
    req = UserRequest(text="¿Hóla Nôvá qué tàl?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "GreetingPlugin"

@pytest.mark.asyncio
async def test_route_request_diagnostic_logging(router):
    # Mock logger to verify it receives diagnostic calls
    from core.engine import logger as engine_logger
    
    original_debug = engine_logger.debug
    original_info = engine_logger.info
    
    engine_logger.debug = MagicMock()
    engine_logger.info = MagicMock()
    
    try:
        req = UserRequest(text="pon musica")
        await router.route_request(req)
        
        # Verify logger.debug calls
        assert engine_logger.debug.call_count >= 2
        # Verify logger.info call
        assert engine_logger.info.call_count >= 1
    finally:
        engine_logger.debug = original_debug
        engine_logger.info = original_info


