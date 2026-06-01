from core.models import PluginContext, PluginResult
from plugins.base import Plugin

class FallbackPlugin(Plugin):
    @property
    def name(self) -> str:
        return "FallbackPlugin"

    @property
    def keywords(self) -> list[str]:
        return []

    @property
    def regex_patterns(self) -> list[str]:
        return []

    async def execute(self, context: PluginContext) -> PluginResult:
        return PluginResult(
            success=False,
            speech="Lo siento, no he entendido qué quieres hacer.",
            data={"reason": "no_match"}
        )
