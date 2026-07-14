# Refinamiento de la Feature: Plugins Aleatorios (Random)

- **Archivo de origen**: [random_plugins.md](file:///home/danuser2018/workspace/orchestrator/doc/features/random_plugins.md)
- **Fecha**: 2026-07-14
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Incorporar tres nuevos plugins públicos relacionados con la generación de resultados aleatorios en el Orchestrator de Nova-2:
* **CoinPlugin** (id: `coin`, prioridad 60): Simula el lanzamiento de una moneda y devuelve "Cara" o "Cruz".
* **DicePlugin** (id: `dice`, prioridad 60): Simula el lanzamiento de un dado de seis caras.
* **RandomNumberPlugin** (id: `random-number`, prioridad 60): Genera un número entero aleatorio comprendido entre 1 y 99 (inclusive).

Para mantener una arquitectura limpia y preparada para futuras capacidades aleatorias (como barajar cartas o sorteos), la lógica de generación pseudoaleatoria se delegará a una nueva utilidad centralizada compartida (`RandomService`), la cual encapsulará las llamadas al módulo estándar `random` de Python. Todos los plugins generarán respuestas breves e informativas que cumplan estrictamente con el `TONE_GUIDE.md` de Nova-2.

### Actores y Reglas de Negocio
1. **Usuario**: Realiza preguntas en lenguaje natural pidiendo resultados al azar (ej. "Lanza una moneda", "Tira un dado", "Dime un número aleatorio").
2. **Orchestrator**: Calcula el score semántico con `RapidFuzz` y enruta la petición al plugin adecuado si supera el umbral configurado (`SIMILARITY_THRESHOLD`).
3. **RandomService**: Clase de utilidad interna (helper class) en el core del Orchestrator que centraliza el uso de la biblioteca pseudoaleatoria del sistema operativo, permitiendo inyectar dependencias y mockear resultados para pruebas unitarias fiables.
4. **CoinPlugin**: Llama a `RandomService.flip_coin()` y formatea el resultado en español conforme a la guía de tono.
5. **DicePlugin**: Llama a `RandomService.roll_dice()` y formatea la salida para indicar el número obtenido del dado.
6. **RandomNumberPlugin**: Llama a `RandomService.random_int(1, 99)` y devuelve el dato directamente como respuesta numérica.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/random_service.py` [NEW]: Crear la clase de utilidad `RandomService`. <br>- `plugins/random/` [NEW]: Crear el directorio y el archivo `main.py` con las clases `CoinPlugin`, `DicePlugin` y `RandomNumberPlugin`. <br>- `tests/test_random_plugin.py` [NEW]: Añadir pruebas unitarias exhaustivas para la utilidad y los tres plugins mockeados. <br>- `tests/test_routing.py` [Modificar]: Incorporar pruebas de enrutamiento que validen que RapidFuzz selecciona correctamente cada plugin con sus ejemplos. <br>- `tests/test_plugin_registration.py` [Modificar]: Añadir las capacidades `"coin"`, `"dice"` y `"random-number"` en las aserciones de registro de capacidades en `system-service`. <br>- `README.md` [Modificar]: Registrar los tres nuevos plugins en la tabla de la sección `6. Estrategia de selección de plugins`. <br>- `CHANGELOG.md` [Modificar]: Registrar los cambios del orquestador en la sección `[Sin publicar]`. |
| `home-assistant` | Modificar | - `docs/services.md` [Modificar]: Añadir las capacidades `"coin"`, `"dice"` y `"random-number"` en la documentación de ejemplos de POST/GET de `system-service`. <br>- `CHANGELOG.md` [Modificar]: Registrar las nuevas capacidades aleatorias a nivel del ecosistema global. |
| Todos los demás servicios | Ninguno | Los demás servicios (STT, TTS, mail-watchdog, etc.) no sufren modificaciones de código. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
No se requiere un nuevo ADR. La introducción de estos plugins y de la utilidad helper local se alinea perfectamente con la arquitectura de plugins dinámicos del Orchestrator, el patrón de enrutamiento determinado por `RapidFuzz` (ADR-003) y los estándares de APIs internas (ADR-004) y manejo de errores (ADR-002).

### Nota de diseño: desacoplamiento y testabilidad
El uso directo del módulo `random` de Python dentro de los plugins dificulta realizar aserciones deterministas en las pruebas unitarias. Al delegar esta obtención a una clase helper `RandomService`, se posibilita mockear de manera precisa sus llamadas en el entorno de pruebas, asegurando que los tests de comportamiento de los plugins sean reproducibles y estables.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Lanzamiento de moneda exitoso (Cara)
```gherkin
Dado que el RandomService determina un resultado de moneda "Cara"
Cuando el usuario solicita "Lanza una moneda" y el Orchestrator enruta a CoinPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Cara."
Y el JSON de data contiene {"result": "Cara"}
```

### Escenario 2: Lanzamiento de moneda exitoso (Cruz)
```gherkin
Dado que el RandomService determina un resultado de moneda "Cruz"
Cuando el usuario solicita "Cara o cruz." y el Orchestrator enruta a CoinPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Cruz."
Y el JSON de data contiene {"result": "Cruz"}
```

### Escenario 3: Lanzamiento de dado exitoso
```gherkin
Dado que el RandomService genera un valor de dado de 5
Cuando el usuario solicita "Tira un dado" y el Orchestrator enruta a DicePlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Ha salido un 5."
Y el JSON de data contiene {"result": 5}
```

### Escenario 4: Generación de número aleatorio exitosa
```gherkin
Dado que el RandomService genera el entero 37
Cuando el usuario solicita "Elige un número aleatorio" y el Orchestrator enruta a RandomNumberPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "37."
Y el JSON de data contiene {"result": 37}
```

### Escenario 5: Manejo de errores por fallo en la obtención aleatoria
```gherkin
Dado que ocurre un fallo o excepción inesperada en el RandomService al generar un resultado
Cuando el usuario solicita "Dado." y se ejecuta el DicePlugin
Entonces el plugin captura el error y responde con success=False
Y el speech devuelto es exactamente "No he podido completar la operación."
Y el error se registra mediante el logger del sistema con stacktrace
```

### Escenario 6: Registro dinámico en system-service
```gherkin
Dado que el Orchestrator arranca con CoinPlugin, DicePlugin y RandomNumberPlugin activos
Cuando se ejecuta la función de ciclo de vida lifespan en main.py
Entonces se envían las siguientes capacidades en la carga útil al endpoint POST /v1/system/capabilities de system-service:
  - {"id": "coin", "description": "Lanza una moneda y devuelve cara o cruz"}
  - {"id": "dice", "description": "Lanza un dado de seis caras"}
  - {"id": "random-number", "description": "Genera un número aleatorio entre 1 y 99"}

> **Nota de aislamiento lingüístico:** Los valores del campo `description` anteriores son cadenas de dato de negocio en español (el idioma del asistente), no identificadores técnicos. Por tanto, no incumplen la regla de aislamiento lingüístico del ecosistema Nova-2, que aplica exclusivamente a identificadores, endpoints, nombres de variables y código fuente.
```

### Escenario 7: Enrutamiento y selección semántica
```gherkin
Dado que el usuario pregunta "Cara o cruz."
Cuando el Orchestrator calcula la similitud semántica con RapidFuzz
Entonces selecciona correctamente CoinPlugin (score > 60.0)

Dado que el usuario pregunta "Lanza el dado."
Cuando el Orchestrator calcula la similitud semántica con RapidFuzz
Entonces selecciona correctamente DicePlugin (score > 60.0)

Dado que el usuario pregunta "Número al azar."
Cuando el Orchestrator calcula la similitud semántica con RapidFuzz
Entonces selecciona correctamente RandomNumberPlugin (score > 60.0)
```

---

## 4. Diseño Técnico y Contratos

### Utilidad Helper (`core/random_service.py`)
Clase responsable de encapsular el generador pseudoaleatorio del sistema.

```python
import logging
import random

logger = logging.getLogger(__name__)

class RandomService:
    def flip_coin(self) -> str:
        """
        Simulates a coin toss, returning 'Cara' or 'Cruz'.
        """
        try:
            return random.choice(["Cara", "Cruz"])
        except Exception as e:
            logger.error(f"Failed to flip coin: {e}", exc_info=True)
            raise e

    def roll_dice(self) -> int:
        """
        Simulates a classic 6-sided dice roll, returning an integer between 1 and 6.
        """
        try:
            return random.randint(1, 6)
        except Exception as e:
            logger.error(f"Failed to roll dice: {e}", exc_info=True)
            raise e

    def random_int(self, min_value: int, max_value: int) -> int:
        """
        Generates a pseudo-random integer between min_value and max_value (inclusive).
        """
        try:
            return random.randint(min_value, max_value)
        except Exception as e:
            logger.error(f"Failed to generate random integer: {e}", exc_info=True)
            raise e
```

### Implementación de Plugins (`plugins/random/main.py`)
Todos los plugins de generación aleatoria se modularizan dentro del mismo paquete.

```python
import logging
from typing import List
from core.models import PluginContext, PluginResult
from plugins.base import Plugin
from core.random_service import RandomService

logger = logging.getLogger(__name__)

class CoinPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "CoinPlugin"

    @property
    def description(self) -> str:
        return "Lanza una moneda y devuelve cara o cruz"

    @property
    def id(self) -> str:
        return "coin"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Lanza una moneda.",
            "Tira una moneda.",
            "Cara o cruz.",
            "Decide con una moneda.",
            "Haz un cara o cruz.",
            "Lanza una moneda al aire.",
            "Necesito un cara o cruz.",
            "Elige cara o cruz.",
            "Vamos a lanzar una moneda.",
            "Moneda."
        ]

    def initialize(self) -> None:
        logger.info("Initializing CoinPlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of CoinPlugin")
        try:
            result = self.random_service.flip_coin()
            # Response formatting: 'Cara.' or 'Cruz.'
            speech = f"{result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error executing CoinPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )


class DicePlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "DicePlugin"

    @property
    def description(self) -> str:
        return "Lanza un dado de seis caras"

    @property
    def id(self) -> str:
        return "dice"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Tira un dado.",
            "Lanza un dado.",
            "Necesito un dado.",
            "Haz una tirada de dado.",
            "Dime un número del dado.",
            "Lanza el dado.",
            "Vamos a tirar un dado.",
            "Tira los dados.",
            "Quiero lanzar un dado.",
            "Dado."
        ]

    def initialize(self) -> None:
        logger.info("Initializing DicePlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of DicePlugin")
        try:
            result = self.random_service.roll_dice()
            # Response formatting conforming to Tone Guide
            speech = f"Ha salido un {result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error executing DicePlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )


class RandomNumberPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.random_service = None

    @property
    def name(self) -> str:
        return "RandomNumberPlugin"

    @property
    def description(self) -> str:
        return "Genera un número aleatorio entre 1 y 99"

    @property
    def id(self) -> str:
        return "random-number"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "Elige un número.",
            "Dime un número.",
            "Dame un número aleatorio.",
            "Escoge un número.",
            "Número al azar.",
            "Piensa un número.",
            "Necesito un número.",
            "Elige un número para mí.",
            "Genera un número.",
            "Número aleatorio."
        ]

    def initialize(self) -> None:
        logger.info("Initializing RandomNumberPlugin")
        self.random_service = RandomService()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of RandomNumberPlugin")
        try:
            result = self.random_service.random_int(1, 99)
            # Response formatting conforming to Tone Guide (direct data format: '{value}.')
            speech = f"{result}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "result": result
                }
            )
        except Exception as e:
            logger.error(f"Error executing RandomNumberPlugin: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido completar la operación."
            )
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Excepción en la generación aleatoria** | Captura ordenada en el plugin, retorno con `success=False` y speech `"No he podido completar la operación."` (conforme a `ADR-002 (Orchestrator)`, categoría plugins conversacionales/de acción). | Bloque `try/except Exception` en el método `execute` de cada plugin para retornar un `PluginResult` controlado sin interrumpir el flujo del API. |
| **Registro de logs detallado** | La traza del error debe incluir el stacktrace completo del fallo original en `RandomService`. | Uso de `logger.error(..., exc_info=True)` tanto en la utilidad como en el plugin antes de retornar. |
| **Distribución uniforme y límites** | El rango debe estar estrictamente limitado y distribuirse de forma equilibrada. | Uso de las funciones nativas `random.choice` y `random.randint` de Python, que garantizan una distribución pseudoaleatoria uniforme adecuada. |
| **Latencia > 5 ms (RNF-01)** | El tiempo de ejecución debe ser inferior a 5 ms. | Operaciones en memoria utilizando la CPU local, sin bloqueos de red, E/S de ficheros ni esperas externas de ningún tipo. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias (`tests/test_random_plugin.py`)
Se creará un conjunto de pruebas dedicado a validar el funcionamiento lógico y el manejo de excepciones de la utilidad y los plugins:
1. **Pruebas de la Utilidad (`RandomService`)**:
   - Comprobar que `flip_coin()` devuelve `"Cara"` o `"Cruz"`.
   - Comprobar que `roll_dice()` devuelve un número entre 1 y 6.
   - Comprobar que `random_int(1, 99)` devuelve un número entre 1 y 99.
