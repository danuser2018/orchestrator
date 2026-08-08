# Orchestrator - Especificación Técnica

## 1. Visión general
El **Orchestrator** es el componente central de un asistente de voz personal que se ejecuta localmente en Linux. Su propósito principal es recibir texto interpretado por un servicio de *Speech-to-Text* (STT), procesarlo seleccionando y ejecutando la habilidad adecuada (plugin), y generar una respuesta textual plana. Esta respuesta será consumida posteriormente por un servicio *Text-to-Speech* (TTS) para ser reproducida por los altavoces. Se prioriza un diseño extremadamente rápido, de bajo consumo de recursos y determinista.

## 2. Responsabilidades

**El Orchestrator HACE:**
- Recibir texto plano del usuario a través de una API REST.
- Mantener y gestionar el ciclo de vida de un ecosistema de plugins dinámicos.
- Seleccionar el plugin más adecuado para atender una petición usando coincidencia por similitud semántica determinista y desempate por prioridades.
- Ejecutar el plugin seleccionado.
- Recibir un resultado estructurado del plugin y extraer el texto que el asistente debe "pronunciar".
- Devolver la respuesta al sistema solicitante.
- Publicar automáticamente la lista completa de capacidades disponibles (plugins) en el servicio `system-service` durante el arranque (operación idempotente).

**El Orchestrator NO HACE:**
- Captura de audio del micrófono o reproducción de audio.
- Inferencia de *Speech-to-Text* (STT).
- Síntesis de voz *Text-to-Speech* (TTS).
- Uso de Large Language Models (LLMs) para decidir qué plugin ejecutar o para redactar la respuesta. Las respuestas son deterministas y preprogramadas por los plugins.

## 3. Arquitectura interna

La arquitectura se divide en los siguientes componentes principales:

- **API Layer**: Construida sobre FastAPI, expone los endpoints HTTP necesarios para interactuar con el Orchestrator.
- **ExecutionPlanner**: Motor de planificación rápido que analiza la entrada de texto y calcula la similitud semántica ponderada frente a las frases de ejemplo de cada plugin cargado para construir un plan de ejecución (`ExecutionPlan`).
- **ParameterResolverEngine / Registry**: Capa contractual desacoplada (`core/parameter_resolution/`) que coordina la extracción y resolución de parámetros declarados por los plugins según su tipo lógico, integrada en la fase de planificación del `ExecutionPlanner`.
- **Plugin Manager**: Encargado de descubrir, cargar dinámicamente, registrar y mantener en memoria las instancias de los plugins disponibles. Tras cargar todos los plugins, se asiste el proceso de recopilación para la posterior publicación de las capacidades en `system-service`.

- **PlanExecutor**: Transforma un plan de ejecución (`ExecutionPlan`) en una serie de llamadas secuenciales a los plugins indicados y emite el resultado estructurado (`AssistantResponse`) que devolverá la API al servicio consumidor.
- **Configuration**: Gestor centralizado para la configuración del Orchestrator y de cada plugin, usando variables de entorno o archivos `.env`.
- **Logging**: Sistema unificado de observabilidad para trazar el flujo completo de la petición, esencial para depurar la selección de plugins y la ejecución.

## 4. El ciclo de vida de una petición sigue un flujo desacoplado en dos fases independientes:

### Fase 1: Planificación (Resolve)
```text
+-------------+         +-----------+        +------------------+        +----------------+
| IM Client   |         | API Layer |        | ExecutionPlanner |        | Plugin Manager |
+-------------+         +-----------+        +------------------+        +----------------+
       |                      |                       |                           |
       | POST /api/v1/resolve |                       |                           |
       | {"text": "..."}      |                       |                           |
       |--------------------->|                       |                           |
       |                      | resolve()             |                           |
       |                      |---------------------->|                           |
       |                      |                       | get_active_plugins()      |
       |                      |                       |-------------------------->|
       |                      |                       |                           |
       |                      |                       | [Plugins...]              |
       |                      |                       |<--------------------------|
       |                      |                       |                           |
       |                      |                       | Calcular similitud        |
       |                      |                       |-----------------+         |
       |                      |                       |                 |         |
       |                      |                       |<----------------+         |
       |                      |                       |                           |
       |                      | ExecutionPlan         |                           |
       |                      |<----------------------|                           |
       | ExecutionPlan        |                       |                           |
       |<---------------------|                       |                           |
```

