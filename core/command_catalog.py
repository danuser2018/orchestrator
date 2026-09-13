import logging
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from core.events import PublicCommandEntry

logger = logging.getLogger(__name__)


@dataclass
class NormalizedCommandEntry:
    name: str
    risk: str
    phrases: List[str]
    normalized_phrases: List[str]


class CommandCatalogProjection:
    def __init__(self):
        self._commands: Dict[str, NormalizedCommandEntry] = {}
        self._is_ready: bool = False

    def update_from_event(self, commands: List[PublicCommandEntry], normalizer_fn: Callable[[str], str]):
        new_catalog: Dict[str, NormalizedCommandEntry] = {}
        for entry in commands:
            name = entry["name"] if isinstance(entry, dict) else entry.name
            risk = entry["risk"] if isinstance(entry, dict) else entry.risk
            phrases = entry["phrases"] if isinstance(entry, dict) else entry.phrases
            norm_phrases = [normalizer_fn(p) for p in phrases if normalizer_fn(p)]
            new_catalog[name] = NormalizedCommandEntry(
                name=name,
                risk=risk,
                phrases=phrases,
                normalized_phrases=norm_phrases,
            )
        self._commands = new_catalog
        self._is_ready = len(new_catalog) > 0
        logger.info(f"Command catalog projection updated in orchestrator with {len(self._commands)} commands.")

    @property
    def is_ready(self) -> bool:
        return self._is_ready

    def list_commands(self) -> List[NormalizedCommandEntry]:
        return list(self._commands.values())

    def get_command(self, name: str) -> Optional[NormalizedCommandEntry]:
        return self._commands.get(name)
