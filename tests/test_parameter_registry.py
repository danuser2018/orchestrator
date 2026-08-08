import pytest
from core.parameter_resolution.base import BaseParameterResolver
from core.parameter_resolution.registry import ParameterResolverRegistry
from core.parameter_resolution.models import ParameterDefinition, ParameterResolutionResult, ParameterResolutionStatus
from core.models import PluginContext

class DummyIntegerResolver(BaseParameterResolver):
    @property
    def target_type(self) -> str:
        return "Integer"

    async def resolve(self, context: PluginContext, definition: ParameterDefinition) -> ParameterResolutionResult:
        return ParameterResolutionResult(
            parameter_name=definition.name,
            value=42,
            status=ParameterResolutionStatus.RESOLVED
        )

def test_registry_register_and_get():
    registry = ParameterResolverRegistry()
    resolver = DummyIntegerResolver()
    
    registry.register(resolver)
    
    # Check exact case match
    assert registry.get("Integer") is resolver
    # Check case insensitive match
    assert registry.get("integer") is resolver
    assert registry.get("INTEGER") is resolver

def test_registry_unregistered_type():
    registry = ParameterResolverRegistry()
    assert registry.get("Date") is None

def test_registry_unregister():
    registry = ParameterResolverRegistry()
    resolver = DummyIntegerResolver()
    
    registry.register(resolver)
    assert registry.get("Integer") is resolver
    
    registry.unregister("integer")
    assert registry.get("Integer") is None
