import pytest
from core.command_catalog import CommandCatalogProjection
from core.events import PublicCommandEntry
from core.parameter_resolution.resolvers.command import CommandResolver


def test_command_catalog_empty_initial_state():
    catalog = CommandCatalogProjection()
    assert catalog.is_ready is False
    assert catalog.list_commands() == []
    assert catalog.get_command("calculator") is None


def test_command_catalog_update_from_event():
    catalog = CommandCatalogProjection()
    entries = [
        PublicCommandEntry(
            name="calculator",
            risk="low",
            phrases=["Calculadora", "  ¡Abre la calculadora!  "],
        ),
        PublicCommandEntry(
            name="backup",
            risk="medium",
            phrases=["Copia de seguridad"],
        ),
    ]

    catalog.update_from_event(entries, CommandResolver.normalize_phrase)

    assert catalog.is_ready is True
    assert len(catalog.list_commands()) == 2

    calc = catalog.get_command("calculator")
    assert calc is not None
    assert calc.name == "calculator"
    assert calc.risk == "low"
    assert calc.phrases == ["Calculadora", "  ¡Abre la calculadora!  "]
    assert calc.normalized_phrases == ["calculadora", "abre la calculadora"]

    backup = catalog.get_command("backup")
    assert backup is not None
    assert backup.name == "backup"
    assert backup.risk == "medium"
    assert backup.normalized_phrases == ["copia de seguridad"]


def test_command_catalog_atomic_replacement():
    catalog = CommandCatalogProjection()
    entries_1 = [
        PublicCommandEntry(name="calculator", risk="low", phrases=["calculadora"])
    ]
    catalog.update_from_event(entries_1, CommandResolver.normalize_phrase)
    assert len(catalog.list_commands()) == 1

    entries_2 = [
        PublicCommandEntry(name="backup", risk="medium", phrases=["backup"]),
        PublicCommandEntry(name="github", risk="low", phrases=["github"]),
    ]
    catalog.update_from_event(entries_2, CommandResolver.normalize_phrase)
    assert len(catalog.list_commands()) == 2
    assert catalog.get_command("calculator") is None
    assert catalog.get_command("backup") is not None
    assert catalog.get_command("github") is not None
