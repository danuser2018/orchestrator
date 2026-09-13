import asyncio
import pytest
from core.models import PluginContext
from core.events import HostCommandsAvailableEvent, PublicCommandEntry
from core.command_catalog import CommandCatalogProjection
from core.parameter_resolution import (
    ParameterResolverRegistry,
    ParameterResolverEngine,
    ParameterDefinition,
    ParameterResolutionStatus,
)
from core.parameter_resolution.resolvers.command import CommandResolver


@pytest.mark.asyncio
async def test_cold_start_and_eventual_convergence_flow():
    # 1. Cold start / Transitory outage: Catalog is empty
    catalog = CommandCatalogProjection()
    assert not catalog.is_ready

    registry = ParameterResolverRegistry()
    resolver = CommandResolver(catalog)
    registry.register(resolver)
    engine = ParameterResolverEngine(registry)

    # 2. Query arrives while catalog is not ready -> Fail-Closed verified
    context = PluginContext(raw_text="Abre la calculadora", normalized_text="abre la calculadora")
    defs = [ParameterDefinition(name="command", type="Command", required=True)]

    params, results = await engine.resolve_parameters(context, defs)
    assert params == {}
    assert len(results) == 1
    assert results[0].status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert results[0].value is None

    # 3. Simulate periodic NATS publication arrival (e.g. tick at interval 0.05s)
    await asyncio.sleep(0.05)
    incoming_event = HostCommandsAvailableEvent(
        version=1,
        commands=[
            PublicCommandEntry(
                name="calculator",
                risk="low",
                phrases=["calculadora", "abre la calculadora"],
            ),
            PublicCommandEntry(
                name="backup",
                risk="medium",
                phrases=["copia de seguridad", "hacer backup"],
            ),
        ],
    )

    # NATS subscriber callback executes
    catalog.update_from_event(incoming_event.commands, CommandResolver.normalize_phrase)
    assert catalog.is_ready is True

    # 4. Same query arrives after convergence (< 200 ms) -> Resolution succeeds
    params_after, results_after = await engine.resolve_parameters(context, defs)
    assert params_after == {"command": "calculator"}
    assert len(results_after) == 1
    assert results_after[0].status == ParameterResolutionStatus.RESOLVED
    assert results_after[0].value == "calculator"
