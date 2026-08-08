import pytest
from plugins.base import Plugin
from core.models import UserRequest, PluginContext, PluginResult
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine
from core.engine import ExecutionPlanner
from core.parameter_resolution import (
    BaseParameterResolver,
    ParameterResolverRegistry,
    ParameterResolverEngine,
    ParameterDefinition,
    ParameterResolutionResult,
    ParameterResolutionStatus,
)

class ParameterizedPlugin(Plugin):
    @property
    def name(self) -> str:
        return "ParameterizedPlugin"

    @property
    def description(self) -> str:
        return "Test plugin with parameters"

    @property
    def id(self) -> str:
        return "parameterized_plugin"

    @property
    def examples(self) -> list:
        return ["dime un numero aleatorio"]

    @property
    def parameters(self) -> list:
        return [
            ParameterDefinition(name="max", type="Integer", required=False, default=100)
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="ok")

class CustomIntegerResolver(BaseParameterResolver):
    @property
    def target_type(self) -> str:
        return "Integer"

    async def resolve(self, context: PluginContext, definition: ParameterDefinition) -> ParameterResolutionResult:
        if "50" in context.raw_text:
            return ParameterResolutionResult(
                parameter_name=definition.name,
                value=50,
                status=ParameterResolutionStatus.RESOLVED
            )
        return ParameterResolutionResult(
            parameter_name=definition.name,
            value=None,
            status=ParameterResolutionStatus.UNRESOLVED_OPTIONAL
        )

@pytest.mark.asyncio
async def test_execution_planner_resolves_plugin_parameters():
    plugin_manager = PluginManager()
    plugin = ParameterizedPlugin()
    plugin_manager.plugins[plugin.id] = plugin
    plugin_manager.plugins[plugin.name] = plugin

    registry = ParameterResolverRegistry()
    registry.register(CustomIntegerResolver())
    param_engine = ParameterResolverEngine(registry)

    planner = ExecutionPlanner(
        plugin_manager=plugin_manager,
        similarity_engine=RapidFuzzSimilarityEngine(),
        parameter_engine=param_engine
    )

    # Test with text containing 50
    request = UserRequest(text="dime un numero aleatorio hasta 50")
    plan = await planner.resolve(request)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "parameterized_plugin"
    assert plan.steps[0].parameters == {"max": 50}

    # Test with text without number (should fallback to default=100)
    request2 = UserRequest(text="dime un numero aleatorio")
    plan2 = await planner.resolve(request2)
    assert len(plan2.steps) == 1
    assert plan2.steps[0].plugin == "parameterized_plugin"
    assert plan2.steps[0].parameters == {"max": 100}
