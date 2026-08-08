import pytest
from core.engine import ExecutionPlanner
from core.models import UserRequest
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine
from core.parameter_resolution import ParameterResolverRegistry, ParameterResolverEngine
from core.parameter_resolution.resolvers.integer import IntegerResolver

@pytest.fixture
def planner():
    plugin_manager = PluginManager()
    plugin_manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    
    registry = ParameterResolverRegistry()
    registry.register(IntegerResolver())
    engine = ParameterResolverEngine(registry)
    
    return ExecutionPlanner(
        plugin_manager=plugin_manager,
        similarity_engine=similarity_engine,
        parameter_engine=engine
    )

@pytest.mark.asyncio
async def test_planner_resolves_integer_parameter(planner):
    request = UserRequest(text="Dime un número menor de ochenta")
    plan = await planner.resolve(request)
    
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "random-number"
    assert step.parameters == {"max": 80}
    assert step.context.parameters == {"max": 80}

@pytest.mark.asyncio
async def test_planner_uses_default_when_no_integer_present(planner):
    request = UserRequest(text="Dime un número")
    plan = await planner.resolve(request)
    
    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "random-number"
    assert step.parameters == {"max": 100}
    assert step.context.parameters == {"max": 100}
