# Orchestrator - Especificación Técnica

## 1. Visión general
El **Orchestrator** es el componente central de un asistente de voz personal que se ejecuta localmente en Linux. Su propósito principal es recibir texto interpretado por un servicio de *Speech-to-Text* (STT), procesarlo seleccionando y ejecutando la habilidad adecuada (plugin), y generar una respuesta textual plana. Esta respuesta será consumida posteriormente por un servicio *Text-to-Speech* (TTS) para ser reproducida por los altavoces. Se prioriza un diseño extremadamente rápido, de bajo consumo de recursos y determinista.

## 2. Responsabilidades

**El Orchestrator HACE:**
- Recibir texto plano del usuario a través de una API REST.
- Mantener y gestionar el ciclo de vida de un ecosistema de plugins dinámicos.
- Seleccionar el plugin más adecuado para atender una petición usando mecanismos rápidos y deterministas (Scoring basado en Keywords y Regex).
- Ejecutar el plugin seleccionado.
- Recibir un resultado estructurado del plugin y extraer el texto que el asistente debe "pronunciar".
- Devolver la respuesta al sistema solicitante.

**El Orchestrator NO HACE:**
- Captura de audio del micrófono o reproducción de audio.
- Inferencia de *Speech-to-Text* (STT).
- Síntesis de voz *Text-to-Speech* (TTS).
- Uso de Large Language Models (LLMs) para decidir qué plugin ejecutar o para redactar la respuesta. Las respuestas son deterministas y preprogramadas por los plugins.

## 3. Arquitectura interna

La arquitectura se divide en los siguientes componentes principales:

- **API Layer**: Construida sobre FastAPI, expone los endpoints HTTP necesarios para interactuar con el Orchestrator.
- **Router (Selection Engine)**: Motor de enrutamiento rápido que analiza la entrada de texto y calcula un "score" (puntuación) para cada plugin cargado.
- **Plugin Manager**: Encargado de descubrir, cargar dinámicamente, registrar y mantener en memoria las instancias de los plugins disponibles.
- **ResponseHandler**: Transforma el resultado estructurado (`PluginResult`) que emite el plugin en la respuesta estandarizada que devolverá la API al servicio consumidor.
- **Configuration**: Gestor centralizado para la configuración del Orchestrator y de cada plugin, usando variables de entorno o archivos `.env`.
- **Logging**: Sistema unificado de observabilidad para trazar el flujo completo de la petición, esencial para depurar la selección de plugins y la ejecución.

## 4. Flujo completo de ejecución

El ciclo de vida de una petición sigue estos pasos:

```text
+-------------+         +-----------+        +--------+        +----------------+       +---------------+
| Cliente STT |         | API Layer |        | Router |        | Plugin Manager |       | WeatherPlugin |
+-------------+         +-----------+        +--------+        +----------------+       +---------------+
       |                      |                  |                     |                        |
       | POST /api/v1/execute |                  |                     |                        |
       | {"text": "..."}      |                  |                     |                        |
       |--------------------->|                  |                     |                        |
       |                      | route_request()  |                     |                        |
       |                      |----------------->|                     |                        |
       |                      |                  | get_active_plugins()|                        |
       |                      |                  |-------------------->|                        |
       |                      |                  |                     |                        |
       |                      |                  | [Plugins...]        |                        |
       |                      |                  |<--------------------|                        |
       |                      |                  |                     |                        |
       |                      |                  | Calcular scores     |                        |
       |                      |                  |-----------------+   |                        |
       |                      |                  |                 |   |                        |
       |                      |                  |<----------------+   |                        |
       |                      |                  |                     |                        |
       |                      | Plugin ganador   |                     |                        |
       |                      |<-----------------|                     |                        |
       |                      |                  |                     |                        |
       |                      | execute(Context) |                     |                        |
       |                      |---------------------------------------------------------------->|
       |                      |                  |                     |                        |
       |                      |                  |                     |   Obtener clima        |
       |                      |                  |                     |   ------------------+  |
       |                      |                  |                     |                     |  |
       |                      |                  |                     |   <-----------------+  |
       |                      |                  |                     |                        |
       |                      | PluginResult(success=True, speech="Hoy hace sol")               |
       |                      |<----------------------------------------------------------------|
       |                      |                  |                     |                        |
       | AssistantResponse    |                  |                     |                        |
       |<---------------------|                  |                     |                        |
       |                      |                  |                     |                        |
+-------------+         +-----------+        +--------+        +----------------+       +---------------+
```

