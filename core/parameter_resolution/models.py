from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel

class ParameterResolutionStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED_OPTIONAL = "UNRESOLVED_OPTIONAL"
    DEFAULT_VALUE_USED = "DEFAULT_VALUE_USED"
    UNRESOLVED_REQUIRED = "UNRESOLVED_REQUIRED"
    TYPE_NOT_REGISTERED = "TYPE_NOT_REGISTERED"

class ParameterDefinition(BaseModel):
    name: str
    type: str
    required: bool = False
    default: Optional[Any] = None

class ParameterResolutionResult(BaseModel):
    parameter_name: str
    value: Optional[Any] = None
    status: ParameterResolutionStatus
    error_message: Optional[str] = None
