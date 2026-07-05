import httpx
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WeatherInfo(BaseModel):
    temperature: float
    precipitation_probability: int

class WeatherServiceClient:
    def __init__(self, base_url: str = None):
        from core.config import settings
        self.base_url = base_url or settings.weather_service_base_url

    async def get_current_weather(self) -> WeatherInfo:
        url = f"{self.base_url.rstrip('/')}/v1/weather/current"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return WeatherInfo(**data)
