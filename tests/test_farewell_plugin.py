import pytest
from core.models import PluginContext
from plugins.farewell.main import FarewellPlugin

@pytest.fixture
def plugin():
    return FarewellPlugin()

@pytest.mark.asyncio
async def test_farewell_plugin_execution(plugin):
    context = PluginContext(raw_text="adios", normalized_text="adios")
    result = await plugin.execute(context)

    assert result.success is True
    assert result.speech in [
               "Adiós.",
	       "Hasta pronto.",
	       "Hasta luego.",
               "Vale.",
               "De acuerdo."
   ]



def test_farewell_plugin_properties(plugin):
    assert plugin.id == "farewell"
    assert plugin.priority == 100
    assert len(plugin.examples) == 10
    assert "Adiós." in plugin.examples
    assert "Puedes irte." in plugin.examples
