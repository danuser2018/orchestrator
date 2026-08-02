import pytest
from core.engine import ExecutionPlanner
from core.models import UserRequest
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine

@pytest.fixture
def planner():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    return ExecutionPlanner(plugin_manager=manager, similarity_engine=similarity_engine)

@pytest.mark.asyncio
async def test_route_author_plugin(planner):
    req = UserRequest(text="¿Quién es el autor de Nova?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "author"

@pytest.mark.asyncio
async def test_route_version_plugin(planner):
    req = UserRequest(text="¿Qué versión tienes?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "version"

@pytest.mark.asyncio
async def test_route_help_plugin(planner):
    req = UserRequest(text="Ayuda")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "help"

@pytest.mark.asyncio
async def test_route_time_plugin(planner):
    req = UserRequest(text="¿Qué hora marca el reloj?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "time"

@pytest.mark.asyncio
async def test_route_date_plugin_mes(planner):
    req = UserRequest(text="¿En qué mes estamos?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "date"

@pytest.mark.asyncio
async def test_route_date_plugin_ano(planner):
    req = UserRequest(text="¿En qué año estamos?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "date"

@pytest.mark.asyncio
async def test_route_date_plugin_fecha(planner):
    req = UserRequest(text="Fecha actual.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "date"

@pytest.mark.asyncio
async def test_route_coin_plugin(planner):
    req = UserRequest(text="Lanza una moneda al aire.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "coin"

@pytest.mark.asyncio
async def test_route_dice_plugin(planner):
    req = UserRequest(text="Tira los dados.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "dice"

@pytest.mark.asyncio
async def test_route_random_number_plugin_1(planner):
    req = UserRequest(text="Dame un número aleatorio.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "random-number"

@pytest.mark.asyncio
async def test_route_random_number_plugin_2(planner):
    req = UserRequest(text="Número al azar.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "random-number"

@pytest.mark.asyncio
async def test_route_volume_up_plugin(planner):
    req = UserRequest(text="Sube un poco el volumen")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "volume-up"

@pytest.mark.asyncio
async def test_route_volume_down_plugin(planner):
    req = UserRequest(text="Ponlo más bajo")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "volume-down"

@pytest.mark.asyncio
async def test_route_volume_status_plugin(planner):
    req = UserRequest(text="¿Qué volumen tengo?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "volume-status"

@pytest.mark.asyncio
async def test_route_mute_plugin(planner):
    req = UserRequest(text="Silénciate")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "mute"

@pytest.mark.asyncio
async def test_route_unmute_plugin(planner):
    req = UserRequest(text="Activa el sonido")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "unmute"

@pytest.mark.asyncio
async def test_route_today_holiday_plugin(planner):
    req = UserRequest(text="¿Hoy es festivo?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "today_holiday"

@pytest.mark.asyncio
async def test_route_next_holiday_plugin(planner):
    req = UserRequest(text="¿Cuál es el próximo festivo?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "next_holiday"

@pytest.mark.asyncio
async def test_route_days_until_next_holiday_plugin(planner):
    req = UserRequest(text="¿Cuánto falta para el próximo festivo?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "days_until_next_holiday"

@pytest.mark.asyncio
async def test_route_holidays_of_year_plugin(planner):
    req = UserRequest(text="¿Qué festivos hay este año?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "holidays_of_year"
