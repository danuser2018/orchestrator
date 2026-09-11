import httpx
import logging
from typing import List, Dict, Any
from core.config import settings

logger = logging.getLogger(__name__)

class SecurityClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.security_service_base_url

    async def register_actions(self, plugin_id: str, actions: List[Dict[str, Any]]) -> bool:
        url = f"{self.base_url.rstrip('/')}/v1/security/actions/register"
        logger.info(f"Registering actions for plugin '{plugin_id}' at {url}")
        payload = {
            "plugin_id": plugin_id,
            "actions": actions
        }
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            logger.info(f"Successfully registered actions for '{plugin_id}'")
            return True
