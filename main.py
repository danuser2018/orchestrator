from contextlib import asynccontextmanager
from fastapi import FastAPI
from core.api import router as api_router
from core.plugin_manager import PluginManager
from core.engine import Router
from core.logger import logger
from core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Orchestrator...")
    plugin_manager = PluginManager()
    plugin_manager.discover_and_load()
    app.state.plugin_manager = plugin_manager
    app.state.engine = Router(plugin_manager)
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

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=settings.host, port=settings.port, reload=True)
