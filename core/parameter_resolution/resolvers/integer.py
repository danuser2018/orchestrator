import re
from typing import Optional
from core.models import PluginContext
from core.logger import logger
from core.parameter_resolution.base import BaseParameterResolver
from core.parameter_resolution.models import (
    ParameterDefinition,
    ParameterResolutionResult,
    ParameterResolutionStatus,
)

SPANISH_CARDINALS = {
    "cero": 0, "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
    "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16, "dieciseis": 16,
    "diecisiete": 17, "dieciocho": 18, "diecinueve": 19, "veinte": 20,
    "veintiuno": 21, "veintiún": 21, "veintiun": 21, "veintidós": 22, "veintidos": 22,
    "veintitrés": 23, "veintitres": 23, "veinticuatro": 24, "veinticinco": 25,
    "veintiséis": 26, "veintiseis": 26, "veintisiete": 27, "veintiocho": 28, "veintinueve": 29,
    "treinta": 30, "cuarenta": 40, "cincuenta": 50, "sesenta": 60, "setenta": 70,
    "ochenta": 80, "noventa": 90, "cien": 100, "doscientos": 200,
    "trescientos": 300, "cuatrocientos": 400, "quinientos": 500, "seiscientos": 600,
    "setecientos": 700, "ochocientos": 800, "novecientos": 900, "mil": 1000
}

SPANISH_HUNDREDS = {
    "cien": 100, "ciento": 100, "doscientos": 200, "trescientos": 300, "cuatrocientos": 400,
    "quinientos": 500, "seiscientos": 600, "setecientos": 700, "ochocientos": 800, "novecientos": 900
}

ARTICLE_FILLER_NOUNS = {
    "numero", "numeros", "valor", "valores", "cifra", "cifras", "opcion", "opciones", "resultado", "resultados"
}

class IntegerResolver(BaseParameterResolver):
    @property
    def target_type(self) -> str:
        return "Integer"

    async def resolve(
        self, 
        context: PluginContext, 
        definition: ParameterDefinition
    ) -> ParameterResolutionResult:
        text = context.normalized_text.lower()
        
        # 1. Search for digit patterns (e.g. "50", "100")
        digit_match = re.search(r'\b\d+\b', text)
        if digit_match:
            val = int(digit_match.group())
            logger.debug(
                f"IntegerResolver: digit match found for '{definition.name}' "
                f"→ {val} (pattern '{digit_match.group()}' in '{text}')"
            )
            return ParameterResolutionResult(
                parameter_name=definition.name,
                value=val,
                status=ParameterResolutionStatus.RESOLVED
            )

        # 2. Search for written Spanish cardinal numbers
        words = text.split()
        num_words = len(words)
        
        for i, word in enumerate(words):
            clean_word = re.sub(r'[^\w]', '', word)
            
            # Check if "un" or "una" is acting as an article before filler nouns (e.g., "un número")
            if clean_word in ("un", "una") and i + 1 < num_words:
                next_word_clean = re.sub(r'[^\w]', '', words[i + 1])
                if next_word_clean in ARTICLE_FILLER_NOUNS:
                    continue

            # Check multiplier with "mil" (e.g., "dos mil")
            if clean_word in SPANISH_CARDINALS and clean_word != "mil" and i + 1 < num_words:
                next_word_clean = re.sub(r'[^\w]', '', words[i + 1])
                if next_word_clean == "mil":
                    val = SPANISH_CARDINALS[clean_word] * 1000
                    logger.debug(
                        f"IntegerResolver: thousands compound match for '{definition.name}' "
                        f"→ {val} ('{clean_word} mil' in '{text}')"
                    )
                    return ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=val,
                        status=ParameterResolutionStatus.RESOLVED
                    )

            # Check compound hundreds (e.g. "ciento veinte", "ciento treinta y cinco")
            if clean_word in SPANISH_HUNDREDS and i + 1 < num_words:
                hundreds_val = SPANISH_HUNDREDS[clean_word]
                next_word_clean = re.sub(r'[^\w]', '', words[i + 1])
                
                # Hundreds + tens + 'y' + units
                if i + 3 < num_words and words[i + 2] == "y":
                    tens_clean = next_word_clean
                    units_clean = re.sub(r'[^\w]', '', words[i + 3])
                    if tens_clean in SPANISH_CARDINALS and units_clean in SPANISH_CARDINALS:
                        val = hundreds_val + SPANISH_CARDINALS[tens_clean] + SPANISH_CARDINALS[units_clean]
                        logger.debug(
                            f"IntegerResolver: hundreds+tens+units compound match for '{definition.name}' "
                            f"→ {val} ('{clean_word} {tens_clean} y {units_clean}' in '{text}')"
                        )
                        return ParameterResolutionResult(
                            parameter_name=definition.name,
                            value=val,
                            status=ParameterResolutionStatus.RESOLVED
                        )
                
                # Hundreds + single cardinal
                if next_word_clean in SPANISH_CARDINALS:
                    val = hundreds_val + SPANISH_CARDINALS[next_word_clean]
                    logger.debug(
                        f"IntegerResolver: hundreds+cardinal compound match for '{definition.name}' "
                        f"→ {val} ('{clean_word} {next_word_clean}' in '{text}')"
                    )
                    return ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=val,
                        status=ParameterResolutionStatus.RESOLVED
                    )

            # Check compound numbers with 'y' (e.g., "treinta y cinco")
            if i + 2 < num_words and words[i + 1] == "y":
                tens_word = clean_word
                units_word = re.sub(r'[^\w]', '', words[i + 2])
                if tens_word in SPANISH_CARDINALS and units_word in SPANISH_CARDINALS:
                    val = SPANISH_CARDINALS[tens_word] + SPANISH_CARDINALS[units_word]
                    logger.debug(
                        f"IntegerResolver: tens+units compound match for '{definition.name}' "
                        f"→ {val} ('{tens_word} y {units_word}' in '{text}')"
                    )
                    return ParameterResolutionResult(
                        parameter_name=definition.name,
                        value=val,
                        status=ParameterResolutionStatus.RESOLVED
                    )

            if clean_word in SPANISH_CARDINALS:
                val = SPANISH_CARDINALS[clean_word]
                logger.debug(
                    f"IntegerResolver: cardinal match for '{definition.name}' "
                    f"→ {val} (token '{clean_word}' in '{text}')"
                )
                return ParameterResolutionResult(
                    parameter_name=definition.name,
                    value=val,
                    status=ParameterResolutionStatus.RESOLVED
                )

        # 3. No integer found
        logger.debug(
            f"IntegerResolver: no integer found for '{definition.name}' in text '{text}'"
        )
        return ParameterResolutionResult(
            parameter_name=definition.name,
            value=None,
            status=ParameterResolutionStatus.UNRESOLVED_OPTIONAL if not definition.required else ParameterResolutionStatus.UNRESOLVED_REQUIRED
        )
