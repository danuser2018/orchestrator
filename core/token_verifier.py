import time
import jwt
import logging
from core.config import settings

logger = logging.getLogger(__name__)

class TokenVerificationError(Exception):
    pass

class UnauthorizedActionError(Exception):
    pass

def verify_step_token(token: str, expected_correlation_id: str, expected_action_id: str, secret: str = None) -> dict:
    if not token:
        raise TokenVerificationError("Missing authorization token")

    hmac_secret = secret or settings.security_hmac_secret
    try:
        payload = jwt.decode(token, hmac_secret, algorithms=["HS256"], options={"verify_exp": False})
    except Exception as e:
        raise TokenVerificationError(f"Invalid token signature or format: {e}")

    now = int(time.time())
    if payload.get("expires_at", 0) <= now:
        raise TokenVerificationError("Authorization token has expired")

    if payload.get("audience") != "nova-orchestrator":
        raise TokenVerificationError(f"Invalid audience '{payload.get('audience')}'")

    if payload.get("execution_id") != expected_correlation_id:
        raise TokenVerificationError(
            f"Correlation ID mismatch: token execution_id '{payload.get('execution_id')}' != step correlation_id '{expected_correlation_id}'"
        )

    if payload.get("action_id") != expected_action_id:
        raise TokenVerificationError(
            f"Action ID mismatch: token action_id '{payload.get('action_id')}' != step action_id '{expected_action_id}'"
        )

    return payload
