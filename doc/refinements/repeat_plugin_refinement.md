# Refinamiento de la Feature: Plugin "Repeat"

- **Archivo de origen**: [repeat_plugin.md](file:///home/danuser2018/workspace/orchestrator/doc/features/repeat_plugin.md)
- **Fecha**: 2026-07-19
- **Estado**: Listo para revisión de DoR

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Desarrollar e integrar el plugin **Repeat** (`RepeatPlugin`) en el servicio `orchestrator` de Nova-2. Este plugin permitirá al usuario solicitar al asistente de voz que repita la última respuesta generada, obteniendo dicha información de manera desacoplada mediante una consulta a la API REST del microservicio `context-service`.

### Actores y Reglas de Negocio
1. **Usuario**: Realiza una solicitud oral o escrita con intenciones de repetición (ej. "¿puedes repetir?").
2. **Orchestrator (RepeatPlugin)**:
   - Identifica la intención mediante scoring de similitud semántica.
   - Consulta el estado más reciente de la conversación en el `context-service`.
   - Si existe una última respuesta (HTTP 200), la devuelve intacta sin reinterpretarla.
   - Si no existe contexto disponible (HTTP 404), responde con el mensaje informativo: `"No hay respuestas anteriores."`.
   - Si ocurre un fallo de red o del servicio remoto, responde con los mensajes estandarizados de error según el ADR-002 del orquestador.
   - Permanece desacoplado del Event Bus (no publica ni suscribe eventos directamente) y no almacena ningún estado en memoria local.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/config.py`: Adición del campo de configuración `context_service_base_url` con valor por defecto `"http://context-service:8000"`. <br> - `CHANGELOG.md`: Registro del cambio en la sección `[Sin publicar]`. |
| `orchestrator` | **[NEW]** | - `core/context_service_client.py`: Cliente de API `ContextServiceClient` para interactuar con la API REST de `context-service`. <br> - `plugins/repeat/main.py`: Implementación del plugin `RepeatPlugin` utilizando el nuevo cliente. <br> - `tests/test_repeat_plugin.py`: Suite de tests unitarios y de integración mockeados para verificar el funcionamiento feliz, la ausencia de contexto (404) y la tolerancia a fallos. |
| `home-assistant` (Despliegue) | Modificar | - `docker-compose.yml`: Adición de la variable de entorno `CONTEXT_SERVICE_BASE_URL: http://context-service:8000` en el contenedor `orchestrator`, y configuración de la dependencia de arranque `context-service` con la condición `service_healthy`. |

> **Evaluación de necesidad de ADR:** De acuerdo con la skill `architecture-decisions`, no se requiere la creación de un nuevo ADR local para esta característica. La implementación del plugin no introduce nuevos patrones de comunicación ni altera modelos de datos públicos (`api-contracts`), sino que consume un endpoint REST existente del `context-service` utilizando la infraestructura y patrones ya documentados en el ADR-014 y ADR-019.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Ejecución exitosa con contexto disponible
```gherkin
Dado que el orquestador tiene configurada la URL del context-service en "context_service_base_url"
Y el context-service tiene registrada una última respuesta con el texto "Hoy es lunes."
Cuando el usuario dice "Repite, por favor"
Entonces el planificador debe seleccionar "RepeatPlugin" con alta confianza
Y el plugin debe consumir el endpoint del context-service
Y debe retornar con éxito la respuesta exacta: "Hoy es lunes."
```

### Escenario 2: Ausencia de contexto conversacional (404)
```gherkin
Dado que el context-service no tiene ninguna respuesta previa almacenada en el almacén de contexto
Cuando el usuario dice "¿Qué has dicho?"
Entonces el orquestador debe ejecutar "RepeatPlugin"
Y el plugin debe detectar la ausencia de contexto mediante un código de respuesta HTTP 404 del servicio
Y debe retornar el mensaje informativo: "No hay respuestas anteriores."
```

### Escenario 3: Caída del servicio de contexto o timeout
```gherkin
Dado que el context-service no está disponible en la red o tarda demasiado en responder (timeout)
Cuando el usuario solicita repetir la respuesta anterior diciendo "¿Cómo has dicho?"
Entonces el intento de conexión del cliente en "RepeatPlugin" debe fallar
Y el plugin debe capturar el error de conexión o timeout
Y debe retornar el mensaje de error estándar para fallos de conectividad: "Servicio no disponible."
```

### Escenario 4: Error HTTP inesperado en el servicio
```gherkin
Dado que el endpoint de context-service responde con un código de error de servidor HTTP 500
Cuando el usuario solicita repetir la última respuesta
Entonces "RepeatPlugin" debe capturar el fallo HTTP
Y debe retornar el mensaje de error estándar para fallos de información: "No he podido obtener la información."
```

---

## 4. Diseño Técnico y Contratos

### Discrepancia Detectada y Alineación de Mensajes de Error (ADR-002)
El documento original (`repeat_plugin.md`) propone retornar `"Ahora mismo no puedo acceder al contexto de la conversación."` en caso de error de comunicación. No obstante, para cumplir estrictamente con el **ADR-002 (Alineación de mensajes de error genéricos en plugins)**, la gestión de excepciones de este plugin de consulta externa debe retornar:
- `"Servicio no disponible."` si hay un fallo de conectividad directa (Timeout, Connection Error).
- `"No he podido obtener la información."` si hay un fallo de respuesta del servidor (5xx, HTTPError general).

Adicionalmente, ante la ausencia de contexto conversacional (HTTP 404), se alinea el mensaje informativo de la propuesta original (`"Todavía no tengo ninguna respuesta para repetir."`) cambiándolo a `"No hay respuestas anteriores."` para respetar la directriz de máxima brevedad y estilo directo establecida en la guía de tono (`TONE_GUIDE.md`) del asistente Nova-2.

### Endpoint de Consumo (`context-service` - English)
El plugin llamará al endpoint REST expuesto por el microservicio de contexto:
- **Method**: `GET`
- **Path**: `/v1/context/last-response`
- **Response Schema (200 OK)**:
  ```json
  {
    "response": "string",
    "plugin": "string",
    "timestamp": "string"
  }
  ```
- **Response Schema (404 Not Found)**:
  ```json
  {
    "error": "NO_CONTEXT_AVAILABLE",
    "message": "No context available.",
    "status": 404
  }
  ```

### Estructura de Configuración (`core/config.py` - English)
```python
class Settings(BaseSettings):
    # ... otras configuraciones
    context_service_base_url: str = "http://context-service:8000"
```

### Cliente de Servicio de Contexto (`core/context_service_client.py` - English)
```python
import httpx
import logging
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class LastResponseInfo(BaseModel):
    response: str
    plugin: str
    timestamp: str

class ContextServiceClient:
    def __init__(self, base_url: Optional[str] = None):
        from core.config import settings
        self.base_url = base_url or settings.context_service_base_url

    async def get_last_response(self) -> Optional[LastResponseInfo]:
        url = f"{self.base_url.rstrip('/')}/v1/context/last-response"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            if response.status_code == 404:
                logger.info("No context available on context-service.")
                return None
            response.raise_for_status()
            data = response.json()
            logger.info(f"Context response received: {data}")
            return LastResponseInfo(**data)
```

### Implementación del Plugin (`plugins/repeat/main.py` - English)
```python
import httpx
import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.context_service_client import ContextServiceClient

logger = logging.getLogger(__name__)

class RepeatPlugin(Plugin):
    def initialize(self) -> None:
        self.client = ContextServiceClient()

    @property
    def name(self) -> str:
        return "RepeatPlugin"

    @property
    def description(self) -> str:
        return "Permite al usuario solicitar que Nova repita la última respuesta generada."

    @property
    def id(self) -> str:
        return "repeat"

    @property
    def priority(self) -> int:
        return 70

    @property
    def examples(self) -> List[str]:
        return [
            "Repite.",
            "Repite, por favor.",
            "¿Puedes repetir?",
            "¿Qué has dicho?",
            "Dímelo otra vez.",
            "No te he oído.",
            "No lo he entendido.",
            "¿Cómo has dicho?"
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.debug("RepeatPlugin selected")
        try:
            last_resp = await self.client.get_last_response()
            if last_resp is None:
                return PluginResult(
                    success=True,
                    speech="No hay respuestas anteriores."
                )
            return PluginResult(
                success=True,
                speech=last_resp.response,
                data={
                    "repeated_plugin": last_resp.plugin,
                    "repeated_timestamp": last_resp.timestamp
                }
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection failure to context-service: {conn_err}")
            return PluginResult(
                success=False,
                speech="Servicio no disponible."
            )
        except httpx.HTTPError as http_err:
            logger.error(f"HTTP error from context-service: {http_err}")
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
        except Exception as exc:
            logger.error(f"Unexpected error executing RepeatPlugin: {exc}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Microservicio no disponible en arranque** | El orquestador arranca normalmente. El plugin solo fallará cuando intente ejecutarse tras la llamada HTTP. | Resiliencia de FastAPI. La conexión del cliente se realiza por petición en caliente. |
| **Timeout de red** | El plugin interrumpe la petición tras un límite de 5.0 segundos y devuelve un error amigable. | Configuración de timeout en el cliente `httpx.AsyncClient(timeout=5.0)` de `ContextServiceClient`. |
| **Respuesta vacía o corrupta** | Si la estructura JSON no coincide con la esperada, se lanza un error de validación interna. | Captura de excepción genérica `Exception` en `execute()` devolviendo el mensaje `"No he podido obtener la información."`. |
| **Ausencia de registros previos** | Devuelve el mensaje informativo controlado. | Tratamiento explícito del código HTTP 404 del endpoint de contexto. |

---

## 6. Estrategia de Testing

Se añadirá el fichero de pruebas `tests/test_repeat_plugin.py` para verificar los siguientes escenarios utilizando mocks:
1. **Propiedades del Plugin**: Verificar id (`repeat`), prioridad (`70`), nombre (`RepeatPlugin`) y ejemplos cargados.
2. **Caso Feliz (Contexto Correcto)**: Simular llamada HTTP exitosa retornando una respuesta válida del context-service y validar que el plugin la devuelve íntegra.
3. **Caso 404 (Sin contexto)**: Simular llamada HTTP con respuesta 404 y verificar la respuesta controlada `"No hay respuestas anteriores."`.
4. **Errores de Conexión/Timeout**: Validar la captura de `ConnectError` and `TimeoutException` mapeando a `"Servicio no disponible."`.
5. **Errores de Servidor (500)**: Validar la respuesta HTTP 500 mapeando a `"No he podido obtener la información."`.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Configuración del Entorno y Propiedades**
  - [ ] Modificar `core/config.py` para añadir el campo `context_service_base_url: str = "http://context-service:8000"` a la clase `Settings`.
- [ ] **Fase 2: Cliente del Servicio de Contexto**
  - [ ] Crear el archivo `core/context_service_client.py` implementando la clase `ContextServiceClient` y el modelo Pydantic `LastResponseInfo` en inglés.
- [ ] **Fase 3: Implementación del Plugin**
  - [ ] Crear el directorio `plugins/repeat/`.
  - [ ] Crear `plugins/repeat/__init__.py`.
  - [ ] Crear `plugins/repeat/main.py` con la clase `RepeatPlugin`, registrando intenciones, prioridades y la llamada al `ContextServiceClient` con control de excepciones.
- [ ] **Fase 4: Configuración de Infraestructura y Despliegue**
  - [ ] Modificar `/home/danuser2018/workspace/home-assistant/docker-compose.yml`:
    - [ ] Agregar la variable `CONTEXT_SERVICE_BASE_URL: http://context-service:8000` en la sección `environment` de `orchestrator`.
    - [ ] Agregar `context-service` en la sección `depends_on` de `orchestrator` con la condición `service_healthy`.
- [ ] **Fase 5: Pruebas y Aseguramiento de Calidad**
  - [ ] Crear la suite de pruebas unitarias y de integración `tests/test_repeat_plugin.py`.
  - [ ] Actualizar `tests/test_plugin_registration.py` para verificar que el nuevo ID de plugin `"repeat"` se encuentre registrado en las capacidades publicadas del sistema.
  - [ ] Ejecutar localmente la suite de pruebas del orquestador mediante `PYTHONPATH=. pytest` para asegurar que los tests pasen.
- [ ] **Fase 6: Registro e Historial de Cambios**
  - [ ] Actualizar el archivo `CHANGELOG.md` del orquestador agregando el soporte para el plugin Repeat en la sección `[Sin publicar]`.
