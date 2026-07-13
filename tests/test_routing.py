import pytest
from core.engine import Router
from core.models import UserRequest
from core.plugin_manager import PluginManager
from core.similarity import RapidFuzzSimilarityEngine

@pytest.fixture
def router():
    manager = PluginManager(plugins_dir="plugins")
    manager.discover_and_load()
    similarity_engine = RapidFuzzSimilarityEngine()
    return Router(plugin_manager=manager, similarity_engine=similarity_engine)

@pytest.mark.asyncio
async def test_route_author_plugin(router):
    req = UserRequest(text="¿Quién es el autor de Nova?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "AuthorPlugin"

@pytest.mark.asyncio
async def test_route_version_plugin(router):
    req = UserRequest(text="¿Qué versión tienes?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "VersionPlugin"

@pytest.mark.asyncio
async def test_route_help_plugin(router):
    req = UserRequest(text="Ayuda")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "HelpPlugin"

@pytest.mark.asyncio
async def test_route_time_plugin(router):
    req = UserRequest(text="¿Qué hora marca el reloj?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "TimePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_mes(router):
    req = UserRequest(text="¿En qué mes estamos?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "DatePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_ano(router):
    req = UserRequest(text="¿En qué año estamos?")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "DatePlugin"

@pytest.mark.asyncio
async def test_route_date_plugin_fecha(router):
    req = UserRequest(text="Fecha actual.")
    plugin, context = await router.route_request(req)
    
    assert plugin is not None
    assert plugin.name == "DatePlugin"