## 5. Sistema de plugins

El sistema de plugins está diseñado para ser totalmente modular y desacoplado del núcleo.

- **Descubrimiento y Carga Dinámica**: En el arranque, el `Plugin Manager` escanea el directorio `plugins/` buscando clases que hereden de la interfaz base `Plugin`. Utiliza el módulo `importlib` de Python para cargarlos de forma dinámica sin necesidad de importaciones estáticas (hardcoded) en el Orchestrator.
- **Registro**: Al cargarse, cada plugin se instancia y se registra en la memoria del `Plugin Manager`, exponiendo sus metadatos (nombre, palabras clave, expresiones regulares).
- **Ciclo de vida**:
  1. `Initialize`: Se ejecuta una vez al arrancar (carga configuración local, inicializa clientes).
  2. `Match/Score`: Invocado en cada petición para evaluar idoneidad.
  3. `Execute`: Invocado solo si el plugin es seleccionado.
  4. `Teardown`: Invocado al apagar el servicio para liberar recursos.

## 6. Estrategia de selección de plugins

Dado que no se usan LLMs, la selección recae en un sistema de **Scoring Determinista**. 
Cada plugin define un manifiesto con metadatos de coincidencia:
- **Keywords**: Lista de palabras clave. Cada coincidencia suma puntos (ej. +1 punto por cada palabra encontrada).
- **Patrones Regex**: Expresiones regulares para intenciones más complejas. Cada coincidencia suma más puntos (ej. +5 puntos por regex cumplida).
- **Regex Exclusiva (Opcional)**: Una expresión que, si coincide, garantiza la selección de ese plugin e ignora al resto (puntuación infinita).

**Cálculo de la puntuación:**
1. El `Router` normaliza el texto de entrada (minúsculas, eliminar acentos/signos).
2. Itera sobre cada plugin y evalúa los Keywords y Patrones.
3. Suma las puntuaciones.
4. El plugin con la puntuación más alta (que supere un umbral mínimo, ej. score > 0) "gana".
5. En caso de empate, se puede aplicar una prioridad estática definida en el plugin, o responder con un "FallbackPlugin" que indique "No he entendido la orden".

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
    def description(self) -> str:
        return ""

    @property
    def keywords(self) -> List[str]:
        return []

    @property
    def regex_patterns(self) -> List[str]:
        return []

    def initialize(self) -> None:
        pass

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
```

## 8. API REST

Construida con FastAPI, proporciona un punto de entrada síncrono para interactuar con el sistema.

**Endpoint Principal:**
`POST /api/v1/execute`

**Request Example:**
```json
{
  "text": "Abre Firefox, por favor."
}
```

**Response Example (Éxito):**
```json
{
  "success": true,
  "plugin_used": "SystemAppsPlugin",
  "speech": "He abierto Firefox",
  "execution_time_ms": 45
}
```

**Response Example (Ningún plugin coincide):**
```json
{
  "success": false,
  "plugin_used": "FallbackPlugin",
  "speech": "Lo siento, no he entendido qué quieres hacer.",
  "execution_time_ms": 2
}
```

## 9. Modelo de datos

Definición de entidades (Modelos Pydantic):

- **UserRequest**: La entrada al sistema.
  - `text` (str): Texto interpretado.
  - `timestamp` (float): Marca de tiempo.
- **PluginContext**: La información que recibe el plugin a ejecutar.
  - `raw_text` (str): El texto original.
  - `normalized_text` (str): Texto en minúsculas y sin acentos.
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
│   ├── api.py           # Endpoints FastAPI
│   ├── config.py        # Configuración global
│   ├── engine.py        # Motor de Routing y Scoring
│   ├── logger.py        # Configuración de logs
│   ├── models.py        # Definición de Pydantic models (UserRequest, etc)
│   └── plugin_manager.py # Lógica de descubrimiento de plugins
├── plugins/
│   ├── base.py          # Definición de las interfaces abstractas (Plugin, etc)
│   ├── fallback/        # Plugin por defecto
│   ├── weather/         # Ejemplo de plugin del tiempo
│   │   ├── main.py      # Clase del plugin
│   │   ├── config.py    # Configuración específica del plugin
│   │   └── requirements.txt # Dependencias opcionales
│   └── filesystem/
├── main.py              # Punto de entrada (uvicorn)
├── requirements.txt     # Dependencias del núcleo (fastapi, pydantic, etc)
├── Dockerfile
└── README.md
```