### Fase 2: Ejecución (Execute Plan)
```text
+-------------+         +-----------+        +--------------+        +---------------+
| IM Client   |         | API Layer |        | PlanExecutor |        | WeatherPlugin |
+-------------+         +-----------+        +--------------+        +---------------+
       |                      |                     |                        |
       | POST /execute-plan   |                     |                        |
       | (ExecutionPlan)      |                     |                        |
       |--------------------->|                     |                        |
       |                      | execute_plan()      |                        |
       |                      |-------------------->|                        |
       |                      |                     | execute(Context)       |
       |                      |                     |----------------------->|
       |                      |                     |                        |
       |                      |                     |   Obtener clima        |
       |                      |                     |   ------------------+  |
       |                      |                     |                     |  |
       |                      |                     |   <-----------------+  |
       |                      |                     |                        |
       |                      |                     | PluginResult           |
       |                      |                     |<-----------------------|
       |                      |                     |                        |
       | AssistantResponse    |                     |                        |
       |<---------------------|                     |                        |
```

## 5. Sistema de plugins

El sistema de plugins está diseñado para ser totalmente modular y desacoplado del núcleo.

- **Descubrimiento y Carga Dinámica**: En el arranque, el `Plugin Manager` escanea el directorio `plugins/` buscando clases que hereden de la interfaz base `Plugin`. Utiliza el módulo `importlib` de Python para cargarlos de forma dinámica sin necesidad de importaciones estáticas (hardcoded) en el Orchestrator.
- **Registro**: Al cargarse, cada plugin se instancia y se registra en la memoria del `Plugin Manager`, exponiendo sus metadatos (nombre, frases de ejemplo y prioridad).
- **Ciclo de vida**:
  1. `Initialize`: Se ejecuta una vez al arrancar (carga configuración local, inicializa clientes).
  2. `Match/Score`: El `PluginMatcher` calcula la similitud semántica entre el texto del usuario y las frases de ejemplo de cada plugin mediante `rapidfuzz`, aplicando desempate por prioridad.
  3. `Execute`: Invocado solo si el plugin es seleccionado.
  4. `Teardown`: Invocado al apagar el servicio para liberar recursos.

## 6. Estrategia de selección de plugins

La selección se realiza mediante un sistema de **Similitud Semántica Determinista** basado en algoritmos de distancia de edición (`rapidfuzz`). 

Cada plugin funcional declara:
- **Examples**: Lista de frases de ejemplo naturales que activan la habilidad.
- **Priority**: Nivel de prioridad (0 a 100) usado para resolver empates y situaciones de ambigüedad.

**Cálculo de la puntuación:**
1. El `ExecutionPlanner` normaliza el texto de entrada y cada frase de ejemplo (minúsculas, eliminar signos diacríticos y de puntuación).
2. Para cada plugin, calcula la similitud combinada entre el texto del usuario y cada frase de ejemplo utilizando cuatro métricas de `rapidfuzz` ponderadas:
   - `ratio` (peso: 0.20)
   - `partial_ratio` (peso: 0.30)
   - `token_sort_ratio` (peso: 0.20)
   - `token_set_ratio` (peso: 0.30)
3. La puntuación final del plugin es la máxima obtenida entre todas sus frases de ejemplo.
4. Si la puntuación más alta no supera el umbral mínimo configurado (`similarity_threshold`, por defecto `60.0`), se deriva al `FallbackPlugin`.
5. Si la diferencia de puntuación entre los dos mejores candidatos es menor que un umbral (`tie_breaker_threshold`, por defecto `5.0`), se resuelve el empate mediante la prioridad:
   - Si un plugin tiene mayor prioridad que el otro, se selecciona.
   - Si tienen la misma prioridad, se considera un empate persistente no resoluble y se deriva al `FallbackPlugin`.

