import pytest
from core.models import PluginContext
from core.command_catalog import CommandCatalogProjection
from core.events import PublicCommandEntry
from core.parameter_resolution.models import ParameterDefinition, ParameterResolutionStatus
from core.parameter_resolution.resolvers.command import CommandResolver


@pytest.fixture
def catalog():
    cat = CommandCatalogProjection()
    entries = [
        PublicCommandEntry(
            name="calculator",
            risk="low",
            phrases=["calculadora", "maquina de calcular", "abre la calculadora"],
        ),
        PublicCommandEntry(
            name="backup",
            risk="medium",
            phrases=["copia de seguridad", "hacer backup", "respaldar datos"],
        ),
        PublicCommandEntry(
            name="format-disk",
            risk="high",
            phrases=["formatear disco externo", "formatear unidad usb"],
        ),
    ]
    cat.update_from_event(entries, CommandResolver.normalize_phrase)
    return cat


@pytest.mark.asyncio
async def test_target_type(catalog):
    resolver = CommandResolver(catalog)
    assert resolver.target_type == "Command"


@pytest.mark.asyncio
async def test_resolve_not_ready_fail_closed():
    empty_catalog = CommandCatalogProjection()
    resolver = CommandResolver(empty_catalog)
    context = PluginContext(raw_text="calculadora", normalized_text="calculadora")
    definition_req = ParameterDefinition(name="command", type="Command", required=True)
    res_req = await resolver.resolve(context, definition_req)
    assert res_req.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res_req.value is None

    definition_opt = ParameterDefinition(name="command", type="Command", required=False)
    res_opt = await resolver.resolve(context, definition_opt)
    assert res_opt.status == ParameterResolutionStatus.UNRESOLVED_OPTIONAL
    assert res_opt.value is None


@pytest.mark.asyncio
async def test_resolve_empty_text(catalog):
    resolver = CommandResolver(catalog)
    context = PluginContext(raw_text="   ", normalized_text="")
    definition = ParameterDefinition(name="command", type="Command", required=True)
    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res.value is None


@pytest.mark.asyncio
async def test_exact_match_precedence(catalog):
    # Scenario 6: Exact match
    resolver = CommandResolver(catalog)
    context = PluginContext(raw_text="Abre la calculadora", normalized_text="abre la calculadora")
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.RESOLVED
    assert res.value == "calculator"


@pytest.mark.asyncio
async def test_fuzzy_match_low_risk_stt_typo(catalog):
    # Scenario 7: Minor STT error "calculadorra" matches low risk (threshold 60.0)
    resolver = CommandResolver(catalog)
    context = PluginContext(raw_text="calculadorra", normalized_text="calculadorra")
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.RESOLVED
    assert res.value == "calculator"


@pytest.mark.asyncio
async def test_fuzzy_match_high_risk_rejection(catalog):
    # Scenario 8: High risk command requires score >= 70.0
    # "formatear particion" scores ~66.7% against "formatear disco externo",
    # which exceeds low threshold (60.0) but is rejected by high threshold (70.0)
    resolver = CommandResolver(catalog)
    context = PluginContext(
        raw_text="formatear particion",
        normalized_text="formatear particion",
    )
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res.value is None


@pytest.mark.asyncio
async def test_ambiguity_rejection():
    # Scenario 9: Two distinct commands with score delta <= 5.0
    cat = CommandCatalogProjection()
    entries = [
        PublicCommandEntry(name="calc-one", risk="low", phrases=["calculadora"]),
        PublicCommandEntry(name="calc-two", risk="low", phrases=["calculador"]),
    ]
    cat.update_from_event(entries, CommandResolver.normalize_phrase)
    resolver = CommandResolver(cat, ambiguity_delta=5.0)

    # Input is "calculado" which is very close to both
    context = PluginContext(raw_text="calculado", normalized_text="calculado")
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res.value is None
    assert "Ambiguous match" in res.error_message


@pytest.mark.asyncio
async def test_semantic_inference_exclusion(catalog):
    # Scenario 12: Semantically equivalent but lexically different phrase is rejected
    resolver = CommandResolver(catalog)
    context = PluginContext(
        raw_text="hazme una cuenta matematica",
        normalized_text="hazme una cuenta matematica",
    )
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res.value is None


@pytest.mark.asyncio
async def test_custom_thresholds(catalog):
    # Custom stricter threshold (98.0) rejects STT typo scoring ~95.6%
    resolver = CommandResolver(catalog, thresholds={"low": 98.0, "medium": 98.0, "high": 98.0})
    context = PluginContext(raw_text="calculadorra", normalized_text="calculadorra")
    definition = ParameterDefinition(name="command", type="Command", required=True)

    res = await resolver.resolve(context, definition)
    assert res.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert res.value is None
