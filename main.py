import httpx
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from core.api import router as api_router
from core.plugin_manager import PluginManager
from core.engine import IntentResolver, PluginExecutor, PluginNotFoundError
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
    
    similarity_engine = RapidFuzzSimilarityEngine()
    app.state.resolver = IntentResolver(plugin_manager, similarity_engine)
    app.state.executor = PluginExecutor(plugin_manager)

    
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
