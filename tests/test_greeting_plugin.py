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
        "Buenos días. ¿Qué necesitas?",
        "Hola. ¿En qué puedo ayudarte?",
        "Buenas tardes.",
        "Buenas tardes, te escucho.",
        "Hola, buenas tardes.",
        "Buenas tardes. ¿Qué necesitas?",
        "Buenas noches.",
        "Buenas noches, te escucho.",
        "Hola, buenas noches.",
        "Buenas noches. ¿Qué necesitas?"
    ]

def test_greeting_plugin_keywords_and_regex(plugin):
    assert "hola" in plugin.keywords
    assert "buenos dias" in plugin.keywords
    assert r"^hola$" in plugin.regex_patterns
    assert r"^hola[.!?]?$" in plugin.regex_patterns
