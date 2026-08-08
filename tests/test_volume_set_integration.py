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
async def test_planner_resolves_volume_set_digit(planner):
    request = UserRequest(text="Pon el volumen al 70")
    plan = await planner.resolve(request)

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "volume-set"
    assert step.parameters == {"volume": 70}
    assert step.context.parameters == {"volume": 70}

@pytest.mark.asyncio
async def test_planner_resolves_volume_set_spelled_out(planner):
    request = UserRequest(text="Pon el volumen a cincuenta")
    plan = await planner.resolve(request)

    assert len(plan.steps) == 1
    step = plan.steps[0]
    assert step.plugin == "volume-set"
    assert step.parameters == {"volume": 50}

@pytest.mark.asyncio
async def test_planner_resolves_volume_set_limits(planner):
    request_zero = UserRequest(text="Pon el volumen al 0")
    plan_zero = await planner.resolve(request_zero)
    assert len(plan_zero.steps) == 1
    assert plan_zero.steps[0].plugin == "volume-set"
    assert plan_zero.steps[0].parameters == {"volume": 0}

    request_max = UserRequest(text="Pon el volumen al 100")
    plan_max = await planner.resolve(request_max)
    assert len(plan_max.steps) == 1
    assert plan_max.steps[0].plugin == "volume-set"
    assert plan_max.steps[0].parameters == {"volume": 100}

@pytest.mark.asyncio
async def test_planner_does_not_interfere_with_relative_volume_commands(planner):
    request_up = UserRequest(text="Sube el volumen")
    plan_up = await planner.resolve(request_up)
    assert len(plan_up.steps) == 1
    assert plan_up.steps[0].plugin == "volume-up"

    request_down = UserRequest(text="Baja el volumen")
    plan_down = await planner.resolve(request_down)
    assert len(plan_down.steps) == 1
    assert plan_down.steps[0].plugin == "volume-down"
