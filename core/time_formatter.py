class TimeFormatter:
    @staticmethod
    def humanize_days(days: int) -> str:
        if days < 0:
            raise ValueError("Days cannot be negative")
            
        exact_mappings = {
            0: "hoy",
            1: "mañana",
            2: "pasado mañana",
            5: "cinco días",
            7: "una semana",
            14: "dos semanas",
            21: "tres semanas",
            30: "un mes",
            45: "un mes y medio",
            60: "dos meses",
            88: "casi tres meses",
            365: "un año"
        }
        if days in exact_mappings:
            return exact_mappings[days]
            
        if days < 7:
            words = {3: "tres", 4: "cuatro", 6: "seis"}
            return f"{words.get(days, str(days))} días"
        elif days < 14:
            return "una semana"
        elif days < 21:
            return "dos semanas"
        elif days < 30:
            return "tres semanas"
        elif days < 45:
            return "un mes"
        elif days < 60:
            return "un mes y medio"
        elif days < 90:
            if days >= 80:
                return "casi tres meses"
            return "dos meses"
        elif days < 365:
            months = int(round(days / 30.0))
            if months == 12:
                return "un año"
            month_words = {
                1: "un mes", 2: "dos meses", 3: "tres meses", 4: "cuatro meses",
                5: "cinco meses", 6: "medio año", 7: "siete meses", 8: "ocho meses",
                9: "nueve meses", 10: "diez meses", 11: "once meses"
            }
            return month_words.get(months, f"{months} meses")
        else:
            years = int(round(days / 365.0))
            if years == 1:
                return "un año"
            return f"{years} años"