2. **Pruebas de comportamiento con mocks**:
   - Usar `unittest.mock.patch` sobre los métodos de `RandomService` (ej. `flip_coin`, `roll_dice`, `random_int`) para que devuelvan valores prefijados y verificar que las salidas de `execute` de los plugins coincidan con los formatos exigidos:
     - `flip_coin` retorna `"Cara"` -> speech `"Cara."`, `data["result"]` = `"Cara"`.
     - `flip_coin` retorna `"Cruz"` -> speech `"Cruz."`, `data["result"]` = `"Cruz"`.
     - `roll_dice` retorna `5` -> speech `"Ha salido un 5."`, `data["result"]` = `5`.
     - `random_int` retorna `37` -> speech `"37."`, `data["result"]` = `37`.
3. **Pruebas de fallo e integridad**:
   - Forzar excepciones en `RandomService` y asertar que los plugins capturan la excepción y devuelven `success=False` con el speech `"No he podido completar la operación."`.
   - Validar las prioridades (`60`), IDs (`coin`, `dice`, `random-number`) e inicializaciones de los tres plugins.

### Pruebas de Registro (`tests/test_plugin_registration.py`)
* Modificar `test_successful_plugin_registration` para incluir aserciones de presencia de las capacidades `"coin"`, `"dice"` y `"random-number"` en la lista de capacidades enviadas al arrancar el Orchestrator.

