import json
import os
import shutil
import tempfile
from datetime import datetime
from unittest.mock import patch, AsyncMock

import httpx
import pytest

from core.models import PluginContext
from core.time_formatter import TimeFormatter
from core.calendar_service_client import (
    HolidayInfo,
    HolidayDateResponse,
    HolidayYearResponse,
    NextHolidayResponse,
    CalendarServiceClient,
    NextHolidayService,
)
from plugins.holidays.main import (
    TodayHolidayPlugin,
    NextHolidayPlugin,
    DaysUntilNextHolidayPlugin,
    HolidaysOfYearPlugin,
    format_date_to_spanish,
    format_date_to_dmy,
)


class MockDatetime(datetime):
    @classmethod
    def now(cls, tz=None):
        return datetime(2026, 7, 16)


# --- 1. Test TimeFormatter ---

def test_time_formatter_humanize_days():
    # Exact mappings
    assert TimeFormatter.humanize_days(0) == "hoy"
    assert TimeFormatter.humanize_days(1) == "mañana"
    assert TimeFormatter.humanize_days(2) == "pasado mañana"
    assert TimeFormatter.humanize_days(5) == "cinco días"
    assert TimeFormatter.humanize_days(7) == "una semana"
    assert TimeFormatter.humanize_days(14) == "dos semanas"
    assert TimeFormatter.humanize_days(21) == "tres semanas"
    assert TimeFormatter.humanize_days(30) == "un mes"
    assert TimeFormatter.humanize_days(45) == "un mes y medio"
    assert TimeFormatter.humanize_days(60) == "dos meses"
    assert TimeFormatter.humanize_days(88) == "casi tres meses"
    assert TimeFormatter.humanize_days(365) == "un año"

    # Intermediate mappings
    assert TimeFormatter.humanize_days(3) == "tres días"
    assert TimeFormatter.humanize_days(4) == "cuatro días"
    assert TimeFormatter.humanize_days(6) == "seis días"
    assert TimeFormatter.humanize_days(10) == "una semana"
    assert TimeFormatter.humanize_days(12) == "una semana"
    assert TimeFormatter.humanize_days(18) == "dos semanas"
    assert TimeFormatter.humanize_days(25) == "tres semanas"
    assert TimeFormatter.humanize_days(35) == "un mes"
    assert TimeFormatter.humanize_days(50) == "un mes y medio"
    assert TimeFormatter.humanize_days(85) == "casi tres meses"
    assert TimeFormatter.humanize_days(120) == "cuatro meses"
    assert TimeFormatter.humanize_days(180) == "medio año"
    assert TimeFormatter.humanize_days(730) == "2 años"

    # Negative value validation
    with pytest.raises(ValueError, match="Days cannot be negative"):
        TimeFormatter.humanize_days(-1)


# --- 2. Test Helpers ---

def test_format_date_to_spanish():
    assert format_date_to_spanish("2026-10-12", "MONDAY") == "Lunes 12 de octubre"
    assert format_date_to_spanish("2026-07-23", "THURSDAY") == "Jueves 23 de julio"


def test_format_date_to_dmy():
    assert format_date_to_dmy("2026-10-12") == "12/10/2026"


# --- 3. Test TodayHolidayPlugin ---

