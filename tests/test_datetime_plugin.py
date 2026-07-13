import pytest
from datetime import datetime
from unittest.mock import patch, MagicMock
from core.datetime_service import DateTimeService
from plugins.datetime.main import TimePlugin, DatePlugin
from core.models import PluginContext

# 1. Tests for DateTimeService
def test_datetime_service_get_current_time():
    service = DateTimeService()
    fixed_dt = datetime(2026, 7, 13, 15, 42)  # Monday
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_dt
        current_time = service.get_current_time()
        assert current_time == "15:42"

def test_datetime_service_get_current_date():
    service = DateTimeService()
    fixed_dt = datetime(2026, 7, 13, 15, 42)  # Monday
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_dt
        current_date = service.get_current_date()
        assert current_date == "Hoy es lunes, 13 de julio de 2026."

def test_datetime_service_get_current_time_exception():
    service = DateTimeService()
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.side_effect = Exception("System clock error")
        with pytest.raises(Exception) as excinfo:
            service.get_current_time()
        assert "System clock error" in str(excinfo.value)

def test_datetime_service_get_current_date_exception():
    service = DateTimeService()
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.side_effect = Exception("System clock error")
        with pytest.raises(Exception) as excinfo:
            service.get_current_date()
        assert "System clock error" in str(excinfo.value)


# 2. Tests for TimePlugin
@pytest.mark.asyncio
async def test_time_plugin_success():
    plugin = TimePlugin()
    plugin.initialize()
    
    fixed_dt = datetime(2026, 7, 13, 15, 42)
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_dt
        context = PluginContext(raw_text="¿Qué hora es?", normalized_text="que hora es")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Son las 15:42."
        assert result.data == {"time": "15:42"}

@pytest.mark.asyncio
async def test_time_plugin_error():
    plugin = TimePlugin()
    plugin.initialize()
    
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.side_effect = Exception("OS clock issue")
        context = PluginContext(raw_text="¿Qué hora es?", normalized_text="que hora es")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."
        assert result.data is None


# 3. Tests for DatePlugin
@pytest.mark.asyncio
async def test_date_plugin_success():
    plugin = DatePlugin()
    plugin.initialize()
    
    fixed_dt = datetime(2026, 7, 13, 15, 42)
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.return_value = fixed_dt
        context = PluginContext(raw_text="¿Qué día es hoy?", normalized_text="que dia es hoy")
        result = await plugin.execute(context)
        
        assert result.success is True
        assert result.speech == "Hoy es lunes, 13 de julio de 2026."
        assert result.data == {"date": "Hoy es lunes, 13 de julio de 2026."}

@pytest.mark.asyncio
async def test_date_plugin_error():
    plugin = DatePlugin()
    plugin.initialize()
    
    with patch("core.datetime_service.datetime") as mock_datetime:
        mock_datetime.now.side_effect = Exception("OS clock issue")
        context = PluginContext(raw_text="¿Qué día es hoy?", normalized_text="que dia es hoy")
        result = await plugin.execute(context)
        
        assert result.success is False
        assert result.speech == "No he podido obtener la información."
        assert result.data is None


# 4. Metadata verification tests
def test_plugin_metadata():
    time_plugin = TimePlugin()
    date_plugin = DatePlugin()
    
    assert time_plugin.id == "time"
    assert time_plugin.name == "TimePlugin"
    assert time_plugin.priority == 80
    assert len(time_plugin.examples) > 0
    assert all(isinstance(e, str) for e in time_plugin.examples)
    
    assert date_plugin.id == "date"
    assert date_plugin.name == "DatePlugin"
    assert date_plugin.priority == 80
    assert len(date_plugin.examples) > 0
    assert all(isinstance(e, str) for e in date_plugin.examples)
    
    assert set(time_plugin.examples).isdisjoint(set(date_plugin.examples)), \
        "TimePlugin and DatePlugin must not share example phrases to avoid routing ambiguity"
