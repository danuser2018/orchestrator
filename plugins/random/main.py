import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.random_service import RandomService
from core.parameter_resolution.models import ParameterDefinition

logger = logging.getLogger(__name__)

class CoinPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "CoinPlugin"

    @property
    def description(self) -> str:
        return "Lanza una moneda y devuelve cara o cruz"

    @property
    def id(self) -> str:
        return "coin"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Lanza una moneda.",
            "Tira una moneda.",
            "Cara o cruz.",
            "Decide con una moneda.",
            "Haz un cara o cruz.",
            "Lanza una moneda al aire.",
            "Necesito un cara o cruz.",
            "Elige cara o cruz.",
            "Vamos a lanzar una moneda.",
            "Moneda."
        ]

    def initialize(self) -> None:
        logger.info("Initializing CoinPlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of CoinPlugin")
        try:
            result = self.random_service.flip_coin()
            # Response formatting: 'Cara.' or 'Cruz.'
            speech = f"{result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error executing CoinPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )


class DicePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "DicePlugin"

    @property
    def description(self) -> str:
        return "Lanza un dado de seis caras"

    @property
    def id(self) -> str:
        return "dice"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Tira un dado.",
            "Lanza un dado.",
            "Necesito un dado.",
            "Haz una tirada de dado.",
            "Dime un número del dado.",
            "Lanza el dado.",
            "Vamos a tirar un dado.",
            "Tira los dados.",
            "Quiero lanzar un dado.",
            "Dado."
        ]

    def initialize(self) -> None:
        logger.info("Initializing DicePlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of DicePlugin")
        try:
            result = self.random_service.roll_dice()
            # Response formatting conforming to Tone Guide
            speech = f"Ha salido un {result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error executing DicePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )


class RandomNumberPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "RandomNumberPlugin"

    @property
    def description(self) -> str:
        return "Genera un número aleatorio"

    @property
    def id(self) -> str:
        return "random-number"

    @property
    def priority(self) -> int:
        return 60

    @property
    def parameters(self) -> List[ParameterDefinition]:
        return [
            ParameterDefinition(
                name="max",
                type="Integer",
                required=False,
                default=100
            )
        ]

    @property
    def examples(self) -> List[str]:
        return [
            "Elige un número.",
            "Dime un número.",
            "Dame un número aleatorio.",
            "Escoge un número.",
            "Número al azar.",
            "Piensa un número.",
            "Necesito un número.",
            "Elige un número para mí.",
            "Genera un número.",
            "Número aleatorio."
        ]

    def initialize(self) -> None:
        logger.info("Initializing RandomNumberPlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of RandomNumberPlugin")
        try:
            max_value = context.parameters.get("max", 100) if context.parameters else 100
            if not isinstance(max_value, int) or max_value < 1:
                max_value = 100

            result = self.random_service.random_int(1, max_value)
            # Response formatting conforming to Tone Guide (direct data format: '{value}.')
            speech = f"{result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result,
                    "max": max_value
                }
            )
        except Exception as e:
            logger.error(f"Error executing RandomNumberPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )

