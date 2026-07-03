import warnings
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
    def keywords(self) -> List[str]:
        """DEPRECATED: Not used by the PluginMatcher engine. Use `examples` instead."""
        warnings.warn(
            f"`keywords` in plugin '{self.__class__.__name__}' is deprecated and not used by the "
            "PluginMatcher engine. Declare natural language `examples` instead (see ADR-004).",
            DeprecationWarning,
            stacklevel=2,
        )
        return []

    @property
    def regex_patterns(self) -> List[str]:
        """DEPRECATED: Not used by the PluginMatcher engine. Use `examples` instead."""
        warnings.warn(
            f"`regex_patterns` in plugin '{self.__class__.__name__}' is deprecated and not used by "
            "the PluginMatcher engine. Declare natural language `examples` instead (see ADR-004).",
            DeprecationWarning,
            stacklevel=2,
        )
        return []

    @property
    def exclusive_regex(self) -> str | None:
        """DEPRECATED: Not used by the PluginMatcher engine. Use `examples` instead."""
        warnings.warn(
            f"`exclusive_regex` in plugin '{self.__class__.__name__}' is deprecated and not used by "
            "the PluginMatcher engine. Declare natural language `examples` instead (see ADR-004).",
            DeprecationWarning,
            stacklevel=2,
        )
        return None

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
