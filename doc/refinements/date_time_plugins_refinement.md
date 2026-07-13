# Refinamiento de la Feature: Plugins de Fecha y Hora

- **Archivo de origen**: [date_time_plugins.md](file:///home/danuser2018/workspace/orchestrator/doc/features/date_time_plugins.md)
- **Fecha**: 2026-07-13
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Incorporar dos nuevos plugins públicos de información al Orchestrator de Nova-2:
* **TimePlugin** (id: `time`, prioridad 80): Responde consultas sobre la hora actual en formato de 24 horas.
* **DatePlugin** (id: `date`, prioridad 80): Responde consultas sobre la fecha actual en formato extendido.

Ambos plugins obtienen los datos directamente del reloj del sistema y delegan la lógica de formateo a una utilidad común compartida (`DateTimeService`). El objetivo es evitar código duplicado para el formateo en español y la gestión de cadenas de texto. Las respuestas deben ser breves, claras y alineadas con el `TONE_GUIDE.md` de Nova-2.

### Actores y Reglas de Negocio
1. **Usuario**: Realiza preguntas en lenguaje natural sobre la hora o partes de la fecha actual (ej. "¿Qué hora es?", "¿Qué día es hoy?", "¿En qué año estamos?").
2. **Orchestrator**: Evalúa el texto, calcula el score semántico con RapidFuzz y delega la ejecución al plugin correspondiente si se supera el umbral de similitud.
3. **DateTimeService**: Clase interna de utilidad (helper class) que centraliza la interacción con `datetime.now()` del sistema operativo y realiza la traducción y formateo al locale español.
4. **TimePlugin**: Utiliza `DateTimeService` para construir y retornar la respuesta de la hora actual.
5. **DatePlugin**: Utiliza `DateTimeService` para construir y retornar la fecha completa actual.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/datetime_service.py` [NEW]: Crear la clase de utilidad `DateTimeService` para el cálculo y formateo de fecha/hora. <br>- `plugins/datetime/` [NEW]: Crear directorio y `main.py` con las clases `TimePlugin` y `DatePlugin`. <br>- `tests/test_datetime_plugin.py` [NEW]: Añadir pruebas unitarias para `DateTimeService`, `TimePlugin` y `DatePlugin`. <br>- `tests/test_routing.py` [Modificar]: Incorporar pruebas de enrutamiento que validen la selección correcta de ambos plugins. <br>- `tests/test_plugin_registration.py` [Modificar]: Añadir las capacidades `"time"` y `"date"` a los mocks de validación de registro de capacidades en el arranque. <br>- `README.md` [Modificar]: Registrar los nuevos plugins en la tabla de prioridades de la sección `6. Estrategia de selección de plugins`. <br>- `CHANGELOG.md` [Modificar]: Registrar la inclusión de la característica y de sus tests asociados en la sección `[Sin publicar]`. |
| `home-assistant` | Modificar | - `docs/services.md` [Modificar]: Añadir los identificadores `time` y `date` en el catálogo de capacidades y ejemplos en la sección de `system-service`. <br>- `CHANGELOG.md` [Modificar]: Documentar a nivel de ecosistema el soporte para respuestas nativas de fecha y hora. |
| Todos los demás servicios | Ninguno | El resto de servicios de microprocesamiento (STT, TTS, mail-watchdog, etc.) permanecen inalterados. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
No se requiere un nuevo ADR. El cambio no altera el protocolo de red, ni añade dependencias a bases de datos o servicios externos. Se ajusta perfectamente al patrón de plugins dinámicos del Orchestrator y sigue las reglas de control de errores y logs definidas en `ADR-002`.

### Nota de diseño: ubicación de la lógica de formateo
La lógica de formateo de fecha y hora (traducción al español, construcción de cadenas de texto) se centraliza en `core/datetime_service.py` como helper interno del Orchestrator. Esta decisión es coherente con el invariante de la skill `service-responsibilities` porque: (1) la fuente de datos es exclusivamente el reloj del sistema operativo, sin dependencia de ningún microservicio externo; (2) no existe un servicio de dominio de fecha/hora en el ecosistema Nova-2; y (3) la complejidad del formateo no justifica la creación de un nuevo microservicio. Los plugins `TimePlugin` y `DatePlugin` delegan toda la obtención y el formateo a esta clase, manteniéndose a sí mismos libres de lógica.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Consulta de la hora actual exitosa
```gherkin
Dado que el reloj del sistema devuelve las 15:42
Cuando el usuario pregunta "¿Qué hora es?" y el Orchestrator enruta a TimePlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Son las 15:42."
Y el JSON de data contiene "time": "15:42"
```

### Escenario 2: Error al obtener la hora
```gherkin
Dado que ocurre un error de lectura o excepción en el reloj del sistema al obtener la hora
Cuando el usuario pregunta "Hora actual."
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

### Escenario 3: Consulta de la fecha actual exitosa
```gherkin
Dado que el reloj del sistema marca el lunes 13 de julio de 2026
Cuando el usuario pregunta "¿Qué día es hoy?" y el Orchestrator enruta a DatePlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Hoy es lunes, 13 de julio de 2026."
Y el JSON de data contiene "date": "Hoy es lunes, 13 de julio de 2026."
```

### Escenario 4: Consulta de mes o año devuelve la fecha completa
```gherkin
Dado que el reloj del sistema marca el lunes 13 de julio de 2026
Cuando el usuario pregunta "¿En qué año estamos?" y el Orchestrator enruta a DatePlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Hoy es lunes, 13 de julio de 2026."
Y el JSON de data contiene "date": "Hoy es lunes, 13 de julio de 2026."
```

### Escenario 5: Error al obtener la fecha
```gherkin
Dado que ocurre un error de lectura o excepción en el reloj del sistema al obtener la fecha
Cuando el usuario pregunta "Fecha actual."
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

### Escenario 6: Registro dinámico en system-service
```gherkin
Dado que el Orchestrator arranca con TimePlugin y DatePlugin cargados
Cuando se ejecuta la función de ciclo de vida lifespan en main.py
Entonces se envían las capacidades {"id": "time", "description": "Consulta la hora actual"} y {"id": "date", "description": "Consulta la fecha actual"} al endpoint POST /v1/system/capabilities de system-service
```

### Escenario 7: Enrutamiento y prioridades con RapidFuzz
```gherkin
Dado que el usuario pregunta "¿Qué hora marca el reloj?"
Cuando el Orchestrator calcula la similitud semántica con RapidFuzz
Entonces selecciona correctamente TimePlugin (score > 60.0)

Dado que el usuario pregunta "¿Qué mes es?"
Cuando el Orchestrator calcula la similitud semántica con RapidFuzz
Entonces selecciona correctamente DatePlugin (score > 60.0)
```

---

## 4. Diseño Técnico y Contratos

### Utilidad Común (`core/datetime_service.py`)
Clase responsable de acceder al sistema y formatear los valores de fecha y hora al español.

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SPANISH_WEEKDAYS = [
    "lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"
]

SPANISH_MONTHS = [
    None, "enero", "febrero", "marzo", "abril", "mayo", "junio", 
    "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
]

class DateTimeService:
    def get_current_time(self) -> str:
        """
        Retrieves system time and formats it as HH:MM.
        """
        try:
            now = datetime.now()
            return now.strftime("%H:%M")
        except Exception as e:
            logger.error(f"Failed to retrieve system time: {e}", exc_info=True)
            raise e

    def get_current_date(self) -> str:
        """
        Retrieves system date and formats it as 'Hoy es {day_of_week}, {day} de {month} de {year}.'
        """
        try:
            now = datetime.now()
            day_of_week = SPANISH_WEEKDAYS[now.weekday()]
            day = now.day
            month = SPANISH_MONTHS[now.month]
            year = now.year
            return f"Hoy es {day_of_week}, {day} de {month} de {year}."
        except Exception as e:
            logger.error(f"Failed to retrieve system date: {e}", exc_info=True)
            raise e
```

### Implementación de Plugins (`plugins/datetime/main.py`)

Ambos plugins se definirán en el mismo módulo para facilitar la modularización.

```python
import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.datetime_service import DateTimeService

logger = logging.getLogger(__name__)

class TimePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.datetime_service = None

    @property
    def name(self) -> str:
        return "TimePlugin"

    @property
    def description(self) -> str:
        return "Consulta la hora actual"

    @property
    def id(self) -> str:
        return "time"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué hora es?",
            "Dime la hora.",
            "¿Me dices la hora?",
            "¿Qué hora tenemos?",
            "¿Puedes decirme la hora?",
            "Necesito saber la hora.",
            "Hora actual.",
            "¿Cuál es la hora?",
            "¿Qué hora marca el reloj?",
            "¿Tienes la hora?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing TimePlugin")
        self.datetime_service = DateTimeService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of TimePlugin")
        try:
            time_str = self.datetime_service.get_current_time()
            speech = f"Son las {time_str}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "time": time_str
                }
            )
        except Exception as e:
            logger.error(f"Error executing TimePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class DatePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.datetime_service = None

    @property
    def name(self) -> str:
        return "DatePlugin"

    @property
    def description(self) -> str:
        return "Consulta la fecha actual"

    @property
    def id(self) -> str:
        return "date"

    @property
    def priority(self) -> int:
        return 80

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué día es hoy?",
            "¿Cuál es la fecha de hoy?",
            "¿Qué fecha es?",
            "¿En qué mes estamos?",
            "¿En qué año estamos?",
            "Dime la fecha.",
            "¿Qué día tenemos hoy?",
            "¿Qué mes es?",
            "¿Qué año es?",
            "Fecha actual."
        ]

    def initialize(self) -> None:
        logger.info("Initializing DatePlugin")
        self.datetime_service = DateTimeService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of DatePlugin")
        try:
            date_str = self.datetime_service.get_current_date()
            return PluginResult(
                success=True,
                speech=date_str,
                data={
                    "date": date_str
                }
            )
        except Exception as e:
            logger.error(f"Error executing DatePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Excepción al obtener la fecha/hora** | Captura y retorno ordenado con `success=False` y mensaje estandarizado. | Bloque `try/except` en el método `execute` de cada plugin que captura cualquier excepción y retorna el `PluginResult` controlado sin tumbar el router de FastAPI. |
| **Excepciones en DateTimeService** | El log del error con stacktrace completo debe quedar registrado para depuración. | Uso de `logger.error(..., exc_info=True)` en la utilidad `DateTimeService` antes de propagar la excepción. |
| **Consultas sobre el mes o año** | Retornar la cadena de fecha completa actual. | Comportamiento por diseño en `DatePlugin`, donde el enrutamiento resolverá la intención hacia `DatePlugin` y éste devolverá siempre la cadena extendida producida por `DateTimeService.get_current_date()`. |
| **Tiempo de respuesta > 10ms** | Todo el cómputo debe ejecutarse localmente sin bloqueos de red para garantizar `< 10ms`. | Acceso directo a la librería estándar `datetime` y ausencia total de llamadas HTTP, E/S de red o subprocesos pesados. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias (`tests/test_datetime_plugin.py`)
Se creará un archivo específico cubriendo:
1. **Mock de reloj del sistema**: Uso de `unittest.mock.patch` sobre `core.datetime_service.datetime` para simular llamadas controladas retornando un objeto `datetime` fijo.
2. **DateTimeService - Formato Hora**: Mockear a las `15:42` y asertar que devuelve `"15:42"`.
3. **DateTimeService - Formato Fecha**: Mockear al lunes `13 de julio de 2026` y asertar que devuelve `"Hoy es lunes, 13 de julio de 2026."`.
4. **TimePlugin - Éxito**: Verificar que `execute` retorna `success=True`, speech `"Son las 15:42."` y `data` con la clave `"time"`.
5. **TimePlugin - Error**: Forzar un error en `DateTimeService` (lanzando una excepción) y verificar que `execute` responde `success=False` y speech `"No he podido obtener la información."`.
6. **DatePlugin - Éxito**: Verificar que `execute` retorna `success=True`, speech `"Hoy es lunes, 13 de julio de 2026."` y `data` con la clave `"date"`.
7. **DatePlugin - Error**: Forzar excepción en `DateTimeService` y asertar retorno de `success=False` y speech `"No he podido obtener la información."`.
8. **Verificación de Metadatos**: Comprobar IDs (`time`, `date`), nombres, prioridades (`80`) y ejemplos de frases para asegurar que no se solapan.

### Pruebas de Registro (`tests/test_plugin_registration.py`)
* Actualizar el test `test_successful_plugin_registration` para validar que el diccionario de capacidades enviado a `system-service` contenga a `"time"` y `"date"`.

### Pruebas de Enrutamiento (`tests/test_routing.py`)
* Añadir aserciones para las frases de entrada del usuario que demuestren que RapidFuzz selecciona correctamente `TimePlugin` o `DatePlugin` de forma determinista:
  - `"¿Qué hora marca el reloj?"` -> `TimePlugin`.
  - `"¿En qué mes estamos?"` -> `DatePlugin`.
  - `"¿En qué año estamos?"` -> `DatePlugin`.
  - `"Fecha actual."` -> `DatePlugin`.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Utilidad DateTimeService en Orchestrator**
  - [ ] Crear el archivo [core/datetime_service.py](file:///home/danuser2018/workspace/orchestrator/core/datetime_service.py) e implementar la clase `DateTimeService` con los métodos `get_current_time()` y `get_current_date()`.
- [ ] **Fase 2: Implementación de Plugins**
  - [ ] Crear el directorio `plugins/datetime` si no existe.
  - [ ] Crear el archivo [plugins/datetime/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/datetime/main.py) y codificar las clases `TimePlugin` y `DatePlugin`.
- [ ] **Fase 3: Implementación y Actualización de Pruebas**
  - [ ] Crear el archivo [tests/test_datetime_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_datetime_plugin.py) con las pruebas unitarias y de error mockeadas para ambos plugins y la utilidad.
  - [ ] Modificar [tests/test_plugin_registration.py](file:///home/danuser2018/workspace/orchestrator/tests/test_plugin_registration.py) para incorporar la validación del registro dinámico de las capacidades `time` y `date`.
  - [ ] Modificar [tests/test_routing.py](file:///home/danuser2018/workspace/orchestrator/tests/test_routing.py) agregando casos de enrutamiento específicos para consultas semánticas de fecha y hora.
  - [ ] ✅ Validación: Ejecutar `PYTHONPATH=. pytest` en el Orchestrator y confirmar que **todos los tests pasan** antes de avanzar a la Fase 4.
- [ ] **Fase 4: Actualización de Documentación y Metadatos**
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en Orchestrator e incorporar `TimePlugin` y `DatePlugin` en la tabla de prioridades.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) en Orchestrator documentando la adición de la nueva feature.
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en Home Assistant para agregar los identificadores y descripciones de `time` y `date` en las secciones del catálogo de capacidades registradas del `system-service`.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) en Home Assistant para registrar las nuevas capacidades del asistente a nivel global de ecosistema.
