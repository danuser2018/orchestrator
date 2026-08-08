from typing import List, Dict, Any, Tuple
from core.models import PluginContext
from .models import ParameterDefinition, ParameterResolutionResult, ParameterResolutionStatus
from .registry import ParameterResolverRegistry

class ParameterResolverEngine:
    def __init__(self, registry: ParameterResolverRegistry):
        self.registry = registry

    async def resolve_parameters(
        self, 
        context: PluginContext, 
        definitions: List[ParameterDefinition]
    ) -> Tuple[Dict[str, Any], List[ParameterResolutionResult]]:
        resolved_params: Dict[str, Any] = {}
        detailed_results: List[ParameterResolutionResult] = []

        for definition in definitions:
            resolver = self.registry.get(definition.type)
            if not resolver:
                if definition.default is not None:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=definition.default,
                        status=ParameterResolutionStatus.DEFAULT_VALUE_USED
                    )
                    resolved_params[definition.name] = definition.default
                elif not definition.required:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                    )
                else:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.TYPE_NOT_REGISTERED,
                        error_message=f"No parameter resolver registered for type '{definition.type}'"
                    )
                detailed_results.append(res)
                continue

            try:
                res = await resolver.resolve(context, definition)
                if res.status == ParameterResolutionStatus.RESOLVED:
                    resolved_params[definition.name] = res.value
                elif res.value is None and definition.default is not None:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=definition.default,
                        status=ParameterResolutionStatus.DEFAULT_VALUE_USED
                    )
                    resolved_params[definition.name] = definition.default
                elif res.value is not None:
                    resolved_params[definition.name] = res.value
            except Exception as e:
                if definition.default is not None:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=definition.default,
                        status=ParameterResolutionStatus.DEFAULT_VALUE_USED,
                        error_message=str(e)
                    )
                    resolved_params[definition.name] = definition.default
                else:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.UNRESOLVED_REQUIRED if definition.required else ParameterResolutionStatus.UNRESOLVED_OPTIONAL,
                        error_message=str(e)
                    )
            detailed_results.append(res)

        return resolved_params, detailed_results
