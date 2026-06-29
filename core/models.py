from pydantic import BaseModel
from typing import Dict, Any, Optional

class HealthResponse(BaseModel):
    status: str

class UserRequest(BaseModel):
    text: str
    timestamp: Optional[float] = None

class PluginContext(BaseModel):
    raw_text: str
    normalized_text: str
    metadata: Dict[str, Any] = {}

class PluginResult(BaseModel):
    success: bool
    speech: str
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class AssistantResponse(BaseModel):
    success: bool
    plugin_used: str
    speech: str
    execution_time_ms: int
