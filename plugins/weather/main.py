from core.models import PluginContext, PluginResult
from plugins.base import Plugin

class WeatherPlugin(Plugin):
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



    async def execute(self, context: PluginContext) -> PluginResult:
        # Simulación
        is_raining = False
        temp = 22
        
        speech = f"Actualmente hace {temp} grados. "
        speech += "No parece que vaya a llover." if not is_raining else "Llévate un paraguas, está lloviendo."
        
        return PluginResult(
            success=True,
            speech=speech,
            data={"temp": temp, "is_raining": is_raining}
        )
