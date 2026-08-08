from abc import ABC, abstractmethod
from core.models import PluginContext
from .models import ParameterDefinition, ParameterResolutionResult

class BaseParameterResolver(ABC):
    @property
    @abstractmethod
    def target_type(self) -> str:
        """Return the logical type handled by this resolver (e.g. 'Integer', 'Date')."""
        pass

    @abstractmethod
    async def resolve(
        self, 
        context: PluginContext, 
        definition: ParameterDefinition
    ) -> ParameterResolutionResult:
        """Resolve a single parameter from the user text/context."""
        pass
