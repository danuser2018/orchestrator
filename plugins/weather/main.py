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
    def keywords(self) -> list[str]:
        return ["tiempo", "clima", "lluvia", "sol", "temperatura", "frio", "calor"]

    @property
    def regex_patterns(self) -> list[str]:
        return [r"que.*tiempo.*hace", r"va.*a.*llover"]

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
