import pytest
from core.parameter_resolution.models import (
    ParameterDefinition,
    ParameterResolutionStatus,
    ParameterResolutionResult,
)

def test_parameter_definition_defaults():
    param = ParameterDefinition(name="max", type="Integer")
    assert param.name == "max"
    assert param.type == "Integer"
    assert param.required is False
    assert param.default is None

def test_parameter_definition_with_values():
    param = ParameterDefinition(
        name="max",
        type="Integer",
        required=True,
        default=100
    )
    assert param.name == "max"
    assert param.type == "Integer"
    assert param.required is True
    assert param.default == 100

def test_parameter_resolution_status_enum():
    assert ParameterResolutionStatus.RESOLVED == "RESOLVED"
    assert ParameterResolutionStatus.UNRESOLVED_OPTIONAL == "UNRESOLVED_OPTIONAL"
    assert ParameterResolutionStatus.DEFAULT_VALUE_USED == "DEFAULT_VALUE_USED"
    assert ParameterResolutionStatus.UNRESOLVED_REQUIRED == "UNRESOLVED_REQUIRED"
    assert ParameterResolutionStatus.TYPE_NOT_REGISTERED == "TYPE_NOT_REGISTERED"

def test_parameter_resolution_result():
    res = ParameterResolutionResult(
        parameter_name="max",
        value=50,
        status=ParameterResolutionStatus.RESOLVED
    )
    assert res.parameter_name == "max"
    assert res.value == 50
    assert res.status == ParameterResolutionStatus.RESOLVED
    assert res.error_message is None