**Tabla de Prioridades de los Plugins del Sistema:**

| Clase de Plugin | `id` | `priority` | `examples` |
| :--- | :--- | :--- | :--- |
| `GreetingPlugin` | `"greeting"` | `100` | Lista de 10 frases |
| `FarewellPlugin` | `"farewell"` | `100` | Lista de 10 frases |
| `TimePlugin` | `"time"` | `80` | Lista de 10 frases |
| `DatePlugin` | `"date"` | `80` | Lista de 10 frases |
| `WeatherPlugin` | `"weather"` | `80` | Lista de 10 frases |
| `RepeatPlugin` | `"repeat"` | `70` | Lista de 8 frases |
| `IdentityPlugin` | `"identity"` | `60` | Lista de 10 frases |
| `AuthorPlugin` | `"author"` | `60` | Lista de 10 frases |
| `VersionPlugin` | `"version"` | `60` | Lista de 10 frases |
| `HelpPlugin` | `"help"` | `60` | Lista de 10 frases |
| `CapabilitiesPlugin`| `"capabilities"` | `60` | Lista de 10 frases |
| `CoinPlugin` | `"coin"` | `60` | Lista de 10 frases |
| `DicePlugin` | `"dice"` | `60` | Lista de 10 frases |
| `RandomNumberPlugin`| `"random-number"` | `60` | Lista de 10 frases |
| `VolumeUpPlugin` | `"volume-up"` | `60` | Lista de 10 frases |
| `VolumeDownPlugin` | `"volume-down"` | `60` | Lista de 10 frases |
| `VolumeStatusPlugin`| `"volume-status"` | `60` | Lista de 10 frases |
| `MutePlugin` | `"mute"` | `60` | Lista de 10 frases |
| `UnmutePlugin` | `"unmute"` | `60` | Lista de 10 frases |
| `TodayHolidayPlugin` | `"today_holiday"` | `60` | Lista de 10 frases |
| `NextHolidayPlugin` | `"next_holiday"` | `60` | Lista de 10 frases |
| `DaysUntilNextHolidayPlugin`| `"days_until_next_holiday"`| `60` | Lista de 10 frases |
| `HolidaysOfYearPlugin`| `"holidays_of_year"`| `60` | Lista de 10 frases |
| `FallbackPlugin` | `"fallback"` | `0` | `[]` |

**Directrices para Desarrolladores (Asignación de Prioridades):**

Al asignar prioridades a nuevos plugins, se deben seguir estas directrices:
1. **Prioridad Muy Alta (100)**: Reservada para intenciones conversacionales inmediatas y críticas de inicio/fin (saludos, despedidas, emergencias).
2. **Prioridad Alta (80)**: Plugins con un dominio de negocio claro y dependencias bien acotadas (clima, control de domótica).
3. **Prioridad Media (60 - valor por defecto)**: Comportamiento conversacional estándar del asistente (información personal, capacidades, etc.).
4. **Prioridad Baja (< 60)**: Plugins genéricos o experimentales que no deben entorpecer los flujos primarios.
5. **Fallback (0)**: Reservada exclusivamente para el plugin por defecto en caso de no coincidencia.

## 7. Contratos

Interfaces base definidas en Python utilizando Pydantic y abc:

```python
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class PluginContext(BaseModel):
    raw_text: str
    normalized_text: str
    metadata: Dict[str, Any] = {}

class PluginResult(BaseModel):
    success: bool
    speech: str
    data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique snake_case identifier for the plugin."""
        pass

    @property
    def priority(self) -> int:
        """Priority level of the plugin (0 to 100). Default is 60 (Medium)."""
        return 60

    @property
    def examples(self) -> List[str]:
        """Collection of natural language example phrases to trigger this plugin."""
        return []

    def initialize(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
```

Construida con FastAPI, proporciona endpoints desacoplados para planificar y ejecutar de manera independiente.

**Endpoints Principales:**

### 1. Resolver Intención
`POST /api/v1/resolve`

Genera un plan de ejecución estructurado a partir del texto del usuario.

**Request Example:**
```json
{
  "text": "¿Qué tiempo hace?"
}
```

