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
	       "Hasta pronto",
               "Nos vemos",
	       "Hasta luego",
               "Perfecto",
               "Cuando necesites algo más, aquí estaré",
               "Vuelve cuando quieras",
               "Me alegra ser de ayuda",
               "Estoy aquí mismo, si necesitas ayuda de nuevo"
   ]

def test_farewell_plugin_keywords_and_regex(plugin):
    assert "gracias" in plugin.keywords
    assert "adios" in plugin.keywords
    assert "terminado" in plugin.keywords
    assert "luego" in plugin.keywords
    assert r"\bgracias\b" in plugin.regex_patterns
    assert r"\badios\b" in plugin.regex_patterns
    assert r"\bhasta luego\b" in plugin.regex_patterns
    assert r"\bhasta pronto\b" in plugin.regex_patterns
    assert r"\bnos vemos\b" in plugin.regex_patterns
    assert r"\bya he terminado\b" in plugin.regex_patterns
    assert r"\bno necesito nada mas\b" in plugin.regex_patterns
    assert r"\beso es todo\b" in plugin.regex_patterns
