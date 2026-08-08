from typing import List, Dict, Any, Tuple
from core.models import PluginContext
from core.logger import logger
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

        logger.debug(
            f"ParameterResolverEngine: starting resolution of {len(definitions)} parameter(s) "
            f"[correlation_id={context.correlation_id}]"
        )

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
                    logger.warning(
                        f"ParameterResolverEngine: no resolver registered for type '{definition.type}'. "
                        f"Parameter '{definition.name}' → DEFAULT ({definition.default})"
                    )
                elif not definition.required:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.UNRESOLVED_OPTIONAL
                    )
                    logger.warning(
                        f"ParameterResolverEngine: no resolver registered for type '{definition.type}'. "
                        f"Optional parameter '{definition.name}' left unresolved."
                    )
                else:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.TYPE_NOT_REGISTERED,
                        error_message=f"No parameter resolver registered for type '{definition.type}'"
                    )
                    logger.error(
                        f"ParameterResolverEngine: no resolver registered for type '{definition.type}'. "
                        f"Required parameter '{definition.name}' cannot be resolved."
                    )
                detailed_results.append(res)
                continue

            try:
                res = await resolver.resolve(context, definition)
                if res.status == ParameterResolutionStatus.RESOLVED:
                    resolved_params[definition.name] = res.value
                    logger.info(
                        f"ParameterResolverEngine: '{definition.name}' resolved via {resolver.__class__.__name__} "
                        f"→ {res.value} [status=RESOLVED, correlation_id={context.correlation_id}]"
                    )
                elif res.value is None and definition.default is not None:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=definition.default,
                        status=ParameterResolutionStatus.DEFAULT_VALUE_USED
                    )
                    resolved_params[definition.name] = definition.default
                    logger.info(
                        f"ParameterResolverEngine: '{definition.name}' not found in text. "
                        f"Using default value → {definition.default} [status=DEFAULT_VALUE_USED, correlation_id={context.correlation_id}]"
                    )
                elif res.value is not None:
                    resolved_params[definition.name] = res.value
                    logger.info(
                        f"ParameterResolverEngine: '{definition.name}' resolved "
                        f"→ {res.value} [status={res.status}, correlation_id={context.correlation_id}]"
                    )
                else:
                    logger.warning(
                        f"ParameterResolverEngine: '{definition.name}' could not be resolved and has no default. "
                        f"[status={res.status}, correlation_id={context.correlation_id}]"
                    )
            except Exception as e:
                if definition.default is not None:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=definition.default,
                        status=ParameterResolutionStatus.DEFAULT_VALUE_USED,
                        error_message=str(e)
                    )
                    resolved_params[definition.name] = definition.default
                    logger.error(
                        f"ParameterResolverEngine: exception resolving '{definition.name}' via {resolver.__class__.__name__}. "
                        f"Falling back to default → {definition.default}. Error: {e}",
                        exc_info=True
                    )
                else:
                    res = ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=None,
                        status=ParameterResolutionStatus.UNRESOLVED_REQUIRED if definition.required else ParameterResolutionStatus.UNRESOLVED_OPTIONAL,
                        error_message=str(e)
                    )
                    logger.error(
                        f"ParameterResolverEngine: exception resolving '{definition.name}' via {resolver.__class__.__name__}. "
                        f"No default available. [status={res.status}] Error: {e}",
                        exc_info=True
                    )
            detailed_results.append(res)

        logger.debug(
            f"ParameterResolverEngine: resolution complete. "
            f"resolved_params={resolved_params} [correlation_id={context.correlation_id}]"
        )
        return resolved_params, detailed_results