**Response Example:**
```json
{
  "steps": [
    {
      "plugin": "WeatherPlugin",
      "confidence": 100.0,
      "parameters": {},
      "channel": "voice",
      "context": {
        "raw_text": "¿Qué tiempo hace?",
        "normalized_text": "que tiempo hace",
        "metadata": {}
      },
      "security": {}
    }
  ]
}
```

### 2. Ejecutar Plan
`POST /api/v1/execute-plan`

Ejecuta el plan estructurado resuelto previamente y produce la respuesta para el usuario.

**Request Example:**
```json
{
  "steps": [
    {
      "plugin": "WeatherPlugin",
      "confidence": 100.0,
      "parameters": {},
      "channel": "voice",
      "context": {
        "raw_text": "¿Qué tiempo hace?",
        "normalized_text": "que tiempo hace",
        "metadata": {}
      },
      "security": {}
    }
  ]
}
```

**Response Example:**
```json
{
  "success": true,
  "plugin_used": "WeatherPlugin",
  "speech": "22 grados. No parece que vaya a llover.",
  "execution_time_ms": 15
}
```

## 9. Modelo de datos

Definición de entidades (Modelos Pydantic):

- **UserRequest**: La entrada al sistema.
  - `text` (str): Texto interpretado.
  - `timestamp` (float, opcional): Marca de tiempo.
  - `correlation_id` (str, opcional): Identificador único para el rastreo e2e.
  - `channel` (str, opcional, por defecto "voice"): Canal de entrada.
- **PluginContext**: La información que recibe el plugin a ejecutar.
  - `raw_text` (str): El texto original.
  - `normalized_text` (str): Texto en minúsculas y sin acentos.
  - `correlation_id` (str, opcional): ID de correlación único.
  - `channel` (str, opcional, por defecto "voice"): Canal de origen.
  - `metadata` (dict): Posible estado de sesión futuro.
- **PluginResult**: Lo que devuelve el plugin.
  - `success` (bool): Éxito o fracaso de la tarea.
  - `speech` (str): Texto literal que el TTS deberá pronunciar.
  - `data` (dict): Metadatos adicionales para debug (ej. `{"application": "Firefox"}`).
- **AssistantResponse**: La salida final del Orchestrator.
  - `speech` (str): Extraído del `PluginResult`.
  - `plugin_used` (str): Quién resolvió la petición.

## 10. Gestión de errores

- **Errores Recuperables / Errores de Dominio**: El plugin se ejecuta pero no puede completar la acción (ej. API del tiempo caída). El plugin devuelve un `PluginResult(success=False, speech="No he podido consultar el tiempo porque el servidor no responde")`. El sistema sigue funcionando normalmente.
- **Errores de Selección**: Si ningún plugin llega a la puntuación mínima, actúa el *FallbackPlugin* devolviendo una respuesta genérica.
- **Errores No Recuperables (Excepciones No Capturadas)**: Si un plugin lanza una excepción, el `ResponseHandler` la captura en un bloque `try/except` general, hace un log del traceback completo (para no tumbar el servidor FastAPI), y devuelve un `AssistantResponse` de error al usuario: "Ha ocurrido un error interno al ejecutar la acción."

## 11. Estructura de directorios

```text
orchestrator/
├── core/
│   ├── api.py                # Endpoints FastAPI
│   ├── config.py             # Configuración global
│   ├── datetime_service.py   # Utilidad de fecha/hora del sistema (helper)
│   ├── engine.py             # Planificador (ExecutionPlanner) y Ejecutor (PlanExecutor)
│   ├── logger.py             # Configuración de logs
│   ├── models.py             # Definición de Pydantic models (UserRequest, etc)
│   ├── plugin_manager.py     # Lógica de descubrimiento de plugins
│   ├── random_service.py     # Utilidad de generación aleatoria (helper)
│   ├── similarity.py         # Motor de similitud semántica (RapidFuzz)
│   ├── system_service_client.py # Cliente HTTP para system-service
│   ├── weather_service_client.py # Cliente HTTP para weather-service
│   ├── host_service_client.py # Cliente HTTP para host-service
│   ├── calendar_service_client.py # Cliente HTTP y lógica de negocio para calendar-service
│   └── time_formatter.py     # Utilidad para formatear tiempos en lenguaje natural
├── plugins/
│   ├── base.py          # Definición de las interfaces abstractas (Plugin, etc)
│   ├── capabilities/    # Plugin de capacidades
│   │   ├── main.py      # Clase del plugin
│   │   └── requirements.txt # Dependencias opcionales
│   ├── datetime/        # Plugins de fecha y hora
│   │   └── main.py      # Clases TimePlugin y DatePlugin
│   ├── fallback/        # Plugin por defecto
│   │   └── main.py      # Clase del plugin
│   ├── farewell/        # Plugin de despedida
│   │   └── main.py      # Clase del plugin
│   ├── greeting/        # Plugin de saludo
│   │   └── main.py      # Clase del plugin
│   ├── identity/        # Plugins de identidad, autoría y versión
│   │   ├── main.py      # Clases IdentityPlugin, AuthorPlugin, VersionPlugin, HelpPlugin
│   │   └── requirements.txt # Dependencias opcionales
│   ├── random/          # Plugins aleatorios (moneda, dado, número)
│   │   └── main.py      # Clases CoinPlugin, DicePlugin, RandomNumberPlugin
│   ├── volume/          # Plugins de volumen (subir, bajar, estado, silenciar, activar sonido)
│   │   └── main.py      # Clases VolumeUpPlugin, VolumeDownPlugin, VolumeStatusPlugin, MutePlugin, UnmutePlugin
│   ├── weather/         # Plugin del tiempo
│   │   └── main.py      # Clase del plugin
│   └── holidays/        # Plugins de festivos (hoy, siguiente, días restantes, año completo)
│       └── main.py      # Clases TodayHolidayPlugin, NextHolidayPlugin, DaysUntilNextHolidayPlugin, HolidaysOfYearPlugin
├── main.py              # Punto de entrada (uvicorn)
├── requirements.txt     # Dependencias del núcleo (fastapi, pydantic, etc)
├── Dockerfile
└── README.md
```

## 12. Observabilidad

El sistema incorpora *structured logging* (usando librerías como `logging` estándar configurada o `loguru`).
- **Nivel INFO**: Cada petición que entra, texto normalizado, qué plugin fue seleccionado, score ganador y tiempo total de ejecución.
- **Nivel DEBUG**: Puntuación desglosada por cada plugin (muy útil para depurar el ExecutionPlanner).
- **Nivel ERROR**: Excepciones capturadas y tiempos de inactividad de las APIs en los plugins.

*Trazabilidad:* Para rastrear el flujo, se puede añadir un `request_id` único a cada petición en el momento que cruza el `API Layer`.

## 13. Extensibilidad

Añadir una nueva capacidad es trivial y **no requiere modificar el núcleo**:
1. Crear una carpeta nueva en `plugins/` (ej. `plugins/spotify/`).
2. Crear un archivo que contenga una clase que herede de `Plugin`.
3. Implementar las propiedades obligatorias (`name`, `description`, `id`) y declarar las frases de ejemplo naturales en `examples` (y opcionalmente el nivel de `priority`) para que el `PluginMatcher` pueda seleccionarlo. Implementar el método `execute()`.
4. Al reiniciar el Orchestrator, el `Plugin Manager` encontrará el nuevo archivo automáticamente y el router lo tendrá en cuenta en el scoring de la siguiente petición.
5. Durante el arranque del Orchestrator, la nueva capacidad se publicará automáticamente en el `system-service` sin necesidad de modificar ningún otro componente.

## 14. Instalación

El servicio está empaquetado en contenedores para garantizar que sea independiente del sistema host.

**Prerrequisitos:** `docker` y `docker-compose`.

**Construir y ejecutar:**
```bash
docker build -t voice-orchestrator .
docker run -d -p 8000:8000 --name orchestrator voice-orchestrator
```

