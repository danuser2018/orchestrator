import pytest
from core.parameter_resolution.resolvers.command import CommandResolver


def test_normalize_lowercase():
    assert CommandResolver.normalize_phrase("CALCULADORA") == "calculadora"
    assert CommandResolver.normalize_phrase("Abre El Navegador") == "abre el navegador"


def test_normalize_strip_diacritics():
    assert CommandResolver.normalize_phrase("máquina") == "maquina"
    assert CommandResolver.normalize_phrase("cálculo") == "calculo"
    assert CommandResolver.normalize_phrase("MÁQUINA DE CÁLCULO") == "maquina de calculo"
    assert CommandResolver.normalize_phrase("configuración rápida") == "configuracion rapida"


def test_normalize_strip_punctuation():
    assert CommandResolver.normalize_phrase("¡Abre la calculadora!") == "abre la calculadora"
    assert CommandResolver.normalize_phrase("¿puedes abrir la calculadora?") == "puedes abrir la calculadora"
    assert CommandResolver.normalize_phrase("backup, por favor.") == "backup por favor"
    assert CommandResolver.normalize_phrase("formatear-disco / unidad!") == "formatear disco unidad"


def test_normalize_collapse_whitespace():
    assert CommandResolver.normalize_phrase("   abre   la    calculadora  ") == "abre la calculadora"
    assert CommandResolver.normalize_phrase("\n\t maquina \t de   calcular \n") == "maquina de calcular"


def test_normalize_empty_and_falsy():
    assert CommandResolver.normalize_phrase("") == ""
    assert CommandResolver.normalize_phrase("   ") == ""
    assert CommandResolver.normalize_phrase(None) == ""


def test_normalize_scenario_5_exact_equivalence():
    input_text = "  ¡MÁQUINA   DE CALCULAR!  "
    catalog_phrase = "Máquina de calcular"
    assert CommandResolver.normalize_phrase(input_text) == "maquina de calcular"
    assert CommandResolver.normalize_phrase(catalog_phrase) == "maquina de calcular"
    assert CommandResolver.normalize_phrase(input_text) == CommandResolver.normalize_phrase(catalog_phrase)
