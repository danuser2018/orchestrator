import time
from fastapi import APIRouter, Request
from .models import UserRequest, AssistantResponse, PluginResult, HealthResponse, ExecutionPlan
from .engine import ExecutionPlanner, PlanExecutor, PluginNotFoundError
from .logger import logger

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def health_check():
    return {"status": "ok"}

@router.post("/resolve", response_model=ExecutionPlan)
async def resolve_intent(request: Request, user_request: UserRequest):
    planner: ExecutionPlanner = request.app.state.planner
    plan = await planner.resolve(user_request)
    return plan

@router.post("/execute-plan", response_model=AssistantResponse)
async def execute_plan(request: Request, plan: ExecutionPlan):
    executor: PlanExecutor = request.app.state.executor
    response = await executor.execute_plan(plan)
    return response
