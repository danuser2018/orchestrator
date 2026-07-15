import time
from fastapi import APIRouter, Request
from .models import UserRequest, AssistantResponse, PluginResult, HealthResponse, ExecutionPlan
from .engine import IntentResolver, PluginExecutor, PluginNotFoundError
from .logger import logger

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}

@router.post("/resolve", response_model=ExecutionPlan)
async def resolve_intent(request: Request, user_request: UserRequest):
    resolver: IntentResolver = request.app.state.resolver
    plan = await resolver.resolve(user_request)
    return plan

@router.post("/execute-plan", response_model=AssistantResponse)
async def execute_plan(request: Request, plan: ExecutionPlan):
    executor: PluginExecutor = request.app.state.executor
    response = await executor.execute_plan(plan)
    return response

@router.post("/execute", response_model=AssistantResponse)
async def execute_request(request: Request, user_request: UserRequest):
    start_time = time.time()
    resolver: IntentResolver = request.app.state.resolver
    executor: PluginExecutor = request.app.state.executor
    
    try:
        plan = await resolver.resolve(user_request)
        response = await executor.execute_plan(plan)
        # Recalculate execution time to represent the entire pipeline time including resolution
        execution_time = int((time.time() - start_time) * 1000)
        response.execution_time_ms = execution_time
        return response
    except PluginNotFoundError:
        raise
    except Exception as e:
        logger.error(f"Uncaught exception during execution: {e}", exc_info=True)
        execution_time = int((time.time() - start_time) * 1000)
        return AssistantResponse(
            success=False,
            plugin_used="Error",
            speech="Ha ocurrido un error interno al ejecutar la acción.",
            execution_time_ms=execution_time
        )
