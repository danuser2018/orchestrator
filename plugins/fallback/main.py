import random
import logging
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from typing import List

logger = logging.getLogger(__name__)

class FallbackPlugin(Plugin):
    @property
    def name(self) -> str:
        return "FallbackPlugin"

    @property
    def description(self) -> str:
        return "Responde de forma predeterminada cuando no se reconoce la petición."

    @property
    def keywords(self) -> list[str]:
        return []

    @property
    def regex_patterns(self) -> list[str]:
        return []

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.debug("FallbackPlugin selected")

        try:
            responses = [
                "No he entendido la petición.",
                "No he entendido la orden.",
                "Petición no reconocida."
            ]

            selected_response = random.choice(responses)
            logger.debug(f"Selected response: {selected_response}")

            return PluginResult(
                success=True,
                speech=selected_response,
                data={"reason": "no_match"}
            )
        except Exception as e:
            logger.error(f"Error executing FallbackPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )
