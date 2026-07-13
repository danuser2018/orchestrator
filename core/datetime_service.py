import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SPANISH_WEEKDAYS = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
]

SPANISH_MONTHS = [
    None, "enero", "febrero", "marzo", "abril", "mayo", "junio", 
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

class DateTimeService:
    def get_current_time(self) -> str:
        """
        Retrieves system time and formats it as HH:MM.
        """
        try:
            now = datetime.now()
            return now.strftime("%H:%M")
        except Exception as e:
            logger.error(f"Failed to retrieve system time: {e}", exc_info=True)
            raise e

    def get_current_date(self) -> str:
        """
        Retrieves system date and formats it as 'Hoy es {day_of_week}, {day} de {month} de {year}.'
        """
        try:
            now = datetime.now()
            day_of_week = SPANISH_WEEKDAYS[now.weekday()]
            day = now.day
            month = SPANISH_MONTHS[now.month]
            year = now.year
            return f"Hoy es {day_of_week}, {day} de {month} de {year}."
        except Exception as e:
            logger.error(f"Failed to retrieve system date: {e}", exc_info=True)
            raise e
