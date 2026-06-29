from abc import ABC, abstractmethod
from typing import List
from core.models import PluginContext, PluginResult

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    def keywords(self) -> List[str]:
        return []

    @property
    def regex_patterns(self) -> List[str]:
        return []

    @property
    def exclusive_regex(self) -> str | None:
        return None

    def initialize(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
