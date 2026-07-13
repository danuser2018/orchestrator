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
