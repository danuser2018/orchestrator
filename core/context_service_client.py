import httpx
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LastResponseInfo(BaseModel):
    response: str
    plugin: str
    timestamp: str

class ContextServiceClient:
    def __init__(self, base_url: Optional[str] = None):
        from core.config import settings
        self.base_url = base_url or settings.context_service_base_url

    async def get_last_response(self) -> Optional[LastResponseInfo]:
        url = f"{self.base_url.rstrip('/')}/v1/context/last-response"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                logger.info("No context available on context-service.")
                return None
            response.raise_for_status()
            data = response.json()
            logger.info(f"Context response received: {data}")
            return LastResponseInfo(**data)