**Con Docker Compose (Recomendado):**
```yaml
# docker-compose.yml
version: '3.8'
services:
  orchestrator:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./plugins:/app/plugins  # Para desarrollo de plugins en caliente
    env_file:
      - .env
```

## 15. Ejemplo completo: WeatherPlugin

**`plugins/weather/main.py`**
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

**Flujo:**
1. Usuario dice: *"Dime qué tiempo hace, por favor."*
2. Texto normalizado: *"dime que tiempo hace por favor"*
3. ExecutionPlanner evalúa `WeatherPlugin` frente a sus frases de ejemplo (ej. *"¿Qué tiempo hace?"*).
4. El score calculado mediante la ponderación de RapidFuzz es superior a `60.0` (por ejemplo, `78.50`).
5. Al ser la puntuación más alta y superar el umbral, gana `WeatherPlugin` y se invoca su plan mediante PlanExecutor.
6. Se devuelve: `{"speech": "Actualmente hace 22 grados. No parece que vaya a llover."}`

## 16. Recomendación final

**Evaluación crítica:**
La arquitectura propuesta destaca por su enorme velocidad, facilidad de despliegue y bajísimo consumo de recursos. Al evitar LLMs para la lógica y selección, el sistema es predecible e ideal para una Raspberry Pi o un servidor casero modesto.

**Posibles problemas futuros:**
- **Mantenimiento del motor de Scoring**: A medida que crezcan los plugins, las palabras clave pueden solaparse. (Ej: "¿Cuánto tiempo falta para mi alarma?" tiene "tiempo", pero es para alarmas, no clima).
- **Gestión de estado/sesión**: Esta versión es puramente transaccional (stateless). No permite conversaciones multi-turno ("Dime el tiempo en Madrid" -> "Y en Barcelona?").
- **Aislamiento de dependencias**: Si dos plugins requieren versiones diferentes de la misma librería externa, Python podría tener problemas de conflictos de dependencias, dado que se cargan en el mismo intérprete.

**Mejoras evolutivas manteniendo la simplicidad:**
1. **Scoring Jerárquico/Entidades**: En lugar de solo Regex planas, usar una librería ligera como *spaCy* o *Snips NLU* (solo modelos locales pequeños) para extraer "intenciones" y "entidades" de forma más inteligente que el puro regex, sin la pesadez de un LLM.
2. **Sistema de prioridades estricto**: Si un plugin choca con otro, definir en configuración quién tiene prioridad.
3. **Paso a procesos aislados (gRPC / Subprocess)**: Si los conflictos de dependencias entre plugins se vuelven inmanejables, migrar el Plugin Manager para que lance cada plugin en su propio proceso independiente, comunicándose por sockets (ZeroMQ o IPC).

## 17. Integración con System Service y Otros Componentes

El Orchestrator se integra con el microservicio central `system-service` y otros componentes para los siguientes propósitos principales:

1. **Consulta de Identidad (`GET /system/info`)**: Consumido por `IdentityPlugin`, `AuthorPlugin` y `VersionPlugin` para conocer la información básica del sistema (nombre, versión, autor, etc.) y responder preguntas de identidad, autoría y versión de forma dinámica al usuario.
2. **Registro Automático de Capacidades (`POST /system/capabilities`)**: Ejecutado exactamente una vez durante el arranque del Orchestrator.
3. **Consulta de Capacidades (`GET /system/capabilities`)**: Consumido por el `CapabilitiesPlugin` para listar todas las habilidades registradas en el sistema.
4. **Consulta de Festivos (`GET /api/v1/holidays` y `GET /api/v1/holidays/next`)**: Consumido por los plugins de festivos (`TodayHolidayPlugin`, `NextHolidayPlugin`, `DaysUntilNextHolidayPlugin`, `HolidaysOfYearPlugin`) para validar el estado de festivos locales, nacionales y regionales.

### Publicación de Capacidades en el Arranque

Al arrancar, el Orchestrator ejecuta los siguientes pasos:
1. Escanea y carga todos los plugins del directorio `plugins/`.
2. Para cada plugin registrado, construye un descriptor público simplificado que contiene:
   - `id`: Identificador único del plugin, declarado mediante la propiedad nativa `plugin.id` (ej. `"weather"`).
   - `description`: Breve descripción pública sobre lo que hace la habilidad.
