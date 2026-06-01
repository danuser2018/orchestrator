import time
from fastapi import APIRouter, Request
from .models import UserRequest, AssistantResponse, PluginResult
from .engine import Router
from .logger import logger

router = APIRouter()

@router.post("/execute", response_model=AssistantResponse)
async def execute_request(request: Request, user_request: UserRequest):
    start_time = time.time()
    
    engine: Router = request.app.state.engine
    
    try:
        plugin, context = await engine.route_request(user_request)
        
        if not plugin:
            execution_time = int((time.time() - start_time) * 1000)
            return AssistantResponse(
                success=False,
                plugin_used="None",
                speech="Lo siento, ha ocurrido un error interno y no hay plugin de respaldo.",
                execution_time_ms=execution_time
            )
            
        result: PluginResult = await plugin.execute(context)
        execution_time = int((time.time() - start_time) * 1000)
        
        return AssistantResponse(
            success=result.success,
            plugin_used=plugin.name,
            speech=result.speech,
            execution_time_ms=execution_time
        )
        
    except Exception as e:
        logger.error(f"Uncaught exception during execution: {e}", exc_info=True)
        execution_time = int((time.time() - start_time) * 1000)
        return AssistantResponse(
            success=False,
            plugin_used="Error",
            speech="Ha ocurrido un error interno al ejecutar la acción.",
            execution_time_ms=execution_time
        )
