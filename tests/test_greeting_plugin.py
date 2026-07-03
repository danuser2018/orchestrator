import pytest
from core.models import PluginContext
from plugins.greeting.main import GreetingPlugin

@pytest.fixture
def plugin():
    return GreetingPlugin()

@pytest.mark.asyncio
async def test_greeting_plugin_execution(plugin):
    context = PluginContext(raw_text="hola", normalized_text="hola")
    result = await plugin.execute(context)
    
    assert result.success is True
    assert result.speech in [
        "Buenos días.",
        "Buenos días, te escucho.",
        "Hola, buenos días.",
        "Buenas tardes.",
        "Buenas tardes, te escucho.",
        "Hola, buenas tardes.",
        "Buenas noches.",
        "Buenas noches, te escucho.",
        "Hola, buenas noches."
    ]



def test_greeting_plugin_properties(plugin):
    assert plugin.id == "greeting"
    assert plugin.priority == 100
    assert len(plugin.examples) == 10
    assert "Hola." in plugin.examples
    assert "Hola, ¿qué tal?" in plugin.examples
