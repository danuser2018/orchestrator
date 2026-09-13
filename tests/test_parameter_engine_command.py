import pytest
from core.models import PluginContext
from core.command_catalog import CommandCatalogProjection
from core.events import PublicCommandEntry
from core.parameter_resolution import (
    ParameterResolverRegistry,
    ParameterResolverEngine,
    ParameterDefinition,
    ParameterResolutionStatus,
)
from core.parameter_resolution.resolvers.command import CommandResolver


@pytest.fixture
def engine():
    catalog = CommandCatalogProjection()
    entries = [
        PublicCommandEntry(name="calculator", risk="low", phrases=["calculadora", "abre la calculadora"]),
        PublicCommandEntry(name="backup", risk="medium", phrases=["copia de seguridad", "hacer backup"]),
    ]
    catalog.update_from_event(entries, CommandResolver.normalize_phrase)

    registry = ParameterResolverRegistry()
    resolver = CommandResolver(catalog)
    registry.register(resolver)

    return ParameterResolverEngine(registry)


@pytest.mark.asyncio
async def test_resolve_command_parameter_exact(engine):
    context = PluginContext(raw_text="Abre la calculadora", normalized_text="abre la calculadora")
    defs = [ParameterDefinition(name="command", type="Command", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"command": "calculator"}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.RESOLVED
    assert results[0].value == "calculator"


@pytest.mark.asyncio
async def test_resolve_command_parameter_fuzzy(engine):
    context = PluginContext(raw_text="calculadorra", normalized_text="calculadorra")
    defs = [ParameterDefinition(name="command", type="Command", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"command": "calculator"}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.RESOLVED


@pytest.mark.asyncio
async def test_resolve_command_parameter_unresolved_required(engine):
    context = PluginContext(raw_text="algo desconocido", normalized_text="algo desconocido")
    defs = [ParameterDefinition(name="command", type="Command", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert results[0].value is None


@pytest.mark.asyncio
async def test_resolve_command_parameter_unresolved_optional_with_default(engine):
    context = PluginContext(raw_text="algo desconocido", normalized_text="algo desconocido")
    defs = [ParameterDefinition(name="command", type="Command", required=False, default="calculator")]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {"command": "calculator"}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.DEFAULT_VALUE_USED
