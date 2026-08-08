import pytest
from plugins.base import Plugin
from core.models import PluginContext, PluginResult

class LegacyPlugin(Plugin):
    @property
    def name(self) -> str:
        return "LegacyPlugin"

    @property
    def description(self) -> str:
        return "Legacy plugin without declaring parameters property"

    @property
    def id(self) -> str:
        return "legacy_plugin"

    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(success=True, speech="ok")

def test_legacy_plugin_parameters_default():
    plugin = LegacyPlugin()
    assert hasattr(plugin, "parameters")
    assert plugin.parameters == []
