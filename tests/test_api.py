def test_execute_weather(client):
    response = client.post("/api/v1/execute", json={"text": "¿Qué tiempo hace hoy?"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["plugin_used"] == "WeatherPlugin"
    assert "grados" in data["speech"]
    assert "execution_time_ms" in data

def test_execute_fallback(client):
    response = client.post("/api/v1/execute", json={"text": "Algo que no entiendes"})
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is False
    assert data["plugin_used"] == "FallbackPlugin"
    assert data["speech"] == "Lo siento, no he entendido qué quieres hacer."

def test_execute_empty_request(client):
    response = client.post("/api/v1/execute", json={})
    assert response.status_code == 422
    
def test_execute_invalid_schema(client):
    response = client.post("/api/v1/execute", json={"mensaje": "Hola"})
    assert response.status_code == 422
