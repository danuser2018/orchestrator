import logging
from typing import List
import httpx
from core.models import PluginContext, PluginResult
from core.parameter_resolution.models import ParameterDefinition
from plugins.base import Plugin
from core.host_service_client import HostServiceClient

logger = logging.getLogger(__name__)

class VolumeUpPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeUpPlugin"

    @property
    def description(self) -> str:
        return "Incrementa el volumen del sistema"

    @property
    def id(self) -> str:
        return "volume-up"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Sube el volumen",
            "Sube un poco el volumen",
            "Más volumen",
            "Pon el volumen más alto",
            "Aumenta el volumen",
            "Quiero más volumen",
            "Dale más volumen",
            "Súbelo",
            "Un poco más alto",
            "Se oye bajo"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeUpPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeUpPlugin")
        try:
            result = await self.client.volume_up(10)
            if result.volume >= 100:
                speech = "Volumen al máximo."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeUpPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class VolumeDownPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeDownPlugin"

    @property
    def description(self) -> str:
        return "Disminuye el volumen del sistema"

    @property
    def id(self) -> str:
        return "volume-down"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Baja el volumen",
            "Menos volumen",
            "Baja un poco",
            "Está muy alto",
            "Reduce el volumen",
            "Bájalo",
            "Un poco menos",
            "Demasiado volumen",
            "Ponlo más bajo",
            "Quiero menos volumen"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeDownPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeDownPlugin")
        try:
            result = await self.client.volume_down(10)
            if result.volume <= 0:
                speech = "Volumen al mínimo."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeDownPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class VolumeStatusPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeStatusPlugin"

    @property
    def description(self) -> str:
        return "Consulta el volumen actual del sistema"

    @property
    def id(self) -> str:
        return "volume-status"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cuál es el volumen?",
            "¿Qué volumen tengo?",
            "¿Cuál es el volumen actual?",
            "Dime el volumen",
            "¿Cómo está el volumen?",
            "Nivel de volumen",
            "¿A cuánto está el volumen?",
            "Volumen actual",
            "¿Qué nivel de sonido hay?",
            "¿Está muy alto el volumen?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeStatusPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeStatusPlugin")
        try:
            result = await self.client.get_volume()
            if result.muted:
                speech = f"Volumen al {result.volume} por ciento y silenciado."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeStatusPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class MutePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "MutePlugin"

    @property
    def description(self) -> str:
        return "Silencia el sistema"

    @property
    def id(self) -> str:
        return "mute"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Mutéate",
            "Silénciate",
            "Quítate el sonido",
            "Ponte en silencio",
            "Deja de hacer ruido",
            "No hables",
            "Silencio",
            "Apaga el sonido",
            "Enmudece",
            "No quiero oírte"
        ]

    def initialize(self) -> None:
        logger.info("Initializing MutePlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of MutePlugin")
        try:
            result = await self.client.mute()
            return PluginResult(
                success=True,
                speech="Hecho.",
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing MutePlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class UnmutePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "UnmutePlugin"

    @property
    def description(self) -> str:
        return "Restaura el sonido del sistema"

    @property
    def id(self) -> str:
        return "unmute"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Desmutéate",
            "Activa el sonido",
            "Recupera el sonido",
            "Vuelve a hablar",
            "Quita el silencio",
            "Ya puedes hablar",
            "Activa el audio",
            "Devuelve el sonido",
            "Sal del modo silencio",
            "Ya puedes hacer ruido"
        ]

    def initialize(self) -> None:
        logger.info("Initializing UnmutePlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of UnmutePlugin")
        try:
            result = await self.client.unmute()
            return PluginResult(
                success=True,
                speech="Sonido activado.",
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing UnmutePlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class VolumeSetPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeSetPlugin"

    @property
    def description(self) -> str:
        return "Establece el volumen de audio del sistema a un valor absoluto entre 0 y 100"

    @property
    def id(self) -> str:
        return "volume-set"

    @property
    def priority(self) -> int:
        return 60

    @property
    def parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="volume",
                type="Integer",
                required=True
            )
        ]

    @property
    def examples(self) -> List[str]:
        return [
            "Pon el volumen al 50",
            "Establece el volumen en 30",
            "Fija el volumen al 75",
            "Pon el volumen al 100",
            "Volumen al 20",
            "Pon el volumen a cero",
            "Ajusta el volumen al 80 por ciento",
            "Pon el volumen en cincuenta",
            "Pon el volumen al 10",
            "Fijar el volumen a 40"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeSetPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeSetPlugin")
        raw_val = context.parameters.get("volume") if context.parameters else None

        if raw_val is None:
            return PluginResult(
                success=False,
                speech="Indica un nivel de volumen."
            )

        if not isinstance(raw_val, int) or isinstance(raw_val, bool) or raw_val < 0 or raw_val > 100:
            return PluginResult(
                success=False,
                speech="Indica un volumen entre 0 y 100."
            )

        try:
            result = await self.client.set_volume(raw_val)
            speech = f"Volumen al {result.volume} por ciento."
            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeSetPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")

