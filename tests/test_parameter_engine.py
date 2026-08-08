import pytest
from core.models import PluginContext
from core.parameter_resolution import (
    BaseParameterResolver,
    ParameterResolverRegistry,
    ParameterResolverEngine,
    ParameterDefinition,
    ParameterResolutionResult,
    ParameterResolutionStatus,
)

class MockResolver(BaseParameterResolver):
    def __init__(self, target: str, return_value=42, return_status=ParameterResolutionStatus.RESOLVED, should_raise=False):
        self._target = target
        self.return_value = return_value
        self.return_status = return_status
        self.should_raise = should_raise

    @property
    def target_type(self) -> str:
        return self._target

    async def resolve(self, context: PluginContext, definition: ParameterDefinition) -> ParameterResolutionResult:
        if self.should_raise:
            raise RuntimeError("Resolver internal error")
        return ParameterResolutionResult(
            parameter_name=definition.name,
            value=self.return_value,
            status=self.return_status
        )

@pytest.mark.asyncio
async def test_resolve_parameters_successful():
    registry = ParameterResolverRegistry()
    registry.register(MockResolver("Integer", return_value=100))
    engine = ParameterResolverEngine(registry)

    context = PluginContext(raw_text="give me 100", normalized_text="give me 100")
    defs = [ParameterDefinition(name="max", type="Integer", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"max": 100}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.RESOLVED

@pytest.mark.asyncio
async def test_resolve_parameters_unregistered_type_with_default():
    registry = ParameterResolverRegistry()
    engine = ParameterResolverEngine(registry)

    context = PluginContext(raw_text="dime un numero", normalized_text="dime un numero")
    defs = [ParameterDefinition(name="max", type="Integer", required=False, default=100)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"max": 100}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.DEFAULT_VALUE_USED

@pytest.mark.asyncio
async def test_resolve_parameters_unregistered_type_optional_no_default():
    registry = ParameterResolverRegistry()
    engine = ParameterResolverEngine(registry)

    context = PluginContext(raw_text="hello", normalized_text="hello")
    defs = [ParameterDefinition(name="limit", type="Integer", required=False)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.UNRESOLVED_OPTIONAL

@pytest.mark.asyncio
async def test_resolve_parameters_unregistered_type_required():
    registry = ParameterResolverRegistry()
    engine = ParameterResolverEngine(registry)

    context = PluginContext(raw_text="hello", normalized_text="hello")
    defs = [ParameterDefinition(name="target", type="Location", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.TYPE_NOT_REGISTERED

@pytest.mark.asyncio
async def test_resolve_parameters_resolver_exception_with_default():
    registry = ParameterResolverRegistry()
    registry.register(MockResolver("Integer", should_raise=True))
    engine = ParameterResolverEngine(registry)

    context = PluginContext(raw_text="error test", normalized_text="error test")
    defs = [ParameterDefinition(name="max", type="Integer", required=False, default=50)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"max": 50}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.DEFAULT_VALUE_USED
    assert "Resolver internal error" in results[0].error_message
