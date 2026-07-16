import json
import logging
import uuid
from datetime import datetime
from pathlib import Path
from typing import List, Dict

import httpx

from core.config import settings
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.calendar_service_client import CalendarServiceClient, NextHolidayService
from core.time_formatter import TimeFormatter

logger = logging.getLogger(__name__)

SPANISH_WEEKDAYS = {
    "MONDAY": "Lunes",
    "TUESDAY": "Martes",
    "WEDNESDAY": "Miércoles",
    "THURSDAY": "Jueves",
    "FRIDAY": "Viernes",
    "SATURDAY": "Sábado",
    "SUNDAY": "Domingo"
}

SPANISH_MONTHS = [
    None, "enero", "febrero", "marzo", "abril", "mayo", "junio", 
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

SCOPE_MAPPING_VOICE = {
    "national": "nacional",
    "regional": "regional",
    "local": "local"
}

SCOPE_MAPPING_EMAIL = {
    "national": "Nacional",
    "regional": "Regional",
    "local": "Local"
}

def format_date_to_spanish(date_str: str, day_of_week: str) -> str:
    # date_str: YYYY-MM-DD
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    weekday = SPANISH_WEEKDAYS.get(day_of_week.upper(), day_of_week)
    day = dt.day
    month = SPANISH_MONTHS[dt.month]
    return f"{weekday} {day} de {month}"

def format_date_to_dmy(date_str: str) -> str:
    # date_str: YYYY-MM-DD -> DD/MM/YYYY
    parts = date_str.split("-")
    return f"{parts[2]}/{parts[1]}/{parts[0]}"


class TodayHolidayPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "TodayHolidayPlugin"

    @property
    def description(self) -> str:
        return "Determina si la fecha actual es festiva."

    @property
    def id(self) -> str:
        return "today_holiday"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Hoy es festivo?",
            "¿Es festivo hoy?",
            "Hoy hay fiesta",
            "Hoy se trabaja",
            "¿Hoy es fiesta?",
            "¿Es día festivo?",
            "Dime si hoy es festivo",
            "¿Tenemos fiesta hoy?",
            "Hoy es laboral",
            "¿Hoy descansamos?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing TodayHolidayPlugin")
        self.client = CalendarServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of TodayHolidayPlugin")
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            res = await self.client.get_holiday(today_str)
            if res.is_holiday and res.holiday:
                scope_es = SCOPE_MAPPING_VOICE.get(res.holiday.scope, res.holiday.scope)
                speech = f"{res.holiday.name}. Festivo {scope_es}."
                return PluginResult(
                    success=True,
                    speech=speech,
                    data={"is_holiday": True, "holiday": res.holiday.model_dump()}
                )
            else:
                return PluginResult(
                    success=True,
                    speech="Hoy no es festivo.",
                    data={"is_holiday": False}
                )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error to Calendar Service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error querying TodayHolidayPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido obtener la información.")


class NextHolidayPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.service = None

    @property
    def name(self) -> str:
        return "NextHolidayPlugin"

    @property
    def description(self) -> str:
        return "Informa del siguiente festivo."

    @property
    def id(self) -> str:
        return "next_holiday"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cuál es el próximo festivo?",
            "¿Cuándo es el siguiente festivo?",
            "¿Qué festivo viene ahora?",
            "¿Cuál es la próxima fiesta?",
            "Próximo festivo",
            "¿Qué día es el próximo festivo?",
            "¿Cuál será el siguiente festivo?",
            "Dime el próximo festivo",
            "¿Qué fiesta viene después?",
            "Próxima fiesta"
        ]

    def initialize(self) -> None:
        logger.info("Initializing NextHolidayPlugin")
        self.service = NextHolidayService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of NextHolidayPlugin")
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            next_h = await self.service.get_next_holiday_data(today_str)
            if not next_h:
                return PluginResult(success=False, speech="No he podido obtener la información.")
            
            date_es = format_date_to_spanish(next_h.date, next_h.day_of_week)
            scope_es = SCOPE_MAPPING_VOICE.get(next_h.scope, next_h.scope)
            human_days = TimeFormatter.humanize_days(next_h.days_until)
            speech = f"{next_h.name}. {date_es}. Festivo {scope_es}. Falta {human_days}."
            
            return PluginResult(
                success=True,
                speech=speech,
                data=next_h.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error in NextHolidayPlugin: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error querying NextHolidayPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido obtener la información.")


class DaysUntilNextHolidayPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.service = None

    @property
    def name(self) -> str:
        return "DaysUntilNextHolidayPlugin"

    @property
    def description(self) -> str:
        return "Informa únicamente del tiempo restante hasta el siguiente festivo."

    @property
    def id(self) -> str:
        return "days_until_next_holiday"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cuánto queda para el próximo festivo?",
            "¿Cuántos días faltan para el siguiente festivo?",
            "¿Cuándo descansamos otra vez?",
            "¿Cuánto falta para el próximo festivo?",
            "¿Cuántos días quedan para la próxima fiesta?",
            "Dime cuánto falta para el siguiente festivo",
            "¿Falta mucho para el próximo festivo?",
            "¿Cuándo será la próxima fiesta?",
            "¿En cuántos días es fiesta?",
            "¿Cuánto queda para descansar?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing DaysUntilNextHolidayPlugin")
        self.service = NextHolidayService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of DaysUntilNextHolidayPlugin")
        today_str = datetime.now().strftime("%Y-%m-%d")
        try:
            next_h = await self.service.get_next_holiday_data(today_str)
            if not next_h:
                return PluginResult(success=False, speech="No he podido obtener la información.")
            
            human_days = TimeFormatter.humanize_days(next_h.days_until)
            speech = f"Falta {human_days}."
            return PluginResult(
                success=True,
                speech=speech,
                data={"days_until": next_h.days_until, "date": next_h.date}
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error in DaysUntilNextHolidayPlugin: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error querying DaysUntilNextHolidayPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido obtener la información.")


class HolidaysOfYearPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "HolidaysOfYearPlugin"

    @property
    def description(self) -> str:
        return "Obtiene el listado completo de festivos del año y lo envía por correo."

    @property
    def id(self) -> str:
        return "holidays_of_year"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué festivos hay este año?",
            "Dime los festivos de este año",
            "¿Cuáles son los festivos?",
            "Muéstrame los festivos",
            "Lista de festivos",
            "¿Qué días festivos hay?",
            "¿Qué fiestas hay este año?",
            "Enséñame el calendario laboral",
            "Quiero ver los festivos",
            "¿Cuáles son los días festivos?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing HolidaysOfYearPlugin")
        self.client = CalendarServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of HolidaysOfYearPlugin")
        current_year = datetime.now().year
        try:
            res = await self.client.get_year_holidays(current_year)
            holidays = res.holidays
            n = len(holidays)
            
            # Generate HTML content for the email
            html_rows = ""
            for h in holidays:
                dmy_date = format_date_to_dmy(h.date)
                day_es = SPANISH_WEEKDAYS.get(h.day_of_week.upper(), h.day_of_week)
                scope_es = SCOPE_MAPPING_EMAIL.get(h.scope, h.scope.capitalize())
                html_rows += f"""
                <tr>
                    <td style="padding: 10px; border-bottom: 1px solid #E2E8F0;">{dmy_date}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #E2E8F0;">{day_es}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #E2E8F0; font-weight: bold;">{h.name}</td>
                    <td style="padding: 10px; border-bottom: 1px solid #E2E8F0;">{scope_es}</td>
                </tr>
                """
                
            html_body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #F7FAFC; padding: 20px; color: #2D3748;">
                <div style="max-width: 600px; margin: 0 auto; background-color: #FFFFFF; border-radius: 8px; box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1); padding: 30px; border-top: 5px solid #3182CE;">
                    <h2 style="color: #2B6CB0; margin-top: 0;">Calendario Oficial de Festivos {current_year}</h2>
                    <p style="font-size: 16px;">Lista ordenada cronológicamente de los días no laborables oficiales cargados en el sistema.</p>
                    <table style="width: 100%; border-collapse: collapse; margin-top: 20px; margin-bottom: 20px; text-align: left;">
                        <thead>
                            <tr style="background-color: #EBF8FF; color: #2B6CB0;">
                                <th style="padding: 10px; border-bottom: 2px solid #BEE3F8;">Fecha</th>
                                <th style="padding: 10px; border-bottom: 2px solid #BEE3F8;">Día</th>
                                <th style="padding: 10px; border-bottom: 2px solid #BEE3F8;">Festivo</th>
                                <th style="padding: 10px; border-bottom: 2px solid #BEE3F8;">Ámbito</th>
                            </tr>
                        </thead>
                        <tbody>
                            {html_rows}
                        </tbody>
                    </table>
                    <p style="font-size: 14px; font-weight: bold; border-top: 1px solid #E2E8F0; padding-top: 15px; margin-bottom: 0;">Total de festivos registrados: {n}</p>
                </div>
            </body>
            </html>
            """
            
            mail_uuid = uuid.uuid4().hex[:8]
            mail_id = f"mail-{mail_uuid}"
            
            # According to ADR-009, the "to" field is not included
            email_payload = {
                "id": mail_id,
                "subject": f"Festivos de {current_year}",
                "body": html_body,
                "content_type": "text/html"
            }
            
            pending_dir = Path(settings.mail_pending_dir)
            file_path = pending_dir / f"{mail_id}.json"
            
            pending_dir.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(email_payload, f, indent=2, ensure_ascii=False)
                
            logger.info(f"Generated mail artifact under: {file_path}")
            
            # Response aligned with TONE_GUIDE.md
            speech = f"{n} festivos. Lista enviada por correo."
            
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "num_holidays": n,
                    "mail_id": mail_id,
                    "file_path": str(file_path)
                }
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error in HolidaysOfYearPlugin: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error querying HolidaysOfYearPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido obtener la información.")
