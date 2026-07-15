from unittest.mock import patch, AsyncMock
from core.system_service_client import SystemInfo

def test_health_check(client):
    response = client.get("api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

from core.weather_service_client import WeatherInfo

def test_execute_weather(client):
    mock_weather = WeatherInfo(temperature=22.0, precipitation_probability=10)
    with patch("core.weather_service_client.WeatherServiceClient.get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_weather
        response = client.post("/api/v1/execute", json={"text": "¿Qué tiempo hace hoy?"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["plugin_used"] == "WeatherPlugin"
        assert "grados" in data["speech"]
        assert "execution_time_ms" in data

def test_execute_with_timestamp(client):
    mock_weather = WeatherInfo(temperature=22.0, precipitation_probability=10)
    with patch("core.weather_service_client.WeatherServiceClient.get_current_weather", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_weather
        response = client.post("/api/v1/execute", json={
            "text": "¿Qué tiempo hace hoy?",
            "timestamp": 1719672000.0
        })
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["plugin_used"] == "WeatherPlugin"

def test_execute_greetings(client):
    response = client.post("/api/v1/execute", json={"text": "Hola"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plugin_used"] == "GreetingPlugin"
    assert data["speech"] in [
        "Buenos días.",
        "Buenos días, te escucho.",
        "Hola, buenos días.",
        "Buenas tardes.",
        "Buenas tardes, te escucho.",
        "Hola, buenas tardes.",
        "Buenas noches.",
        "Buenas noches, te escucho.",
        "Hola, buenas noches."
    ]
    assert "execution_time_ms" in data

def test_execute_farewell(client):
    response = client.post("/api/v1/execute", json={"text": "Adios"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plugin_used"] == "FarewellPlugin"
    assert data["speech"]  in [
        "Adiós.",
        "Hasta pronto.",
        "Hasta luego.",
        "Vale.",
        "De acuerdo."
    ]
    assert "execution_time_ms" in data

def test_execute_fallback(client):
    response = client.post("/api/v1/execute", json={"text": "dibuja un dinosaurio azul"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plugin_used"] == "FallbackPlugin"
    assert data["speech"] in [
        "No he entendido la petición.",
        "No he entendido la orden.",
        "Petición no reconocida."
    ]

def test_execute_empty_request(client):
    response = client.post("/api/v1/execute", json={})
    assert response.status_code == 422
    
def test_execute_invalid_schema(client):
    response = client.post("/api/v1/execute", json={"mensaje": "Hola"})
    assert response.status_code == 422

def test_execute_identity(client):
    mock_info = SystemInfo(
        name="Nova",
        author="David",
        version="2.5.0",
        description="Asistente personal de voz y automatización"
    )
    with patch("core.system_service_client.SystemServiceClient.get_system_info", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_info
        response = client.post("/api/v1/execute", json={"text": "¿Quién eres?"})
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["plugin_used"] == "IdentityPlugin"
        assert data["speech"] == "Soy Nova-2, tu sistema local de automatización."

def test_resolve_intent_success(client):
    response = client.post("/api/v1/resolve", json={"text": "¿Qué tiempo hace hoy?"})
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert len(data["steps"]) == 1
    step = data["steps"][0]
    assert step["plugin"] == "WeatherPlugin"
    assert step["context"]["raw_text"] == "¿Qué tiempo hace hoy?"

def test_resolve_intent_empty_text(client):
    response = client.post("/api/v1/resolve", json={"text": "   "})
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 1
    assert data["steps"][0]["plugin"] == "FallbackPlugin"

def test_resolve_validation_error(client):
    response = client.post("/api/v1/resolve", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "ValidationError"
    assert "obligatorio" in data["message"]
    assert data["status"] == 422

def test_execute_plan_success(client):
    plan_payload = {
        "steps": [
            {
                "plugin": "GreetingPlugin",
                "confidence": 95.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "Hola",
                    "normalized_text": "hola",
                    "metadata": {}
                },
                "security": {}
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plugin_used"] == "GreetingPlugin"
    assert "execution_time_ms" in data

def test_execute_plan_plugin_not_found(client):
    plan_payload = {
        "steps": [
            {
                "plugin": "UnknownPlugin",
                "confidence": 95.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "Hola",
                    "normalized_text": "hola",
                    "metadata": {}
                },
                "security": {}
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan_payload)
    assert response.status_code == 400
    data = response.json()
    assert data["error"] == "PluginNotFoundError"
    assert "UnknownPlugin" in data["message"]
    assert data["status"] == 400

def test_execute_propagates_plugin_not_found_error(client):
    """Verifica que /execute re-lanza PluginNotFoundError con HTTP 400 (D-02 fix)."""
    from unittest.mock import patch, AsyncMock
    from core.models import ExecutionPlan, ExecutionPlanStep, PluginContext

    fake_plan = ExecutionPlan(
        steps=[
            ExecutionPlanStep(
                plugin="GhostPlugin",
                context=PluginContext(raw_text="test", normalized_text="test")
            )
        ]
    )
    with patch("core.engine.IntentResolver.resolve", new_callable=AsyncMock) as mock_resolve:
        mock_resolve.return_value = fake_plan
        response = client.post("/api/v1/execute", json={"text": "test"})
        assert response.status_code == 400
        data = response.json()
        assert data["error"] == "PluginNotFoundError"
        assert "GhostPlugin" in data["message"]
        assert data["status"] == 400