### Pruebas de Enrutamiento (`tests/test_routing.py`)
* Agregar casos de prueba de enrutamiento con aserciones semánticas específicas:
  - `"Lanza una moneda al aire."` -> `CoinPlugin`
  - `"Tira los dados."` -> `DicePlugin`
  - `"Dame un número aleatorio."` -> `RandomNumberPlugin`
  - `"Número al azar."` -> `RandomNumberPlugin`

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Servicio Helper RandomService en Orchestrator**
  - [ ] Crear el archivo [core/random_service.py](file:///home/danuser2018/workspace/orchestrator/core/random_service.py) e implementar la clase de utilidad `RandomService`.
- [ ] **Fase 2: Implementación de Plugins en Orchestrator**
  - [ ] Crear el directorio `plugins/random` en el repositorio `orchestrator`.
  - [ ] Crear el archivo [plugins/random/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/random/main.py) y codificar las clases `CoinPlugin`, `DicePlugin` y `RandomNumberPlugin`.
- [ ] **Fase 3: Pruebas Unitarias y de Enrutamiento**
  - [ ] Crear el archivo [tests/test_random_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_random_plugin.py) con toda la suite unitaria mockeada.
  - [ ] Modificar [tests/test_plugin_registration.py](file:///home/danuser2018/workspace/orchestrator/tests/test_plugin_registration.py) para validar el registro dinámico de las tres nuevas capacidades.
  - [ ] Modificar [tests/test_routing.py](file:///home/danuser2018/workspace/orchestrator/tests/test_routing.py) agregando los casos de enrutamiento para RapidFuzz correspondientes a las tiradas de dados, monedas y números al azar.
  - [ ] ✅ Validación: Ejecutar `PYTHONPATH=. pytest` en el Orchestrator y verificar que el 100% de los tests pasen exitosamente.
- [ ] **Fase 4: Documentación y Sincronización de Repositorios**
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en Orchestrator para incluir a `CoinPlugin`, `DicePlugin` y `RandomNumberPlugin` en la tabla de prioridades.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) en Orchestrator registrando las nuevas adiciones bajo la sección `[Sin publicar]`.
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en Home Assistant para incorporar `"coin"`, `"dice"` y `"random-number"` en los ejemplos de payloads de registro de capacidades en `system-service`.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) en Home Assistant para registrar las nuevas capacidades aleatorias del asistente.
