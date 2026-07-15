# Refinamiento de la Feature: Plugins de Control de Volumen

- **Archivo de origen**: [sound_plugins.md](file:///home/danuser2018/workspace/orchestrator/doc/features/sound_plugins.md)
- **Fecha**: 2026-07-15
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Incorporar cinco nuevos plugins públicos de control de volumen en el Orchestrator de Nova-2 para permitir la consulta y modificación del sonido del sistema a través de lenguaje natural:
* **VolumeUpPlugin** (id: `volume-up`, prioridad 60): Incrementa el volumen en un paso fijo de 10.
* **VolumeDownPlugin** (id: `volume-down`, prioridad 60): Disminuye el volumen en un paso fijo de 10.
* **VolumeStatusPlugin** (id: `volume-status`, prioridad 60): Consulta el volumen actual y el estado de silencio (mute).
* **MutePlugin** (id: `mute`, prioridad 60): Silencia el sistema de audio física y lógicamente.
* **UnmutePlugin** (id: `unmute`, prioridad 60): Restaura el sonido del sistema.

Para mantener el desacoplamiento arquitectónico y la testabilidad, los plugins no interactuarán directamente con el hardware ni invocarán comandos del sistema. En su lugar, consumirán la API REST del microservicio native `host-service` (HAL) a través de una nueva clase centralizada `HostServiceClient` ubicada en `core/host_service_client.py`. El cliente apuntará por defecto a `http://host.docker.internal:8007` (el puerto de escucha del daemon de control local).

Todas las respuestas de voz generadas por estos plugins seguirán el principio de mínima información y estilo impersonal especificados en `TONE_GUIDE.md`.

### Actores y Reglas de Negocio
1. **Usuario**: Envía peticiones en lenguaje natural pidiendo cambiar o comprobar el audio (ej. "Súbele un poco", "Silencio", "¿Qué volumen hay?").
2. **Orchestrator**: Evalúa las frases semánticamente con `RapidFuzz` y enruta la petición al plugin que supere el umbral configurado (`SIMILARITY_THRESHOLD`).
3. **HostServiceClient**: Cliente HTTP asíncrono en el core del orquestador que realiza la comunicación de red con la API del `host-service`.
4. **VolumeUpPlugin**: Invoca el endpoint `/v1/audio/volume/up` enviando el paso fijo de incrementación (`step=10`).
5. **VolumeDownPlugin**: Invoca el endpoint `/v1/audio/volume/down` enviando el paso fijo de decrecimiento (`step=10`).
6. **VolumeStatusPlugin**: Invoca el endpoint `/v1/audio/volume` para comprobar el volumen y estado de silencio actuales.
7. **MutePlugin**: Invoca el endpoint `/v1/audio/mute`. Confirma la acción con `"Hecho."`.
8. **UnmutePlugin**: Invoca el endpoint `/v1/audio/unmute`. Confirma la acción con `"Sonido activado."`.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/config.py`: Añadir el parámetro de configuración `host_service_base_url` a la clase `Settings` con valor por defecto `"http://host.docker.internal:8007"`. <br>- `core/host_service_client.py` [NEW]: Crear el cliente asíncrono `HostServiceClient` y el modelo de datos `AudioState`. <br>- `plugins/volume/` [NEW]: Crear el directorio y el archivo `main.py` con las clases `VolumeUpPlugin`, `VolumeDownPlugin`, `VolumeStatusPlugin`, `MutePlugin` y `UnmutePlugin`. <br>- `tests/test_volume_plugin.py` [NEW]: Agregar la suite de pruebas unitarias para el cliente y los 5 plugins utilizando mocks. <br>- `tests/test_routing.py` [Modificar]: Incorporar pruebas de enrutamiento para RapidFuzz con los ejemplos de los 5 plugins. <br>- `tests/test_plugin_registration.py` [Modificar]: Incluir los IDs de capacidad `"volume-up"`, `"volume-down"`, `"volume-status"`, `"mute"` y `"unmute"` en las aserciones de registro dinámico en `system-service`. <br>- `README.md` [Modificar]: Registrar los plugins en la sección de prioridades del orquestador. <br>- `CHANGELOG.md` [Modificar]: Registrar los cambios en la sección `[Sin publicar]`. |
| `home-assistant` | Modificar | - `docker-compose.yml` [Modificar]: Configurar inline la variable de entorno `HOST_SERVICE_BASE_URL: http://host.docker.internal:8007` bajo el servicio `orchestrator`. <br>- `docs/services.md` [Modificar]: Añadir los 5 IDs de capacidad en los payloads de ejemplos documentados de `system-service`. <br>- `CHANGELOG.md` [Modificar]: Registrar las nuevas capacidades de sonido e integración en el registro histórico global. |
| Todos los demás servicios | Ninguno | Las interfaces HTTP REST públicas y el flujo conversacional no se ven alterados. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
No se requiere un nuevo ADR. El diseño se ajusta estrictamente al [ADR-013: Integración del Servicio Host (host-service)](file:///home/danuser2018/workspace/home-assistant/docs/adr/adr-013-integracion-host-service.md) que establece la delegación del hardware nativo en el puerto 8007 mediante la pasarela Docker Compose `host.docker.internal`, y al [ADR-002: Alineación de mensajes de error genéricos en plugins](file:///home/danuser2018/workspace/orchestrator/doc/adr/adr-002-alineacion-mensajes-error-plugins.md).

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

> **Nota de trazabilidad:** Las respuestas de voz definidas en los criterios de aceptación a continuación difieren intencionalmente de los ejemplos del documento descriptivo original (`sound_plugins.md`). Los ajustes se realizaron para alinear los textos con el `TONE_GUIDE.md` (principio de mínima información, estilo impersonal): *"Volumen al 60 por ciento y silenciado."* reemplaza a *"El volumen está al 60 y el sonido está silenciado."*; *"Sonido activado."* reemplaza a *"Ya puedo hablar otra vez."* Estas respuestas del refinamiento prevalecen sobre las del documento de feature.

### Escenario 1: Incremento de volumen normal
```gherkin
Dado que el host-service devuelve el estado {"volume": 50, "muted": false} tras un incremento
Cuando el usuario solicita "Sube el volumen" y el Orchestrator enruta a VolumeUpPlugin
Entonces el plugin invoca a HostServiceClient.volume_up con step=10
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al 50 por ciento."
Y el JSON de data contiene {"volume": 50, "muted": false}
```

### Escenario 2: Intento de incremento sobre volumen máximo
```gherkin
Dado que el host-service aplica el incremento pero devuelve el estado {"volume": 100, "muted": false} porque el límite ya estaba alcanzado
Cuando el usuario solicita "Más volumen" y el Orchestrator enruta a VolumeUpPlugin
Entonces el plugin invoca a HostServiceClient.volume_up con step=10
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al máximo."
Y el JSON de data contiene {"volume": 100, "muted": false}
```

### Escenario 3: Reducción de volumen normal
```gherkin
Dado que el host-service devuelve el estado {"volume": 30, "muted": false} tras una reducción
Cuando el usuario solicita "Baja el volumen" y el Orchestrator enruta a VolumeDownPlugin
Entonces el plugin invoca a HostServiceClient.volume_down con step=10
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al 30 por ciento."
Y el JSON de data contiene {"volume": 30, "muted": false}
```

### Escenario 4: Intento de reducción sobre volumen mínimo
```gherkin
Dado que el host-service aplica la reducción pero devuelve el estado {"volume": 0, "muted": false} porque el límite ya estaba alcanzado
Cuando el usuario solicita "Bájalo" y el Orchestrator enruta a VolumeDownPlugin
Entonces el plugin invoca a HostServiceClient.volume_down con step=10
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al mínimo."
Y el JSON de data contiene {"volume": 0, "muted": false}
```

### Escenario 5: Consulta de volumen con sonido activo
```gherkin
Dado que el host-service responde con el estado {"volume": 60, "muted": false}
Cuando el usuario solicita "Dime el volumen" y el Orchestrator enruta a VolumeStatusPlugin
Entonces el plugin invoca a HostServiceClient.get_volume
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al 60 por ciento."
Y el JSON de data contiene {"volume": 60, "muted": false}
```

### Escenario 6: Consulta de volumen con sistema silenciado
```gherkin
Dado que el host-service responde con el estado {"volume": 60, "muted": true}
Cuando el usuario solicita "¿Cuál es el volumen actual?" y el Orchestrator enruta a VolumeStatusPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Volumen al 60 por ciento y silenciado."
Y el JSON de data contiene {"volume": 60, "muted": true}
```

### Escenario 7: Silenciar el sistema (Mute) exitoso
```gherkin
Dado que el host-service silencia correctamente el sistema de audio
Cuando el usuario solicita "Silencio" y el Orchestrator enruta a MutePlugin
Entonces el plugin invoca a HostServiceClient.mute
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Hecho."
Y el JSON de data contiene {"volume": 60, "muted": true}
```

### Escenario 8: Restaurar el sonido (Unmute) exitoso
```gherkin
Dado que el host-service activa correctamente el audio
Cuando el usuario solicita "Desmutéate" y el Orchestrator enruta a UnmutePlugin
Entonces el plugin invoca a HostServiceClient.unmute
Y el plugin responde con success=True
Y el speech devuelto es exactamente "Sonido activado."
Y el JSON de data contiene {"volume": 60, "muted": false}
```

### Escenario 9: Indisponibilidad del host-service
```gherkin
Dado que la API REST del host-service está apagada o lanza un timeout de conexión
Cuando el usuario solicita cualquier cambio o consulta de volumen
Entonces el plugin correspondiente captura la excepción de red
Y el plugin responde con success=False
Y el speech devuelto es exactamente "Servicio no disponible."
```

---

## 4. Diseño Técnico y Contratos

### Parámetros de Configuración (`core/config.py` y `docker-compose.yml`)

Se añade el endpoint base de la HAL a la clase `Settings`:
```python
class Settings(BaseSettings):
    # ... otras variables ...
    host_service_base_url: str = "http://host.docker.internal:8007"
```

Se declara la variable en el entorno del orquestador en `docker-compose.yml`:
```yaml
  orchestrator:
    # ...
    environment:
      SYSTEM_SERVICE_BASE_URL: http://system-service:8000
      MAIL_PENDING_DIR: /shared/mail/pending
      WEATHER_SERVICE_BASE_URL: http://weather-service:8000
      HOST_SERVICE_BASE_URL: http://host.docker.internal:8007
```

### Contrato del Cliente de Host (`core/host_service_client.py`)
```python
import httpx
import logging
from pydantic import BaseModel, Field
from core.config import settings

logger = logging.getLogger(__name__)

class AudioState(BaseModel):
    volume: int = Field(..., ge=0, le=100)
    muted: bool

class HostServiceClient:
    def __init__(self, base_url: str = None):
        self.base_url = base_url or settings.host_service_base_url

    async def get_volume(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def volume_up(self, step: int) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume/up"
        logger.info(f"Consuming URL: {url} with step: {step}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"step": step})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def volume_down(self, step: int) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/volume/down"
        logger.info(f"Consuming URL: {url} with step: {step}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url, json={"step": step})
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def mute(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/mute"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)

    async def unmute(self) -> AudioState:
        url = f"{self.base_url.rstrip('/')}/v1/audio/unmute"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return AudioState(**data)
```

### Implementación de Plugins (`plugins/volume/main.py`)
```python
import logging
from typing import List
import httpx
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.host_service_client import HostServiceClient

logger = logging.getLogger(__name__)

class VolumeUpPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeUpPlugin"

    @property
    def description(self) -> str:
        return "Incrementa el volumen del sistema"

    @property
    def id(self) -> str:
        return "volume-up"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Sube el volumen",
            "Sube un poco el volumen",
            "Más volumen",
            "Pon el volumen más alto",
            "Aumenta el volumen",
            "Quiero más volumen",
            "Dale más volumen",
            "Súbelo",
            "Un poco más alto",
            "Se oye bajo"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeUpPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeUpPlugin")
        try:
            result = await self.client.volume_up(10)
            if result.volume >= 100:
                speech = "Volumen al máximo."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeUpPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class VolumeDownPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeDownPlugin"

    @property
    def description(self) -> str:
        return "Disminuye el volumen del sistema"

    @property
    def id(self) -> str:
        return "volume-down"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Baja el volumen",
            "Menos volumen",
            "Baja un poco",
            "Está muy alto",
            "Reduce el volumen",
            "Bájalo",
            "Un poco menos",
            "Demasiado volumen",
            "Ponlo más bajo",
            "Quiero menos volumen"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeDownPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeDownPlugin")
        try:
            result = await self.client.volume_down(10)
            if result.volume <= 0:
                speech = "Volumen al mínimo."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeDownPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class VolumeStatusPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VolumeStatusPlugin"

    @property
    def description(self) -> str:
        return "Consulta el volumen actual del sistema"

    @property
    def id(self) -> str:
        return "volume-status"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cuál es el volumen?",
            "¿Qué volumen tengo?",
            "¿Cuál es el volumen actual?",
            "Dime el volumen",
            "¿Cómo está el volumen?",
            "Nivel de volumen",
            "¿A cuánto está el volumen?",
            "Volumen actual",
            "¿Qué nivel de sonido hay?",
            "¿Está muy alto el volumen?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VolumeStatusPlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VolumeStatusPlugin")
        try:
            result = await self.client.get_volume()
            if result.muted:
                speech = f"Volumen al {result.volume} por ciento y silenciado."
            else:
                speech = f"Volumen al {result.volume} por ciento."

            return PluginResult(
                success=True,
                speech=speech,
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing VolumeStatusPlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class MutePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "MutePlugin"

    @property
    def description(self) -> str:
        return "Silencia el sistema"

    @property
    def id(self) -> str:
        return "mute"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Mutéate",
            "Silénciate",
            "Quítate el sonido",
            "Ponte en silencio",
            "Deja de hacer ruido",
            "No hables",
            "Silencio",
            "Apaga el sonido",
            "Enmudece",
            "No quiero oírte"
        ]

    def initialize(self) -> None:
        logger.info("Initializing MutePlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of MutePlugin")
        try:
            result = await self.client.mute()
            return PluginResult(
                success=True,
                speech="Hecho.",
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing MutePlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")


class UnmutePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "UnmutePlugin"

    @property
    def description(self) -> str:
        return "Restaura el sonido del sistema"

    @property
    def id(self) -> str:
        return "unmute"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Desmutéate",
            "Activa el sonido",
            "Recupera el sonido",
            "Vuelve a hablar",
            "Quita el silencio",
            "Ya puedes hablar",
            "Activa el audio",
            "Devuelve el sonido",
            "Sal del modo silencio",
            "Ya puedes hacer ruido"
        ]

    def initialize(self) -> None:
        logger.info("Initializing UnmutePlugin")
        self.client = HostServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of UnmutePlugin")
        try:
            result = await self.client.unmute()
            return PluginResult(
                success=True,
                speech="Sonido activado.",
                data=result.model_dump()
            )
        except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
            logger.error(f"Connection error connecting to host-service: {conn_err}")
            return PluginResult(success=False, speech="Servicio no disponible.")
        except Exception as e:
            logger.error(f"Error executing UnmutePlugin: {e}", exc_info=True)
            return PluginResult(success=False, speech="No he podido completar la operación.")
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Pérdida de Conexión o Timeout** | Retornar una respuesta controlada con `"Servicio no disponible."` y éxito en falso. | Capturar `httpx.ConnectError` y `httpx.TimeoutException` en el bloque try/except del método `execute` de cada plugin. |
| **Error HTTP del Host (500, 503, etc.)** | Capturar y retornar `"No he podido completar la operación."`. | Llamar a `response.raise_for_status()` dentro de `HostServiceClient` y capturar excepciones genéricas en la ejecución del plugin. |
| **Respuesta JSON malformada o incompleta** | Evitar la caída del orquestador y responder con `"No he podido completar la operación."`. | La validación de tipos del constructor `AudioState(**data)` en el cliente arrojará un error si el JSON no es conforme, capturado por el bloque general `except Exception` en el plugin. |
| **Intentos redundantes de Mute/Unmute** | Operación idempotente. Devolver `"Hecho."` o `"Sonido activado."` normalmente. | El servicio `host-service` maneja el estado de forma nativa sin fallar. Los plugins reportan el estado final sin generar errores. |
| **Volumen en el límite (100 o 0)** | Responder `"Volumen al máximo."` o `"Volumen al mínimo."` según el estado devuelto por el `host-service` tras aplicar la operación. | Formatear la respuesta a partir del `AudioState` devuelto por `volume_up()` o `volume_down()`: si `result.volume >= 100` → `"Volumen al máximo."`, si `result.volume <= 0` → `"Volumen al mínimo."`. La lógica de límites reside en el `host-service` (HAL), no en los plugins. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias (`tests/test_volume_plugin.py`)
Se creará un conjunto de pruebas dedicadas a validar el funcionamiento de `HostServiceClient` y cada uno de los plugins de volumen:
1. **Pruebas del cliente (`HostServiceClient`)**:
   - Validar que las llamadas GET a `/v1/audio/volume` retornan el modelo `AudioState` correcto.
   - Validar que las llamadas POST a `/v1/audio/volume/up` y `down` pasan el parámetro de payload `{"step": 10}`.
   - Validar el tratamiento de excepciones de red (`ConnectError`, `TimeoutException`) y que son propagadas al llamador.
2. **Pruebas de comportamiento de Plugins**:
   - Usar `unittest.mock.patch` sobre los métodos del cliente `HostServiceClient` para simular respuestas prefijadas.
   - Validar `VolumeUpPlugin`:
     - Retorna `"Volumen al 50 por ciento."` si `volume_up()` devuelve `{"volume": 50, "muted": false}`.
     - Retorna `"Volumen al máximo."` si `volume_up()` devuelve `{"volume": 100, "muted": false}`.
   - Validar `VolumeDownPlugin`:
     - Retorna `"Volumen al 30 por ciento."` si `volume_down()` devuelve `{"volume": 30, "muted": false}`.
     - Retorna `"Volumen al mínimo."` si `volume_down()` devuelve `{"volume": 0, "muted": false}`.
   - Validar `VolumeStatusPlugin`:
     - Retorna `"Volumen al 60 por ciento."` si el sonido no está silenciado.
     - Retorna `"Volumen al 60 por ciento y silenciado."` si el sonido está silenciado.
   - Validar `MutePlugin` y `UnmutePlugin`:
     - Retornan `"Hecho."` y `"Sonido activado."` respectivamente ante ejecuciones correctas.
   - Validar la captura de indisponibilidad y que se retorne `"Servicio no disponible."` con `success=False`.

### Pruebas de Registro (`tests/test_plugin_registration.py`)
* Modificar `test_successful_plugin_registration` para incluir aserciones de presencia de las capacidades `"volume-up"`, `"volume-down"`, `"volume-status"`, `"mute"` y `"unmute"` en el listado de registro del orquestador.

### Pruebas de Enrutamiento (`tests/test_routing.py`)
* Agregar los siguientes casos de prueba en la suite semántica:
  - `"Sube un poco el volumen"` -> `VolumeUpPlugin`
  - `"Ponlo más bajo"` -> `VolumeDownPlugin`
  - `"¿Qué volumen tengo?"` -> `VolumeStatusPlugin`
  - `"Silénciate"` -> `MutePlugin`
  - `"Activa el sonido"` -> `UnmutePlugin`

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Configuración del Cliente HTTP en Orchestrator**
  - [ ] Verificar que `httpx>=0.25.0` está declarado en [requirements.txt](file:///home/danuser2018/workspace/orchestrator/requirements.txt).
  - [ ] Modificar [core/config.py](file:///home/danuser2018/workspace/orchestrator/core/config.py) agregando la variable `host_service_base_url` a la clase `Settings`.
  - [ ] Crear el archivo [core/host_service_client.py](file:///home/danuser2018/workspace/orchestrator/core/host_service_client.py) e implementar el cliente `HostServiceClient` con las llamadas asíncronas descritas.
- [ ] **Fase 2: Codificación de Plugins en Orchestrator**
  - [ ] Crear el directorio `plugins/volume`.
  - [ ] Crear el archivo [plugins/volume/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/volume/main.py) y programar las clases de plugins de volumen y silencio.
- [ ] **Fase 3: Desarrollo de la Suite de Pruebas**
  - [ ] Crear el archivo [tests/test_volume_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_volume_plugin.py) con todos los tests unitarios.
  - [ ] Modificar [tests/test_plugin_registration.py](file:///home/danuser2018/workspace/orchestrator/tests/test_plugin_registration.py) añadiendo las aserciones de registro de capacidades de sonido.
  - [ ] Modificar [tests/test_routing.py](file:///home/danuser2018/workspace/orchestrator/tests/test_routing.py) con las aserciones de enrutamiento para los 5 nuevos plugins.
  - [ ] ✅ Validación: Ejecutar `PYTHONPATH=. pytest` en el Orchestrator para asegurar que el 100% de los tests pasen con éxito.
- [ ] **Fase 4: Integración del Ecosistema en Home Assistant**
  - [ ] Verificar que el servicio `orchestrator` en [docker-compose.yml](file:///home/danuser2018/workspace/home-assistant/docker-compose.yml) contiene la entrada `extra_hosts: ["host.docker.internal:host-gateway"]` (ya presente en el estado actual; debe conservarse al añadir `HOST_SERVICE_BASE_URL`).
  - [ ] Modificar [docker-compose.yml](file:///home/danuser2018/workspace/home-assistant/docker-compose.yml) añadiendo la variable `HOST_SERVICE_BASE_URL: http://host.docker.internal:8007` en el bloque `environment` del servicio `orchestrator`.
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) para reflejar las 5 nuevas capacidades registradas en el `system-service`.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) y [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) registrando el lanzamiento de la feature.
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) agregando los plugins en la sección de prioridades de enrutamiento y añadiendo `HOST_SERVICE_BASE_URL` a la tabla de variables de entorno.
