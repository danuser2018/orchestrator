import httpx
import logging
from pydantic import BaseModel
from .config import settings

logger = logging.getLogger(__name__)

class SystemInfo(BaseModel):
    name: str
    author: str
    version: str
    description: str

class SystemServiceClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.system_service_base_url

    async def get_system_info(self) -> SystemInfo:
        url = f"{self.base_url.rstrip('/')}/system/info"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return SystemInfo(**data)
