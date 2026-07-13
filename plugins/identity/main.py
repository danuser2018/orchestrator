import logging
import re
import httpx
from typing import List

from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.system_service_client import SystemServiceClient

logger = logging.getLogger(__name__)

def build_display_name(name: str, version: str) -> str:
    if not re.match(r"^\d+\.\d+\.\d+$", version):
        raise ValueError(f"Invalid version format: {version}")
    major = version.split(".")[0]
    return f"{name}-{major}"

class IdentityPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "IdentityPlugin"

    @property
    def description(self) -> str:
        return "Responde consultas sobre la identidad de Nova."

    @property
    def id(self) -> str:
        return "identity"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Quién eres?",
            "¿Cómo te llamas?",
            "¿Qué eres?",
            "Cuéntame quién eres.",
            "Preséntate.",
            "Háblame de ti.",
            "¿Eres una inteligencia artificial?",
            "¿Para qué sirves?",
            "¿Cuál es tu función?",
            "Dime quién eres."
        ]



    def initialize(self) -> None:
        logger.info("Initializing IdentityPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of IdentityPlugin")
        try:
            try:
                system_info = await self.client.get_system_info()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving system info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving system info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            try:
                display_name = build_display_name(system_info.name, system_info.version)
            except ValueError as val_err:
                logger.error(f"Version validation failed: {val_err}")
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            logger.info(f"Display name generated: {display_name}")

            speech = f"Soy {display_name}, tu sistema local de automatización."
            
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "name": system_info.name,
                    "version": system_info.version,
                    "display_name": display_name
                }
            )

        except Exception as e:
            logger.error(f"Unexpected exception in IdentityPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class AuthorPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "AuthorPlugin"

    @property
    def description(self) -> str:
        return "Información sobre el autor de Nova"

    @property
    def id(self) -> str:
        return "author"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Quién te ha creado?",
            "¿Quién te hizo?",
            "¿Quién es tu creador?",
            "¿Quién es el autor de Nova?",
            "¿Quién desarrolló Nova?",
            "¿Quién te desarrolló?",
            "Dame el nombre del autor de Nova.",
            "¿Quién programó Nova?",
            "¿Quién escribió el código de Nova?",
            "¿Quién es tu autor?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing AuthorPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of AuthorPlugin")
        try:
            try:
                system_info = await self.client.get_system_info()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving system info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving system info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            speech = f"Nova ha sido desarrollada por {system_info.author}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "author": system_info.author
                }
            )
        except Exception as e:
            logger.error(f"Unexpected exception in AuthorPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class VersionPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VersionPlugin"

    @property
    def description(self) -> str:
        return "Información sobre la versión instalada de Nova"

    @property
    def id(self) -> str:
        return "version"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué versión eres?",
            "¿Qué versión tienes?",
            "¿Qué versión de Nova es esta?",
            "¿Cuál es tu versión?",
            "¿En qué versión estás?",
            "Dime tu versión.",
            "¿Qué versión está instalada?",
            "¿Qué release tienes?",
            "¿Qué build estás ejecutando?",
            "¿Cuál es la versión actual?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VersionPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VersionPlugin")
        try:
            try:
                system_info = await self.client.get_system_info()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving system info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving system info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            speech = f"Versión {system_info.version}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "version": system_info.version
                }
            )
        except Exception as e:
            logger.error(f"Unexpected exception in VersionPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class HelpPlugin(Plugin):
    @property
    def name(self) -> str:
        return "HelpPlugin"

    @property
    def description(self) -> str:
        return "Explica cómo utilizar Nova"

    @property
    def id(self) -> str:
        return "help"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cómo se usa Nova?",
            "¿Cómo te utilizo?",
            "¿Cómo puedo hablar contigo?",
            "¿Cómo funcionas?",
            "¿Cómo debo usarte?",
            "Explícame cómo utilizar Nova.",
            "¿Cómo puedo darte órdenes?",
            "Ayuda.",
            "Necesito ayuda.",
            "¿Cómo empiezo?"
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of HelpPlugin")
        speech = "Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: \"¿Qué tiempo hace?\" o \"Enciende la luz del salón.\""
        return PluginResult(
            success=True,
            speech=speech,
            data={}
        )

