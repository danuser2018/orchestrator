def test_health_check(client):
    response = client.get("api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_resolve_intent_success(client):
    response = client.post("/api/v1/resolve", json={"text": "¿Qué tiempo hace hoy?"})
    assert response.status_code == 200
    data = response.json()
    assert "steps" in data
    assert len(data["steps"]) == 1
    step = data["steps"][0]
    assert step["plugin"] in ("weather", "WeatherPlugin")
    assert step["context"]["raw_text"] == "¿Qué tiempo hace hoy?"

def test_resolve_intent_empty_text(client):
    response = client.post("/api/v1/resolve", json={"text": "   "})
    assert response.status_code == 200
    data = response.json()
    assert len(data["steps"]) == 1
    assert data["steps"][0]["plugin"] in ("fallback", "FallbackPlugin")


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

def test_execute_legacy_endpoint_returns_404(client):
    """Verifies that the legacy POST /api/v1/execute endpoint is removed and returns 404."""
    response = client.post("/api/v1/execute", json={"text": "Hola"})
    assert response.status_code == 404
