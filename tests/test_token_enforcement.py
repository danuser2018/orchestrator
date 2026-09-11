import time
import jwt
import pytest
from fastapi.testclient import TestClient
from main import app
from core.config import settings

client = TestClient(app)

def make_token(execution_id: str, action_id: str, secret: str = None, expires_at: int = None, audience: str = "nova-orchestrator"):
    now = int(time.time())
    exp = expires_at if expires_at is not None else now + 300
    sec = secret if secret is not None else settings.security_hmac_secret
    payload = {
        "execution_id": execution_id,
        "action_id": action_id,
        "audience": audience,
        "issued_at": now,
        "expires_at": exp,
        "nonce": "test-nonce"
    }
    return jwt.encode(payload, sec, algorithm="HS256")

def test_token_enforcement_valid_token_success():
    corr_id = "exec-valid-001"
    token = make_token(execution_id=corr_id, action_id="greeting")
    plan = {
        "steps": [
            {
                "plugin": "greeting",
                "confidence": 100.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "hola",
                    "normalized_text": "hola",
                    "correlation_id": corr_id,
                    "channel": "voice"
                },
                "security": {
                    "authorization_token": token
                }
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True

def test_token_enforcement_missing_token_403():
    corr_id = "exec-missing-001"
    plan = {
        "steps": [
            {
                "plugin": "greeting",
                "confidence": 100.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "hola",
                    "normalized_text": "hola",
                    "correlation_id": corr_id,
                    "channel": "voice"
                },
                "security": {}
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan)
    assert response.status_code == 403
    data = response.json()
    assert data["error"] == "UNAUTHORIZED_ACTION"

def test_token_enforcement_invalid_signature_403():
    corr_id = "exec-invalid-sig"
    bad_token = make_token(execution_id=corr_id, action_id="greeting", secret="wrong-secret")
    plan = {
        "steps": [
            {
                "plugin": "greeting",
                "confidence": 100.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "hola",
                    "normalized_text": "hola",
                    "correlation_id": corr_id,
                    "channel": "voice"
                },
                "security": {
                    "authorization_token": bad_token
                }
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan)
    assert response.status_code == 403
    assert response.json()["error"] == "UNAUTHORIZED_ACTION"

def test_token_enforcement_expired_token_403():
    corr_id = "exec-expired"
    expired_token = make_token(execution_id=corr_id, action_id="greeting", expires_at=int(time.time()) - 10)
    plan = {
        "steps": [
            {
                "plugin": "greeting",
                "confidence": 100.0,
                "parameters": {},
                "channel": "voice",
                "context": {
                    "raw_text": "hola",
                    "normalized_text": "hola",
                    "correlation_id": corr_id,
                    "channel": "voice"
                },
                "security": {
                    "authorization_token": expired_token
                }
            }
        ]
    }
    response = client.post("/api/v1/execute-plan", json=plan)
    assert response.status_code == 403
    assert response.json()["error"] == "UNAUTHORIZED_ACTION"
