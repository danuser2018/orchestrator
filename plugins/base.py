from abc import ABC, abstractmethod
from typing import List
from core.models import PluginContext, PluginResult
from core.parameter_resolution.models import ParameterDefinition

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Functional description of the capability."""
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique snake_case identifier for the plugin."""
        pass

    @property
    def priority(self) -> int:
        """Priority level of the plugin (0 to 100). Default is 60 (Medium)."""
        return 60

    @property
    def examples(self) -> List[str]:
        """Collection of natural language example phrases to trigger this plugin."""
        return []

    @property
    def parameters(self) -> List[ParameterDefinition]:
        """Collection of parameters declared by the plugin. Default is empty list."""
        return []


    def initialize(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def __getattribute__(self, name: str):
        val = super().__getattribute__(name)
        if name == "examples" and isinstance(val, list):
            return [e for e in val if isinstance(e, str) and e.strip()]
        return val

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
