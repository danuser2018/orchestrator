import pytest
from core.engine import IntentResolver
from core.models import UserRequest, ExecutionPlan, ExecutionPlanStep, PluginContext, PluginResult
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine
from plugins.base import Plugin

@pytest.fixture
def resolver():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    return IntentResolver(plugin_manager=manager, similarity_engine=similarity_engine)

def test_normalize_text(resolver):
    assert resolver.normalize_text("¿Qué tiempo hace hoy, eh?") == "que tiempo hace hoy eh"
    assert resolver.normalize_text("¡Hola mundo!") == "hola mundo"
    assert resolver.normalize_text("MAYÚSCULAS") == "mayusculas"

@pytest.mark.asyncio
async def test_resolve_successful_match(resolver):
    req = UserRequest(text="Hola Nova qué tal te va hoy")
    plan = await resolver.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "GreetingPlugin"
    assert step.context.normalized_text == "hola nova que tal te va hoy"

@pytest.mark.asyncio
async def test_resolve_empty_input_fallback(resolver):
    req = UserRequest(text="   ")
    plan = await resolver.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "FallbackPlugin"
    assert step.confidence == 0.0

@pytest.mark.asyncio
async def test_resolve_below_threshold_fallback(resolver):
    req = UserRequest(text="dibuja un dinosaurio azul")
    plan = await resolver.resolve(req)
    
    assert isinstance(plan, ExecutionPlan)
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "FallbackPlugin"

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
async def test_resolve_tie_breaker_by_priority(resolver):
    mock_a = MockPluginA()
    mock_b = MockPluginB()
    resolver.plugin_manager.plugins["MockPluginA"] = mock_a
    resolver.plugin_manager.plugins["MockPluginB"] = mock_b
    
    req = UserRequest(text="activar sistema de alarma")
    plan = await resolver.resolve(req)
    
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "MockPluginA"
