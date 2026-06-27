import httpx
import logging
from typing import List
from pydantic import BaseModel
from core.config import settings

logger = logging.getLogger(__name__)

class SystemInfo(BaseModel):
    name: str
    author: str
    version: str
    description: str

class Capability(BaseModel):
    id: str
    description: str

class CapabilityList(BaseModel):
    capabilities: List[Capability]

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

    async def register_capabilities(self, capabilities: List[dict]) -> bool:
        url = f"{self.base_url.rstrip('/')}/system/capabilities"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"capabilities": capabilities})
            response.raise_for_status()
            logger.info("Capabilities registration call successful.")
            return True

    async def get_capabilities(self) -> CapabilityList:
        url = f"{self.base_url.rstrip('/')}/system/capabilities"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return CapabilityList(**data)
