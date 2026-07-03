import json
import logging
import uuid
from pathlib import Path
from typing import List

import httpx

from core.config import settings
from core.models import PluginContext, PluginResult
from core.system_service_client import SystemServiceClient
from plugins.base import Plugin

logger = logging.getLogger(__name__)

class CapabilitiesPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "CapabilitiesPlugin"

    @property
    def description(self) -> str:
        return "Responde preguntas sobre las funciones disponibles en Nova y envía al usuario un correo con el listado completo de capacidades registradas."

    @property
    def id(self) -> str:
        return "capabilities"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué puedes hacer?",
            "¿En qué me puedes ayudar?",
            "¿Qué funciones tienes?",
            "¿Qué sabes hacer?",
            "Muéstrame tus capacidades.",
            "¿Qué comandos conoces?",
            "¿Qué cosas puedo pedirte?",
            "¿Cómo puedo usarte?",
            "¿Qué opciones tengo?",
            "Enséñame lo que puedes hacer."
        ]

    @property
    def keywords(self) -> List[str]:
        return [
            "hacer",
            "funciones",
            "capacidades",
            "puedes",
            "sabes",
            "ayuda"
        ]

    @property
    def regex_patterns(self) -> List[str]:
        return [
            r".*qué.*puedes.*hacer.*",
            r".*que.*puedes.*hacer.*",
            r".*qué.*sabes.*hacer.*",
            r".*que.*sabes.*hacer.*",
            r".*qué.*funciones.*tienes.*",
            r".*que.*funciones.*tienes.*",
            r".*qué.*eres.*capaz.*de.*hacer.*",
            r".*que.*eres.*capaz.*de.*hacer.*"
        ]

    def initialize(self) -> None:
        logger.info("Initializing CapabilitiesPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of CapabilitiesPlugin")
        
        # 1. Consult capabilities from system-service
        try:
            logger.info("Retrieving system capabilities from System Service...")
            capabilities_list = await self.client.get_capabilities()
            capabilities = capabilities_list.capabilities
            logger.info(f"Successfully retrieved {len(capabilities)} capabilities.")
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
            return PluginResult(
                success=False,
                speech="Lo siento, ahora mismo no puedo consultar las funciones disponibles."
            )
        except httpx.HTTPError as http_err:
            logger.error(f"HTTP error retrieving capabilities: {http_err}", exc_info=True)
            return PluginResult(
                success=False,
                speech="Lo siento, ahora mismo no puedo consultar las funciones disponibles."
            )
        except Exception as e:
            logger.error(f"Unexpected error querying system capabilities: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="Lo siento, ahora mismo no puedo consultar las funciones disponibles."
            )

        n = len(capabilities)

        # 2. Sort capabilities alphabetically by description (case-insensitive)
        sorted_capabilities = sorted(capabilities, key=lambda x: x.description.lower())
        
        # 3. Generate plain text body for email
        bullet_points = "\n".join([f"• {cap.description}" for cap in sorted_capabilities])
        
        body = (
            "Hola.\n\n"
            f"Actualmente puedo realizar {n} funciones.\n\n"
            "Estas son las capacidades disponibles:\n\n"
            f"{bullet_points}\n\n"
            "Este listado se genera automáticamente a partir de las capacidades registradas en el sistema."
        )

        mail_uuid = uuid.uuid4().hex[:8]
        mail_id = f"mail-{mail_uuid}"
        
        email_payload = {
            "id": mail_id,
            "subject": "Capacidades disponibles en Nova",
            "body": body,
            "content_type": "text/plain"
        }

        # 4. Deposit JSON artifact in mail_pending_dir
        pending_dir = Path(settings.mail_pending_dir)
        file_path = pending_dir / f"{mail_id}.json"
        
        logger.info(f"Generating mail artifact under: {file_path}")
        try:
            # Ensure the directory exists (useful for local development/testing)
            pending_dir.mkdir(parents=True, exist_ok=True)
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(email_payload, f, indent=2, ensure_ascii=False)
            logger.info(f"Successfully wrote mail artifact to {file_path}.")
        except Exception as write_err:
            logger.error(f"Failed to write mail artifact file to {file_path}: {write_err}", exc_info=True)
            return PluginResult(
                success=False,
                speech="Lo siento, ha ocurrido un problema al preparar el correo."
            )

        # 5. Return natural language response
        speech = f"Actualmente puedo realizar {n} funciones. Te he enviado un correo con el listado completo para que puedas consultarlo cuando quieras."
        
        return PluginResult(
            success=True,
            speech=speech,
            data={
                "num_capabilities": n,
                "mail_id": mail_id,
                "file_path": str(file_path)
            }
        )
