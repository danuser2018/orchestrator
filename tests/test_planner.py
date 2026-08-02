import pytest
from core.engine import ExecutionPlanner
from core.models import UserRequest, ExecutionPlan, ExecutionPlanStep, PluginContext, PluginResult
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine
from unittest.mock import MagicMock
from plugins.base import Plugin

@pytest.fixture
def planner():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    return ExecutionPlanner(plugin_manager=manager, similarity_engine=similarity_engine)

def test_normalize_text(planner):
    assert planner.normalize_text("¿Qué tiempo hace hoy, eh?") == "que tiempo hace hoy eh"
    assert planner.normalize_text("¡Hola mundo!") == "hola mundo"
    assert planner.normalize_text("MAYÚSCULAS") == "mayusculas"

@pytest.mark.asyncio
async def test_resolve_successful_match(planner):
    req = UserRequest(text="Hola Nova qué tal te va hoy")
    plan = await planner.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin in ("greeting", "GreetingPlugin")
    assert step.context.normalized_text == "hola nova que tal te va hoy"

@pytest.mark.asyncio
async def test_resolve_empty_input_fallback(planner):
    req = UserRequest(text="   ")
    plan = await planner.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin in ("fallback", "FallbackPlugin")
    assert step.confidence == 0.0

@pytest.mark.asyncio
async def test_resolve_below_threshold_fallback(planner):
    req = UserRequest(text="dibuja un dinosaurio azul")
    plan = await planner.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin in ("fallback", "FallbackPlugin")

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
async def test_resolve_tie_breaker_by_priority(planner):
    mock_a = MockPluginA()
    mock_b = MockPluginB()
    planner.plugin_manager.plugins["MockPluginA"] = mock_a
    planner.plugin_manager.plugins["MockPluginB"] = mock_b
    planner.plugin_manager.plugins["mock_a"] = mock_a
    planner.plugin_manager.plugins["mock_b"] = mock_b
    
    req = UserRequest(text="activar sistema de alarma")
    plan = await planner.resolve(req)
    
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin in ("mock_a", "MockPluginA")

class MockPluginAEqualPriority(MockPluginA):
    @property
    def priority(self) -> int:
        return 80

class MockPluginBEqualPriority(MockPluginB):
    @property
    def priority(self) -> int:
        return 80

@pytest.mark.asyncio
async def test_resolve_persistent_tie_fallback(planner):
    mock_a = MockPluginAEqualPriority()
    mock_b = MockPluginBEqualPriority()
    planner.plugin_manager.plugins["MockPluginA"] = mock_a
    planner.plugin_manager.plugins["MockPluginB"] = mock_b
    planner.plugin_manager.plugins["mock_a"] = mock_a
    planner.plugin_manager.plugins["mock_b"] = mock_b
    
    req = UserRequest(text="activar sistema de alarma")
    plan = await planner.resolve(req)
    
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin in ("fallback", "FallbackPlugin")

@pytest.mark.asyncio
async def test_resolve_normalization_coherence(planner):
    req = UserRequest(text="¿Hóla Nôvá qué tàl?")
    plan = await planner.resolve(req)
    
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin in ("greeting", "GreetingPlugin")


@pytest.mark.asyncio
async def test_resolve_diagnostic_logging(planner):
    from core.engine import logger as engine_logger
    
    original_debug = engine_logger.debug
    original_info = engine_logger.info
    
    engine_logger.debug = MagicMock()
    engine_logger.info = MagicMock()
    
    try:
        req = UserRequest(text="pon musica")
        await planner.resolve(req)
        
        assert engine_logger.debug.call_count >= 2
        assert engine_logger.info.call_count >= 1
    finally:
        engine_logger.debug = original_debug
        engine_logger.info = original_info

