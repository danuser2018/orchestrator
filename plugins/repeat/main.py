import httpx
import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.context_service_client import ContextServiceClient

logger = logging.getLogger(__name__)

class RepeatPlugin(Plugin):
    def initialize(self) -> None:
        self.client = ContextServiceClient()

    @property
    def name(self) -> str:
        return "RepeatPlugin"

    @property
    def description(self) -> str:
        return "Permite al usuario solicitar que Nova repita la última respuesta generada."

    @property
    def id(self) -> str:
        return "repeat"

    @property
    def priority(self) -> int:
        return 70

    @property
    def examples(self) -> List[str]:
        return [
            "Repite.",
            "Repite, por favor.",
            "¿Puedes repetir?",
            "¿Qué has dicho?",
            "Dímelo otra vez.",
            "No te he oído.",
            "No lo he entendido.",
            "¿Cómo has dicho?"
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.debug("RepeatPlugin selected")
        try:
            last_resp = await self.client.get_last_response()
            if last_resp is None:
                return PluginResult(
                    success=True,
                    speech="No hay respuestas anteriores."
                )
            return PluginResult(
                success=True,
                speech=last_resp.response,
                data={
                    "repeated_plugin": last_resp.plugin,
                    "repeated_timestamp": last_resp.timestamp
                }
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection failure to context-service: {conn_err}")
            return PluginResult(
                success=False,
                speech="Servicio no disponible."
            )
        except httpx.HTTPError as http_err:
            logger.error(f"HTTP error from context-service: {http_err}")
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
        except Exception as exc:
            logger.error(f"Unexpected error executing RepeatPlugin: {exc}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