3. Envía la lista de capacidades mediante una petición `POST /system/capabilities` a `system-service`.

### Publicación de Eventos del Dominio (ResponseGeneratedEvent)

El Orchestrator se integra con el bus de eventos asíncrono utilizando la librería `nova-event-bus` (conectada al broker NATS mediante la variable `NATS_URL`).
Cuando el `PlanExecutor` finaliza la ejecución de un plan de plugin de forma exitosa, publica de manera asíncrona un evento de tipo `ResponseGeneratedEvent` bajo el subject `event.interaction.response-generated`.

El payload del evento incluye:
- `response` (str): Texto de la respuesta generada para el usuario.
- `plugin` (str): ID del plugin que resolvió la petición.
- `confidence` (float): Puntuación de confianza obtenida durante la resolución del plugin.
- `timestamp` (datetime): Fecha y hora del evento en UTC.
- `correlation_id` (str): Identificador único de correlación para trazar la petición de extremo a extremo.
- `execution_time_ms` (int): Tiempo en milisegundos que tomó procesar la petición.
- `channel` (str): Canal de comunicación (ej. `"voice"`).
- `metadata` (dict): Metadatos adicionales de la sesión.

El envío del evento se realiza de manera no bloqueante. En caso de fallo de conexión con el broker NATS o error en el bus de eventos, la excepción es capturada y logueada, permitiendo al Orchestrator responder exitosamente al cliente a través de la API REST sin interrupción de su ciclo de vida.

### Integración con Mail Watchdog (CapabilitiesPlugin)

El `CapabilitiesPlugin` permite al usuario consultar las funciones que Nova puede realizar. La lógica incluye:
1. Consultar a `system-service` las capacidades activas con `GET /system/capabilities`.
2. Ordenarlas alfabéticamente por su descripción.
3. Generar un artefacto JSON compatible con el contrato de `mail-watchdog` y guardarlo en el directorio de salida (outbox) `MAIL_PENDING_DIR` (por defecto `/shared/mail/pending`).
4. `mail-watchdog` procesa este directorio asíncronamente y envía el email al usuario.

### Configuración

La comunicación y comportamiento del Orchestrator y sus plugins se configuran mediante las siguientes variables de entorno:
- `SYSTEM_SERVICE_BASE_URL` (por defecto `http://system-service:8000`): Dirección base del System Service.
- `HOST_SERVICE_BASE_URL` (por defecto `http://host.docker.internal:8007`): Dirección base del Host Service (capa HAL).
- `MAIL_PENDING_DIR` (por defecto `/shared/mail/pending`): Directorio donde se escriben los correos pendientes para que los procese `mail-watchdog`.
- `CALENDAR_SERVICE_BASE_URL` (por defecto `http://calendar-service:8000`): Dirección base del servicio de calendario offline.
- `SIMILARITY_THRESHOLD` (por defecto `60.0`): Umbral mínimo de similitud requerido para activar un plugin.
- `TIE_BREAKER_THRESHOLD` (por defecto `5.0`): Umbral de diferencia de puntuación para resolver ambigüedades.
- `WEIGHT_RATIO` (por defecto `0.20`), `WEIGHT_PARTIAL_RATIO` (por defecto `0.30`), `WEIGHT_TOKEN_SORT_RATIO` (por defecto `0.20`), `WEIGHT_TOKEN_SET_RATIO` (por defecto `0.30`): Pesos de los algoritmos de similitud (su suma debe ser exactamente 1.0).
- `NATS_URL` (por defecto `nats://nats:4222`): Dirección del servidor de mensajería NATS.

### Robustez y Manejo de Errores

El proceso de registro de capacidades está diseñado para no interrumpir el ciclo de vida del Orchestrator. Si la llamada de registro falla (por error de red, respuesta HTTP errónea o timeout), el Orchestrator:
- Registra una advertencia (`WARNING`) en sus logs (o `ERROR` para fallos inesperados).
- Continúa el arranque normalmente y queda completamente operativo para atender peticiones.

