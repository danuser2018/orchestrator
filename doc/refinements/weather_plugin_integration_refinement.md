# Refinamiento de la Feature: Adaptación del Weather Plugin para consumir Weather Service

- **Archivo de origen**: [weather_plugin_implementation.md](file:///home/danuser2018/workspace/orchestrator/doc/features/weather_plugin_implementation.md)
- **Fecha**: 2026-07-05
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Modificar el `WeatherPlugin` para que obtenga la información meteorológica desde el `weather-service` en lugar de utilizar datos simulados.

Esta modificación permitirá ofrecer información meteorológica real al usuario sin alterar el contrato del plugin con el Orchestrator. La solución debe respetar los principios de mínima información y diseño directo de `TONE_GUIDE.md` y la gestión homogénea de errores indicada en el `ADR-002 (Orchestrator)`.

### Actores y Reglas de Negocio
1. **Usuario**: Realiza preguntas de lenguaje natural referentes al clima, el tiempo o la temperatura (ej. "¿Va a llover hoy?").
2. **Orchestrator**: Calcula la similitud semántica de la consulta del usuario y enruta la petición al `WeatherPlugin` tras ser la opción más cercana y superar el umbral mínimo de similitud.
3. **WeatherPlugin**: Inicializa su cliente HTTP asíncrono y consume la información en tiempo real desde el servicio local. Mapea la probabilidad de precipitación en una frase directa en español, redondea la temperatura a un número entero y genera el `PluginResult` estructurado.
4. **WeatherService**: Microservicio local que responde con la información estructurada de clima actual, abstrayendo al orquestador del proveedor externo Open-Meteo.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/config.py`: Añadir el parámetro de configuración `weather_service_base_url` en la clase `Settings` con valor por defecto `"http://weather-service:8000"`.  <br>- `core/weather_service_client.py` [NEW]: Crear el cliente HTTP asíncrono `WeatherServiceClient` y el modelo Pydantic `WeatherInfo` para manejar las peticiones a `weather-service` y encapsular excepciones de red.  <br>- `plugins/weather/main.py`: Modificar para inicializar el cliente, invocar `get_current_weather()`, redondear la temperatura, mapear la probabilidad de lluvia, formatear el texto según el Tone Guide y capturar excepciones de acuerdo con `ADR-002`.  <br>- `tests/test_weather_plugin.py` [NEW]: Agregar la suite de pruebas unitarias cubriendo escenarios exitosos con variaciones de temperatura y lluvia, y la correcta respuesta ante indisponibilidad, timeouts y fallos HTTP.  <br>- `README.md`: Actualizar la sección `15. Ejemplo completo: WeatherPlugin` para que muestre el código de producción integrado real.  <br>- `CHANGELOG.md`: Registrar en la sección `[Sin publicar]` la implementación real del plugin meteorológico con integración hacia el servicio. |
| `home-assistant` | Modificar | - `docker-compose.yml`: Definir inline la variable de entorno `WEATHER_SERVICE_BASE_URL: http://weather-service:8000` bajo el bloque `environment:` del servicio `orchestrator`.  <br>- `CHANGELOG.md`: Registrar la integración real del weather plugin de orchestrator con el weather-service local.  <br>- `docs/services.md`: Actualizar la respuesta de ejemplo del WeatherPlugin para alinearlo con el Tone Guide y la salida real. |
| Todos los demás servicios | Ninguno | Las interfaces HTTP REST públicas y el flujo síncrono del sistema asistente de voz no se ven afectados por este cambio. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
De acuerdo con las reglas de `architecture-decisions`, no es necesaria la creación de un nuevo ADR. El contrato de red asíncrono y local ya fue sancionado y aceptado previamente en el `ADR-011` del ecosistema, y la política de formateo de errores y respuestas textuales ya está establecida por el `ADR-002 (Orchestrator)` y la guía `TONE_GUIDE.md`.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Consulta del clima exitosa con baja probabilidad de lluvia
```gherkin
Dado que el servicio weather-service responde con HTTP 200 y el JSON {"temperature": 27.4, "precipitation_probability": 10}
Cuando el usuario pregunta "¿Qué tiempo hace?" y el Orchestrator enruta la petición a WeatherPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "27 grados. No parece que vaya a llover."
Y el JSON de data contiene "temperature": 27.4 y "precipitation_probability": 10
```

### Escenario 2: Consulta del clima exitosa con alta probabilidad de lluvia
```gherkin
Dado que el servicio weather-service responde con HTTP 200 y el JSON {"temperature": 18.6, "precipitation_probability": 75}
Cuando el usuario pregunta "¿Va a llover hoy?" y el Orchestrator enruta la petición a WeatherPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "19 grados. Es probable que llueva."
Y el JSON de data contiene "temperature": 18.6 y "precipitation_probability": 75
```

### Escenario 3: Indisponibilidad de conexión con el servicio meteorológico
```gherkin
Dado que el contenedor weather-service no está disponible en la red o la petición tiene timeout
Cuando el usuario solicita información sobre el clima
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "Servicio no disponible."
```

### Escenario 4: Respuesta de error por parte del servicio meteorológico
```gherkin
Dado que el servicio weather-service responde con un código de error HTTP 500 o 503
Cuando el usuario solicita información sobre el clima
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

---

## 4. Diseño Técnico y Contratos

### Parámetros de Configuración y Despliegue (`core/config.py` y `docker-compose.yml`)
Se incorpora a la clase de configuración `Settings` el parámetro `weather_service_base_url` para aislar el direccionamiento:

```python
class Settings(BaseSettings):
    # ... other configurations ...
    weather_service_base_url: str = "http://weather-service:8000"
```

En el archivo de despliegue `docker-compose.yml` del ecosistema se declara la variable de infraestructura inline bajo la sección `environment:` de `orchestrator`:
```yaml
  orchestrator:
    # ...
    environment:
      SYSTEM_SERVICE_BASE_URL: http://system-service:8000
      MAIL_PENDING_DIR: /shared/mail/pending
      WEATHER_SERVICE_BASE_URL: http://weather-service:8000
```

### Contrato del Cliente Meteorológico (`core/weather_service_client.py`)
```python
import httpx
import logging
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class WeatherInfo(BaseModel):
    temperature: float
    precipitation_probability: int

class WeatherServiceClient:
    def __init__(self, base_url: str = None):
        from core.config import settings
        self.base_url = base_url or settings.weather_service_base_url

    async def get_current_weather(self) -> WeatherInfo:
        url = f"{self.base_url.rstrip('/')}/v1/weather/current"
        logger.info(f"Consuming URL: {url}")
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            logger.info(f"Response received: {data}")
            return WeatherInfo(**data)
```

### Contrato e Implementación del Plugin Clima (`plugins/weather/main.py`)
```python
import logging
import httpx
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.weather_service_client import WeatherServiceClient

logger = logging.getLogger(__name__)

class WeatherPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "WeatherPlugin"

    @property
    def description(self) -> str:
        return "Responde consultas sobre el tiempo y el clima."

    @property
    def id(self) -> str:
        return "weather"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> list[str]:
        return [
            "¿Qué tiempo hace?",
            "¿Qué tiempo hará mañana?",
            "¿Va a llover hoy?",
            "¿Qué temperatura hay?",
            "¿Cómo está el tiempo?",
            "Dime el pronóstico del tiempo.",
            "¿Va a hacer calor hoy?",
            "¿Necesito paraguas?",
            "¿Qué clima hace?",
            "¿Cómo estará el tiempo esta tarde?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing WeatherPlugin")
        self.client = WeatherServiceClient()

    def _get_precipitation_msg(self, probability: int) -> str:
        if probability <= 20:
            return "No parece que vaya a llover."
        elif probability <= 40:
            return "Hay poca probabilidad de lluvia."
        elif probability <= 60:
            return "Podría llover."
        elif probability <= 80:
            return "Es probable que llueva."
        else:
            return "Es muy probable que llueva."

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of WeatherPlugin")
        try:
            try:
                weather_info = await self.client.get_current_weather()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to Weather Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving weather info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving weather info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            rounded_temp = int(round(weather_info.temperature))
            precip_msg = self._get_precipitation_msg(weather_info.precipitation_probability)
            speech = f"{rounded_temp} grados. {precip_msg}"

            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "temperature": weather_info.temperature,
                    "precipitation_probability": weather_info.precipitation_probability
                }
            )

        except Exception as e:
            logger.error(f"Unexpected exception in WeatherPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Pérdida de Conexión o Timeout** | Retornar una respuesta estructurada controlada con `"Servicio no disponible."` y éxito en falso. | Capturar `httpx.ConnectError` y `httpx.TimeoutException` durante la llamada a red en el método `execute` del plugin. |
| **Respuesta con código de error HTTP (ej. 500, 503)** | Retornar una respuesta controlada con `"No he podido obtener la información."`. | `httpx.AsyncClient` con invocación de `response.raise_for_status()`, capturando `httpx.HTTPError` en la lógica del plugin. |
| **Respuesta JSON malformada o incompleta** | Evitar la caída del servicio y retornar `"No he podido obtener la información."`. | El constructor `WeatherInfo(**data)` validará los tipos de datos en la deserialización. Si arroja una excepción `ValidationError`, se captura en el bloque `except Exception` general retornando el error de información genérico. |
| **Probabilidades fuera del rango 0-100** | Mantener la robustez del mapeo y evitar errores de índice. | El método `_get_precipitation_msg` utiliza rangos secuenciales y una cláusula `else` por defecto para cualquier valor superior a 80, garantizando que siempre se devuelva un string válido. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias (`tests/test_weather_plugin.py`)
1. **Verificación de éxito y traducción de lluvia baja**: Mockear respuesta exitosa (`temperature=27.4`, `precipitation_probability=15`) y asegurar que se redondea a `27` y la frase es `"No parece que vaya a llover."`.
2. **Verificación de éxito y traducción de lluvia media/alta**: Mockear respuesta exitosa (`temperature=18.6`, `precipitation_probability=75`) y asegurar que se redondea a `19` y la frase es `"Es probable que llueva."`.
3. **Verificación de error de conexión**: Mockear lanzamiento de `httpx.ConnectError` y verificar que la respuesta de voz es `"Servicio no disponible."` con `success=False`.
4. **Verificación de error de timeout**: Mockear lanzamiento de `httpx.TimeoutException` y verificar que la respuesta de voz es `"Servicio no disponible."` con `success=False`.
5. **Verificación de error HTTP / Servidor interno**: Mockear lanzamiento de `httpx.HTTPStatusError` y verificar que la respuesta de voz es `"No he podido obtener la información."` con `success=False`.
6. **Verificación de metadatos y propiedades**: Comprobar que `plugin.id == "weather"`, `plugin.priority == 80` y la lista de `examples` no está vacía.

### Verificación local
La verificación se realizará ejecutando en la terminal:
```bash
PYTHONPATH=. pytest tests/test_weather_plugin.py
PYTHONPATH=. pytest
```
Asegurando que todos los tests antiguos y nuevos finalizan satisfactoriamente sin advertencias críticas de regresión.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Configuración de Config y Creación de Cliente en Orchestrator**
  - [ ] Modificar [core/config.py](file:///home/danuser2018/workspace/orchestrator/core/config.py) para añadir `weather_service_base_url` a la clase `Settings`.
  - [ ] Crear el nuevo archivo [core/weather_service_client.py](file:///home/danuser2018/workspace/orchestrator/core/weather_service_client.py) conteniendo la clase `WeatherServiceClient` y el modelo `WeatherInfo`.
- [ ] **Fase 2: Integración de la API en el Weather Plugin**
  - [ ] Modificar [plugins/weather/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/weather/main.py) reemplazando la lógica mockeada de simulación por la llamada real asíncrona a través de `WeatherServiceClient`.
  - [ ] Implementar la función de traducción de probabilidades de lluvia a texto y el redondeo correcto de la temperatura a entero.
  - [ ] Incluir bloques de control de excepciones asíncronas para retornar `"Servicio no disponible."` o `"No he podido obtener la información."` de acuerdo al `ADR-002`.
- [ ] **Fase 3: Desarrollo de Suite de Tests Unitarios**
  - [ ] Crear el archivo de pruebas [tests/test_weather_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_weather_plugin.py) con todos los casos de prueba de integración de red mockeados (éxito, ConnectError, Timeout, HTTPError, propiedades).
  - [ ] Ejecutar localmente `PYTHONPATH=. pytest` para validar la suite.
- [ ] **Fase 4: Configuración de Entornos y Documentación**
  - [ ] Modificar [docker-compose.yml](file:///home/danuser2018/workspace/home-assistant/docker-compose.yml) en `home-assistant` para agregar la variable `WEATHER_SERVICE_BASE_URL` de forma inline bajo la sección `environment:` del servicio `orchestrator`.
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en `orchestrator` para actualizar el código de ejemplo del `WeatherPlugin` en la sección 15.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) en `orchestrator` para registrar la adición de `weather_service_client.py` y la integración real.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) en `home-assistant` para dejar constancia de la integración del plugin con el microservicio.
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en `home-assistant` para actualizar la respuesta de ejemplo en la línea 239.
- [ ] **Fase 5: Validación General del Ecosistema**
  - [ ] Validar el correcto arranque de la pila de servicios en docker localizando el nuevo parámetro.
