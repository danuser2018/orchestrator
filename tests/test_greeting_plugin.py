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
        "Buenas tardes.",
        "Buenas noches.",
        "Hola."
    ]

def test_greeting_plugin_keywords_and_regex(plugin):
    assert "hola" in plugin.keywords
    assert "buenos dias" in plugin.keywords
    assert r"^hola$" in plugin.regex_patterns
    assert r"^hola[.!?]?$" in plugin.regex_patterns
