import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.api import router as api_router
from core.plugin_manager import PluginManager
from core.engine import ExecutionPlanner, PlanExecutor, PluginNotFoundError
from core.similarity import RapidFuzzSimilarityEngine
from core.logger import logger
from core.config import settings
from core.system_service_client import SystemServiceClient

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Orchestrator...")
    plugin_manager = PluginManager()
    plugin_manager.discover_and_load()
    app.state.plugin_manager = plugin_manager
    
    # Initialize and connect Event Bus
    from nova_event_bus import NatsEventBus
    event_bus = NatsEventBus()
    try:
        await event_bus.connect()
        logger.info("Successfully connected to Event Bus.")
    except Exception as exc:
        logger.error(f"Failed to connect to Event Bus during startup: {exc}", exc_info=True)
    
    app.state.event_bus = event_bus
    
    from core.parameter_resolution import ParameterResolverRegistry, ParameterResolverEngine
    parameter_registry = ParameterResolverRegistry()
    parameter_engine = ParameterResolverEngine(parameter_registry)
    app.state.parameter_registry = parameter_registry
    app.state.parameter_engine = parameter_engine
    
    similarity_engine = RapidFuzzSimilarityEngine()
    app.state.planner = ExecutionPlanner(plugin_manager, similarity_engine, parameter_engine=parameter_engine)
    app.state.executor = PlanExecutor(plugin_manager, event_bus=event_bus)

    
    # Publish capabilities to System Service
    plugins = plugin_manager.get_active_plugins()
    num_plugins = len(plugins)
    
    capabilities = []
    for plugin in plugins:
        if plugin.id == "fallback":
            continue
            
        capabilities.append({
            "id": plugin.id,
            "description": plugin.description
        })
        
    client = SystemServiceClient()
    url = f"{client.base_url.rstrip('/')}/v1/system/capabilities"
    logger.info(f"Discovered {num_plugins} plugins. Registering {len(capabilities)} capabilities to System Service using URL: {url}")
    
    try:
        await client.register_capabilities(capabilities)
        logger.info(f"Published {len(capabilities)} capabilities to System Service.")
    except httpx.TimeoutException as timeout_err:
        logger.warning(f"Timeout error publishing capabilities to System Service: {timeout_err}")
    except httpx.HTTPError as http_err:
        logger.warning(f"HTTP error publishing capabilities to System Service: {http_err}")
    except Exception as exc:
        logger.error(f"Unexpected error publishing capabilities to System Service: {exc}", exc_info=True)
        
    logger.info("Orchestrator initialized and ready.")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestrator...")
    try:
        await event_bus.disconnect()
        logger.info("Successfully disconnected from Event Bus.")
    except Exception as exc:
        logger.error(f"Error disconnecting from Event Bus during shutdown: {exc}", exc_info=True)
        
    plugin_manager.teardown()

app = FastAPI(
    title=settings.app_name,
    description="Local Voice Assistant Orchestrator",
    version="1.0.0",
    lifespan=lifespan
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc: RequestValidationError):
    errors = exc.errors()
    message = "El campo 'text' es obligatorio y no puede estar vacío." if any(err.get("loc") == ("body", "text") for err in errors) else str(exc)
    return JSONResponse(
        status_code=422,
        content={
            "error": "ValidationError",
            "message": message,
            "status": 422
        }
    )

@app.exception_handler(PluginNotFoundError)
async def plugin_not_found_exception_handler(request, exc: PluginNotFoundError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "PluginNotFoundError",
            "message": str(exc),
            "status": 400
        }
    )

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