@pytest.fixture
def today_plugin():
    plugin = TodayHolidayPlugin()
    plugin.initialize()
    return plugin


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_today_holiday_plugin_is_holiday(today_plugin):
    mock_response = HolidayDateResponse(
        isHoliday=True,
        holiday=HolidayInfo(
            date="2026-07-16",
            dayOfWeek="THURSDAY",
            name="Fiesta de la Virgen del Carmen",
            scope="local",
        ),
    )
    with patch.object(today_plugin.client, "get_holiday", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        context = PluginContext(raw_text="¿Hoy es festivo?", normalized_text="hoy es festivo")
        result = await today_plugin.execute(context)

        assert result.success is True
        assert result.speech == "Fiesta de la Virgen del Carmen. Festivo local."
        assert result.data == {
            "is_holiday": True,
            "holiday": {
                "date": "2026-07-16",
                "day_of_week": "THURSDAY",
                "name": "Fiesta de la Virgen del Carmen",
                "scope": "local",
            },
        }


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_today_holiday_plugin_not_holiday(today_plugin):
    mock_response = HolidayDateResponse(isHoliday=False)
    with patch.object(today_plugin.client, "get_holiday", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        context = PluginContext(raw_text="¿Hoy es festivo?", normalized_text="hoy es festivo")
        result = await today_plugin.execute(context)

        assert result.success is True
        assert result.speech == "Hoy no es festivo."
        assert result.data == {"is_holiday": False}


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_today_holiday_plugin_connection_error(today_plugin):
    with patch.object(today_plugin.client, "get_holiday", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Hoy es festivo?", normalized_text="hoy es festivo")
        result = await today_plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_today_holiday_plugin_http_error(today_plugin):
    with patch.object(today_plugin.client, "get_holiday", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.HTTPStatusError("500 Error", request=None, response=None)
        context = PluginContext(raw_text="¿Hoy es festivo?", normalized_text="hoy es festivo")
        result = await today_plugin.execute(context)

        assert result.success is False
        assert result.speech == "No he podido obtener la información."


# --- 4. Test NextHolidayPlugin ---

@pytest.fixture
def next_plugin():
    plugin = NextHolidayPlugin()
    plugin.initialize()
    return plugin


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_next_holiday_plugin_success(next_plugin):
    mock_response = NextHolidayResponse(
        date="2026-10-12",
        dayOfWeek="MONDAY",
        name="Fiesta Nacional de España",
        scope="national",
        daysUntil=88,
    )
    with patch.object(next_plugin.service, "get_next_holiday_data", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        context = PluginContext(raw_text="¿Cuál es el próximo festivo?", normalized_text="cual es el proximo festivo")
        result = await next_plugin.execute(context)

        assert result.success is True
        assert result.speech == "Fiesta Nacional de España. Lunes 12 de octubre. Festivo nacional. Falta casi tres meses."
        assert result.data == {
            "date": "2026-10-12",
            "day_of_week": "MONDAY",
            "name": "Fiesta Nacional de España",
            "scope": "national",
            "days_until": 88,
        }


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_next_holiday_plugin_not_found(next_plugin):
    with patch.object(next_plugin.service, "get_next_holiday_data", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        context = PluginContext(raw_text="¿Cuál es el próximo festivo?", normalized_text="cual es el proximo festivo")
        result = await next_plugin.execute(context)

        assert result.success is False
        assert result.speech == "No he podido obtener la información."


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_next_holiday_plugin_connection_error(next_plugin):
    with patch.object(next_plugin.service, "get_next_holiday_data", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Cuál es el próximo festivo?", normalized_text="cual es el proximo festivo")
        result = await next_plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."


# --- 5. Test DaysUntilNextHolidayPlugin ---

@pytest.fixture
def days_until_plugin():
    plugin = DaysUntilNextHolidayPlugin()
    plugin.initialize()
    return plugin


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_days_until_next_holiday_plugin_success(days_until_plugin):
    mock_response = NextHolidayResponse(
        date="2026-07-23",
        dayOfWeek="THURSDAY",
        name="Santiago Apóstol",
        scope="regional",
        daysUntil=7,
    )
    with patch.object(days_until_plugin.service, "get_next_holiday_data", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        context = PluginContext(raw_text="¿Cuánto falta?", normalized_text="cuanto falta")
        result = await days_until_plugin.execute(context)

        assert result.success is True
        assert result.speech == "Falta una semana."
        assert result.data == {"days_until": 7, "date": "2026-07-23"}


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_days_until_next_holiday_plugin_connection_error(days_until_plugin):
    with patch.object(days_until_plugin.service, "get_next_holiday_data", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Cuánto falta?", normalized_text="cuanto falta")
        result = await days_until_plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."


# --- 6. Test HolidaysOfYearPlugin ---

@pytest.fixture
def year_plugin():
    plugin = HolidaysOfYearPlugin()
    plugin.initialize()
    return plugin


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_holidays_of_year_plugin_success(year_plugin):
    # Setup temporary directory for pending emails
    temp_dir = tempfile.mkdtemp()
    
    mock_response = HolidayYearResponse(
        year=2026,
        holidays=[
            HolidayInfo(date="2026-01-01", dayOfWeek="THURSDAY", name="Año Nuevo", scope="national"),
            HolidayInfo(date="2026-01-06", dayOfWeek="TUESDAY", name="Epifanía del Señor", scope="national"),
            HolidayInfo(date="2026-03-20", dayOfWeek="FRIDAY", name="San José", scope="regional"),
            HolidayInfo(date="2026-05-01", dayOfWeek="FRIDAY", name="Fiesta del Trabajo", scope="national"),
            HolidayInfo(date="2026-07-16", dayOfWeek="THURSDAY", name="Virgen del Carmen", scope="local"),
        ],
    )

    with patch("plugins.holidays.main.settings") as mock_settings:
        mock_settings.mail_pending_dir = temp_dir
        
        with patch.object(year_plugin.client, "get_year_holidays", new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_response
            context = PluginContext(raw_text="¿Qué festivos hay este año?", normalized_text="que festivos hay este año")
            result = await year_plugin.execute(context)

            assert result.success is True
            assert result.speech == "5 festivos. Lista enviada por correo."
            assert result.data["num_holidays"] == 5
            
            # Verify the written email JSON
            mail_id = result.data["mail_id"]
            file_path = result.data["file_path"]
            assert os.path.exists(file_path)
            
            with open(file_path, "r", encoding="utf-8") as f:
                email_payload = json.load(f)
                
            assert email_payload["id"] == mail_id
            assert email_payload["subject"] == "Festivos de 2026"
            assert email_payload["content_type"] == "text/html"
            assert "to" not in email_payload
            assert "Año Nuevo" in email_payload["body"]
            assert "Epifanía del Señor" in email_payload["body"]
            assert "San José" in email_payload["body"]
            assert "Fiesta del Trabajo" in email_payload["body"]
            assert "Virgen del Carmen" in email_payload["body"]

    # Clean up temp dir
    shutil.rmtree(temp_dir)


@pytest.mark.asyncio
@patch("plugins.holidays.main.datetime", MockDatetime)
async def test_holidays_of_year_plugin_connection_error(year_plugin):
    with patch.object(year_plugin.client, "get_year_holidays", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.ConnectError("Connection refused")
        context = PluginContext(raw_text="¿Qué festivos hay este año?", normalized_text="que festivos hay este año")
        result = await year_plugin.execute(context)

        assert result.success is False
        assert result.speech == "Servicio no disponible."
