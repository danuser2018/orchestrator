import httpx
import logging
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class AudioState(BaseModel):
    volume: int = Field(..., ge=0, le=100)
    muted: bool

class HostServiceClient:
    def __init__(self, base_url: str = None):
        from core.config import settings
        self.base_url = base_url or settings.host_service_base_url

    async def get_volume(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def volume_up(self, step: int) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume/up"
        logger.info(f"Consuming URL: {url} with step: {step}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"step": step})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def volume_down(self, step: int) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume/down"
        logger.info(f"Consuming URL: {url} with step: {step}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"step": step})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def mute(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/mute"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def unmute(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/unmute"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def set_volume(self, volume: int) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume/set"
        logger.info(f"Consuming URL: {url} with volume: {volume}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"volume": volume})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

