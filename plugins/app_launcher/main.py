from typing import List, Optional
import httpx

from core.logger import logger
from core.models import PluginContext, PluginResult
from core.parameter_resolution.models import ParameterDefinition
from core.host_service_client import HostServiceClient
from plugins.base import Plugin


class AppLauncherPlugin(Plugin):
    """
    Plugin that routes natural-language instructions to launch host applications
    via host-service HAL. Supports dynamically updated trigger examples received
    asynchronously via NATS.
    """

    DEFAULT_COLD_START_EXAMPLES: List[str] = [
        "abre una aplicacion",
        "abrir aplicacion",
        "ejecuta una aplicacion",
        "ejecutar programa",
        "iniciar programa",
        "lanzar aplicacion",
        "abrir el programa",
        "abre el programa",
        "ejecuta un programa",
        "inicia la aplicacion",
    ]

    def __init__(self):
        super().__init__()
        self.client: Optional[HostServiceClient] = None
        self._dynamic_examples: List[str] = list(self.DEFAULT_COLD_START_EXAMPLES)

    @property
    def name(self) -> str:
        return "AppLauncherPlugin"

    @property
    def description(self) -> str:
        return "Abre y ejecuta aplicaciones del entorno host local"

    @property
    def id(self) -> str:
        return "open_app"

    @property
    def priority(self) -> int:
        return 60

    @property
    def parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="command",
                type="Command",
                required=True,
                description="Identificador logico del comando o aplicacion a ejecutar",
            )
        ]

    @property
    def risk_policy(self) -> dict:
        return {
            "policy": "lookup",
            "source": "command",
            "table": "host_commands",
        }

    @property
    def examples(self) -> List[str]:
        return list(self._dynamic_examples)

    def load_dynamic_phrases(self, new_phrases: List[str]) -> None:
        """
        Updates in-memory trigger examples with dynamic phrases received from host-service via NATS.
        Preserves cold-start fallback examples and appends unique new phrases.
        """
        cleaned = [p.strip() for p in new_phrases if isinstance(p, str) and p.strip()]
        combined = list(dict.fromkeys(self.DEFAULT_COLD_START_EXAMPLES + cleaned))
        self._dynamic_examples = combined
        logger.info(
            f"AppLauncherPlugin: updated dynamic examples ({len(self._dynamic_examples)} total phrases)."
        )

    def initialize(self) -> None:
        logger.info("Initializing AppLauncherPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of AppLauncherPlugin")
        raw_command = context.parameters.get("command") if context.parameters else None

        if not raw_command or not isinstance(raw_command, str) or not raw_command.strip():
            logger.warning("AppLauncherPlugin: Missing or invalid 'command' parameter in context.")
            return PluginResult(
                success=False,
                speech="No he podido abrir la aplicación.",
            )

        command_name = raw_command.strip()
        try:
            if not self.client:
                self.client = HostServiceClient()

            result = await self.client.execute_command(command_name)
            logger.info(
                f"AppLauncherPlugin: Successfully launched '{command_name}' (pid={result.pid})"
            )
            return PluginResult(
                success=True,
                speech="Aplicación abierta.",
                data=result.model_dump(),
            )
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error(
                f"AppLauncherPlugin: Connection error or timeout reaching host-service: {exc}"
            )
            return PluginResult(
                success=False,
                speech="Servicio no disponible.",
            )
        except httpx.HTTPStatusError as exc:
            logger.warning(
                f"AppLauncherPlugin: host-service rejected command '{command_name}' with HTTP {exc.response.status_code}"
            )
            return PluginResult(
                success=False,
                speech="No he podido abrir la aplicación.",
            )
        except Exception as exc:
            logger.error(
                f"AppLauncherPlugin: Unexpected error executing command '{command_name}': {exc}",
                exc_info=True,
            )
            return PluginResult(
                success=False,
                speech="No he podido abrir la aplicación.",
            )
