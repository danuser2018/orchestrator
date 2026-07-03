import random
import logging
from typing import List

from core.models import PluginContext, PluginResult
from plugins.base import Plugin

logger = logging.getLogger(__name__)

class FarewellPlugin(Plugin):

    @property
    def name(self) -> str:
        return "FarewellPlugin"

    @property
    def description(self) -> str:
        return "Responde a mensajes de despedida del usuario."

    @property
    def id(self) -> str:
        return "farewell"

    @property
    def priority(self) -> int:
        return 100

    @property
    def examples(self) -> List[str]:
        return [
            "Adiós.",
            "Hasta luego.",
            "Hasta pronto.",
            "Nos vemos.",
            "Chao.",
            "Me voy.",
            "Eso es todo.",
            "Ya hemos terminado.",
            "Gracias, hasta luego.",
            "Puedes irte."
        ]

    @property
    def keywords(self) -> List[str]:
        return [
            "gracias",
	    "adios",
	    "terminado",
	    "luego"
        ]

    @property
    def regex_patterns(self) -> List[str]:
        return [
	    r"\bgracias\b",
	    r"\badios\b",
	    r"\bhasta luego\b",
	    r"\bhasta pronto\b",
	    r"\bnos vemos\b",
	    r"\bya he terminado\b",
	    r"\bno necesito nada mas\b",
	    r"\beso es todo\b"
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.debug("FarewellPlugin selected")

        try:
            responses = [
               "Adiós.",
	       "Hasta pronto.",
	       "Hasta luego.",
               "Vale.",
               "De acuerdo."
            ]

            selected_response = random.choice(responses)
            logger.debug(f"Selected response: {selected_response}")

            return PluginResult(
                success=True,
                speech=selected_response
            )
        except Exception as e:
            logger.error(f"Error executing FarewellPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )

