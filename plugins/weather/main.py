import logging
import httpx
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.weather_service_client import WeatherServiceClient

logger = logging.getLogger(__name__)

class WeatherPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "WeatherPlugin"

    @property
    def description(self) -> str:
        return "Responde consultas sobre el tiempo y el clima."

    @property
    def id(self) -> str:
        return "weather"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> list[str]:
        return [
            "¿Qué tiempo hace?",
            "¿Qué tiempo hará mañana?",
            "¿Va a llover hoy?",
            "¿Qué temperatura hay?",
            "¿Cómo está el tiempo?",
            "Dime el pronóstico del tiempo.",
            "¿Va a hacer calor hoy?",
            "¿Necesito paraguas?",
            "¿Qué clima hace?",
            "¿Cómo estará el tiempo esta tarde?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing WeatherPlugin")
        self.client = WeatherServiceClient()

    def _get_precipitation_msg(self, probability: int) -> str:
        if probability <= 20:
            return "No parece que vaya a llover."
        elif probability <= 40:
            return "Hay poca probabilidad de lluvia."
        elif probability <= 60:
            return "Podría llover."
        elif probability <= 80:
            return "Es probable que llueva."
        else:
            return "Es muy probable que llueva."

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of WeatherPlugin")
        try:
            try:
                weather_info = await self.client.get_current_weather()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to Weather Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving weather info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving weather info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            rounded_temp = int(round(weather_info.temperature))
            precip_msg = self._get_precipitation_msg(weather_info.precipitation_probability)
            speech = f"{rounded_temp} grados. {precip_msg}"

            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "temperature": weather_info.temperature,
                    "precipitation_probability": weather_info.precipitation_probability
                }
            )

        except Exception as e:
            logger.error(f"Unexpected exception in WeatherPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
