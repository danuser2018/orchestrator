import pytest
from core.models import PluginContext
from core.parameter_resolution.models import ParameterDefinition, ParameterResolutionStatus
from core.parameter_resolution.resolvers.integer import IntegerResolver

@pytest.fixture
def integer_resolver():
    return IntegerResolver()

@pytest.fixture
def definition():
    return ParameterDefinition(name="max", type="Integer", required=False, default=100)

@pytest.mark.asyncio
async def test_target_type(integer_resolver):
    assert integer_resolver.target_type == "Integer"

@pytest.mark.asyncio
@pytest.mark.parametrize("input_text,expected_val", [
    ("5", 5),
    ("25", 25),
    ("Dime un número menor de 50", 50),
    ("Límite en 100", 100),
    ("1500 opciones", 1500),
])
async def test_resolve_digits(integer_resolver, definition, input_text, expected_val):
    context = PluginContext(raw_text=input_text, normalized_text=input_text.lower())
    result = await integer_resolver.resolve(context, definition)
    assert result.status == ParameterResolutionStatus.RESOLVED
    assert result.value == expected_val
    assert isinstance(result.value, int)

@pytest.mark.asyncio
@pytest.mark.parametrize("input_text,expected_val", [
    ("Dime uno", 1),
    ("Dame cinco opciones", 5),
    ("Genera diez resultados", 10),
    ("Límite en veinte", 20),
    ("Genera un número hasta veinticinco", 25),
    ("Hasta cincuenta", 50),
    ("Dime un número menor de ochenta", 80),
    ("Dame un valor menor de cien", 100),
    ("Máximo ciento veinte", 120),
    ("Dame un número menor de mil", 1000),
    ("Valor hasta treinta y cinco", 35),
])
async def test_resolve_spanish_cardinals(integer_resolver, definition, input_text, expected_val):
    # Simulating normalized text lowercased without accents as produced by ExecutionPlanner
    from unicodedata import normalize, category
    normalized = ''.join(c for c in normalize('NFD', input_text.lower()) if category(c) != 'Mn')
    context = PluginContext(raw_text=input_text, normalized_text=normalized)
    result = await integer_resolver.resolve(context, definition)
    assert result.status == ParameterResolutionStatus.RESOLVED
    assert result.value == expected_val
    assert isinstance(result.value, int)

@pytest.mark.asyncio
async def test_resolve_no_number(integer_resolver, definition):
    context = PluginContext(raw_text="Dime un número", normalized_text="dime un numero")
    result = await integer_resolver.resolve(context, definition)
    assert result.status == ParameterResolutionStatus.UNRESOLVED_OPTIONAL
    assert result.value is None

@pytest.mark.asyncio
async def test_resolve_no_number_required(integer_resolver):
    req_def = ParameterDefinition(name="max", type="Integer", required=True)
    context = PluginContext(raw_text="Dime un número", normalized_text="dime un numero")
    result = await integer_resolver.resolve(context, req_def)
    assert result.status == ParameterResolutionStatus.UNRESOLVED_REQUIRED
    assert result.value is None

@pytest.mark.asyncio
async def test_resolve_multiple_numbers_extracts_first(integer_resolver, definition):
    context = PluginContext(raw_text="Dime un número entre 10 y 50", normalized_text="dime un numero entre 10 y 50")
    result = await integer_resolver.resolve(context, definition)
    assert result.status == ParameterResolutionStatus.RESOLVED
    assert result.value == 10

@pytest.mark.asyncio
async def test_resolve_ciento_isolated_fails(integer_resolver, definition):
    context = PluginContext(raw_text="Dame ciento opciones", normalized_text="dame ciento opciones")
    result = await integer_resolver.resolve(context, definition)
    assert result.status == ParameterResolutionStatus.UNRESOLVED_OPTIONAL
    assert result.value is None

