import datetime
import random
import logging
from typing import List

from core.models import PluginContext, PluginResult
from plugins.base import Plugin

logger = logging.getLogger(__name__)

class GreetingPlugin(Plugin):
    @property
    def name(self) -> str:
        return "GreetingPlugin"

    @property
    def description(self) -> str:
        return "Responde a saludos del usuario."

    @property
    def id(self) -> str:
        return "greeting"

    @property
    def priority(self) -> int:
        return 100

    @property
    def examples(self) -> List[str]:
        return [
            "Hola.",
            "Buenos días.",
            "Buenas tardes.",
            "Buenas noches.",
            "Hola, Nova.",
            "Buenos días, Nova.",
            "¿Hay alguien?",
            "¿Estás ahí?",
            "¿Me escuchas?",
            "Hola, ¿qué tal?"
        ]



    async def execute(self, context: PluginContext) -> PluginResult:
        logger.debug("GreetingPlugin selected")
        
        try:
            current_hour = datetime.datetime.now().hour
            
            if 6 <= current_hour < 12:
                logger.debug("Detected greeting period: morning")
                responses = [
                    "Buenos días.",
                    "Buenos días, te escucho.",
                    "Hola, buenos días."
                ]
            elif 12 <= current_hour < 21:
                logger.debug("Detected greeting period: afternoon")
                responses = [
                    "Buenas tardes.",
                    "Buenas tardes, te escucho.",
                    "Hola, buenas tardes."
                ]
            else:
                logger.debug("Detected greeting period: evening")
                responses = [
                    "Buenas noches.",
                    "Buenas noches, te escucho.",
                    "Hola, buenas noches."
                ]
                
            selected_response = random.choice(responses)
            logger.debug(f"Selected response: {selected_response}")
            
            return PluginResult(
                success=True,
                speech=selected_response
            )
        except Exception as e:
            logger.error(f"Error executing GreetingPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )
