from typing import Dict, Optional
from .base import BaseParameterResolver

class ParameterResolverRegistry:
    def __init__(self):
        self._resolvers: Dict[str, BaseParameterResolver] = {}

    def register(self, resolver: BaseParameterResolver) -> None:
        type_key = resolver.target_type.lower()
        self._resolvers[type_key] = resolver

    def get(self, target_type: str) -> Optional[BaseParameterResolver]:
        return self._resolvers.get(target_type.lower())

    def unregister(self, target_type: str) -> None:
        self._resolvers.pop(target_type.lower(), None)
