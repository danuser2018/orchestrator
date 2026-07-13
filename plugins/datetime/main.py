import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.datetime_service import DateTimeService

logger = logging.getLogger(__name__)

class TimePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.datetime_service = None

    @property
    def name(self) -> str:
        return "TimePlugin"

    @property
    def description(self) -> str:
        return "Consulta la hora actual"

    @property
    def id(self) -> str:
        return "time"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué hora es?",
            "Dime la hora.",
            "¿Me dices la hora?",
            "¿Qué hora tenemos?",
            "¿Puedes decirme la hora?",
            "Necesito saber la hora.",
            "Hora actual.",
            "¿Cuál es la hora?",
            "¿Qué hora marca el reloj?",
            "¿Tienes la hora?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing TimePlugin")
        self.datetime_service = DateTimeService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of TimePlugin")
        try:
            time_str = self.datetime_service.get_current_time()
            speech = f"Son las {time_str}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "time": time_str
                }
            )
        except Exception as e:
            logger.error(f"Error executing TimePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class DatePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.datetime_service = None

    @property
    def name(self) -> str:
        return "DatePlugin"

    @property
    def description(self) -> str:
        return "Consulta la fecha actual"

    @property
    def id(self) -> str:
        return "date"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué día es hoy?",
            "¿Cuál es la fecha de hoy?",
            "¿Qué fecha es?",
            "¿En qué mes estamos?",
            "¿En qué año estamos?",
            "Dime la fecha.",
            "¿Qué día tenemos hoy?",
            "¿Qué mes es?",
            "¿Qué año es?",
            "Fecha actual."
        ]

    def initialize(self) -> None:
        logger.info("Initializing DatePlugin")
        self.datetime_service = DateTimeService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of DatePlugin")
        try:
            date_str = self.datetime_service.get_current_date()
            return PluginResult(
                success=True,
                speech=date_str,
                data={
                    "date": date_str
                }
            )
        except Exception as e:
            logger.error(f"Error executing DatePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
