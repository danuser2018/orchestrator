from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, List
from nova_event_bus import Event, event


@event("event.interaction.response-generated")
@dataclass
class ResponseGeneratedEvent(Event):
    response: str
    plugin: str
    confidence: float
    timestamp: datetime
    correlation_id: str
    execution_time_ms: int
    channel: str
    metadata: Dict[str, Any]


@dataclass
class PublicCommandEntry:
    name: str
    risk: str
    phrases: List[str]


@event("event.host.commands.available")
@dataclass
class HostCommandsAvailableEvent(Event):
    version: int
    commands: List[PublicCommandEntry]
