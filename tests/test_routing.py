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
    assert plan.steps[0].plugin == "AuthorPlugin"

@pytest.mark.asyncio
async def test_route_version_plugin(planner):
    req = UserRequest(text="¿Qué versión tienes?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "VersionPlugin"

@pytest.mark.asyncio
async def test_route_help_plugin(planner):
    req = UserRequest(text="Ayuda")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "HelpPlugin"

@pytest.mark.asyncio
async def test_route_time_plugin(planner):
    req = UserRequest(text="¿Qué hora marca el reloj?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "TimePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_mes(planner):
    req = UserRequest(text="¿En qué mes estamos?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "DatePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_ano(planner):
    req = UserRequest(text="¿En qué año estamos?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "DatePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_fecha(planner):
    req = UserRequest(text="Fecha actual.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "DatePlugin"

@pytest.mark.asyncio
async def test_route_coin_plugin(planner):
    req = UserRequest(text="Lanza una moneda al aire.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "CoinPlugin"

@pytest.mark.asyncio
async def test_route_dice_plugin(planner):
    req = UserRequest(text="Tira los dados.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "DicePlugin"

@pytest.mark.asyncio
async def test_route_random_number_plugin_1(planner):
    req = UserRequest(text="Dame un número aleatorio.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "RandomNumberPlugin"

@pytest.mark.asyncio
async def test_route_random_number_plugin_2(planner):
    req = UserRequest(text="Número al azar.")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "RandomNumberPlugin"

@pytest.mark.asyncio
async def test_route_volume_up_plugin(planner):
    req = UserRequest(text="Sube un poco el volumen")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "VolumeUpPlugin"

@pytest.mark.asyncio
async def test_route_volume_down_plugin(planner):
    req = UserRequest(text="Ponlo más bajo")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "VolumeDownPlugin"

@pytest.mark.asyncio
async def test_route_volume_status_plugin(planner):
    req = UserRequest(text="¿Qué volumen tengo?")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "VolumeStatusPlugin"

@pytest.mark.asyncio
async def test_route_mute_plugin(planner):
    req = UserRequest(text="Silénciate")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "MutePlugin"

@pytest.mark.asyncio
async def test_route_unmute_plugin(planner):
    req = UserRequest(text="Activa el sonido")
    plan = await planner.resolve(req)
    assert len(plan.steps) == 1
    assert plan.steps[0].plugin == "UnmutePlugin"
