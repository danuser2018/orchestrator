import pytest
from unittest.mock import patch, MagicMock

from core.command_catalog import CommandCatalogProjection
from core.events import HostCommandsAvailableEvent, PublicCommandEntry
from core.parameter_resolution.resolvers.command import CommandResolver
from core.parameter_resolution import (
    ParameterResolverRegistry,
    ParameterResolverEngine,
    ParameterDefinition,
    ParameterResolutionStatus,
)


@pytest.mark.asyncio
async def test_end_to_end_command_resolution_flow():
    # 1. Host Service prepares projection (strict isolation: only name, risk, phrases)
    public_entries = [
        PublicCommandEntry(
            name="calculator",
            risk="low",
            phrases=["calculadora", "maquina de calcular", "abre la calculadora"],
        ),
        PublicCommandEntry(
            name="backup",
            risk="medium",
            phrases=["copia de seguridad", "hacer backup"],
        ),
    ]
    event = HostCommandsAvailableEvent(version=1, commands=public_entries)

    # Invariant: No physical argv in event
    for entry in event.commands:
        assert not hasattr(entry, "command")
        assert not hasattr(entry, "argv")

    # 2. Orchestrator projection receives event
    projection = CommandCatalogProjection()
    projection.update_from_event(event.commands, CommandResolver.normalize_phrase)
    assert projection.is_ready is True

    # 3. Parameter resolution engine resolves user utterance
    registry = ParameterResolverRegistry()
    resolver = CommandResolver(projection)
    registry.register(resolver)
    engine = ParameterResolverEngine(registry)

    from core.models import PluginContext
    context = PluginContext(raw_text="¡Abre la calculadora!", normalized_text="abre la calculadora")
    defs = [ParameterDefinition(name="command", type="Command", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert results[0].status == ParameterResolutionStatus.RESOLVED
    assert params["command"] == "calculator"