## 12. Observabilidad

El sistema incorpora *structured logging* (usando librerías como `logging` estándar configurada o `loguru`).
- **Nivel INFO**: Cada petición que entra, texto normalizado, qué plugin fue seleccionado, score ganador y tiempo total de ejecución.
- **Nivel DEBUG**: Puntuación desglosada por cada plugin (muy útil para depurar el Router).
- **Nivel ERROR**: Excepciones capturadas y tiempos de inactividad de las APIs en los plugins.

*Trazabilidad:* Para rastrear el flujo, se puede añadir un `request_id` único a cada petición en el momento que cruza el `API Layer`.

## 13. Extensibilidad

Añadir una nueva capacidad es trivial y **no requiere modificar el núcleo**:
1. Crear una carpeta nueva en `plugins/` (ej. `plugins/spotify/`).
2. Crear un archivo que contenga una clase que herede de `Plugin`.
3. Implementar las propiedades obligatorias (`name`, `keywords`...) y el método `execute()`.
4. Al reiniciar el Orchestrator, el `Plugin Manager` encontrará el nuevo archivo automáticamente y el router lo tendrá en cuenta en el scoring de la siguiente petición.

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
from core.models import PluginContext, PluginResult
from plugins.base import Plugin

class WeatherPlugin(Plugin):
    @property
    def name(self) -> str:
        return "WeatherPlugin"

    @property
    def keywords(self) -> list[str]:
        return ["tiempo", "clima", "lluvia", "sol", "temperatura", "frio", "calor"]

    @property
    def regex_patterns(self) -> list[str]:
        return [r"qué.*tiempo.*hace", r"va.*a.*llover"]

    async def execute(self, context: PluginContext) -> PluginResult:
        # Aquí iría una llamada a OpenWeatherMap, por ejemplo
        # weather_data = requests.get(...)
        
        # Simulación
        is_raining = False
        temp = 22
        
        speech = f"Actualmente hace {temp} grados. "
        speech += "No parece que vaya a llover." if not is_raining else "Llévate un paraguas, está lloviendo."
        
        return PluginResult(
            success=True,
            speech=speech,
            data={"temp": temp, "is_raining": is_raining}
        )
```

**Flujo:**
1. Usuario dice: *"Dime qué tiempo hace, por favor."*
2. Texto normalizado: *"dime que tiempo hace por favor"*
3. Router evalúa `WeatherPlugin`:
   - Match keyword: "tiempo" (+1)
   - Match regex: `r"que.*tiempo.*hace"` (+5)
   - Score total = 6.
4. Gana `WeatherPlugin`, se invoca `execute()`.
5. Se devuelve: `{"speech": "Actualmente hace 22 grados. No parece que vaya a llover."}`

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
