import httpx
import logging
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict

logger = logging.getLogger(__name__)

class HolidayInfo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: str
    day_of_week: str = Field(..., alias="dayOfWeek")
    name: str
    scope: str

class HolidayDateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    is_holiday: bool = Field(..., alias="isHoliday")
    holiday: Optional[HolidayInfo] = None

class HolidayYearResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    year: int
    holidays: List[HolidayInfo]

class NextHolidayResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    date: str
    day_of_week: str = Field(..., alias="dayOfWeek")
    name: str
    scope: str
    days_until: int = Field(..., alias="daysUntil")

class CalendarServiceClient:
    def __init__(self, base_url: str = None):
        from core.config import settings
        self.base_url = base_url or settings.calendar_service_base_url

    async def get_holiday(self, query_date: str) -> HolidayDateResponse:
        url = f"{self.base_url.rstrip('/')}/api/v1/holidays?date={query_date}"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return HolidayDateResponse.model_validate(response.json())

    async def get_next_holiday(self, from_date: str) -> NextHolidayResponse:
        url = f"{self.base_url.rstrip('/')}/api/v1/holidays/next?from={from_date}"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return NextHolidayResponse.model_validate(response.json())

    async def get_year_holidays(self, year: int) -> HolidayYearResponse:
        url = f"{self.base_url.rstrip('/')}/api/v1/holidays?year={year}"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return HolidayYearResponse.model_validate(response.json())


class NextHolidayService:
    def __init__(self, client: Optional[CalendarServiceClient] = None):
        self.client = client or CalendarServiceClient()

    async def get_next_holiday_data(self, from_date: str) -> Optional[NextHolidayResponse]:
        try:
            return await self.client.get_next_holiday(from_date)
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error or timeout connecting to Calendar Service: {conn_err}")
            raise conn_err
        except httpx.HTTPStatusError as status_err:
            logger.error(f"HTTP error status from Calendar Service: {status_err}")
            raise status_err
        except Exception as e:
            logger.error(f"Unexpected error in NextHolidayService: {e}", exc_info=True)
            raise e
