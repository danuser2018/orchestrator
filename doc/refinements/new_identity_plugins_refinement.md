# Refinamiento de la Feature: Nuevos Plugins Públicos de Identidad

- **Archivo de origen**: [new_identity_plugins.md](file:///home/danuser2018/workspace/orchestrator/doc/features/new_identity_plugins.md)
- **Fecha**: 2026-07-13
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Incorporar tres nuevos plugins públicos de información al Orchestrator del asistente Nova-2:
* **AuthorPlugin** (id: `author`): Responde a preguntas sobre el creador/autor de Nova-2, consultando la información configurada en `system-service`.
* **VersionPlugin** (id: `version`): Responde a consultas sobre la versión de software de Nova-2 instalada, consumiendo `system-service`.
* **HelpPlugin** (id: `help`): Explica el modelo de interacción conversacional del asistente, ayudando al usuario a saber cómo usar Nova-2 sin listar las capacidades dinámicas (tarea delegada en `CapabilitiesPlugin`).

Estos plugins deberán participar en el algoritmo estándar de similitud semántica con RapidFuzz y seguir estrictamente las pautas de brevedad, claridad y consistencia descritas en `TONE_GUIDE.md` y la gestión de excepciones de `ADR-002`.

### Actores y Reglas de Negocio
1. **Usuario**: Realiza preguntas o peticiones de ayuda en lenguaje natural referidas al autor, la versión de software o la guía de uso (ej. "¿Quién es tu creador?", "¿Qué versión tienes?", "Ayuda").
2. **Orchestrator**: Calcula la similitud semántica de las frases de entrada del usuario y enruta la petición al plugin correspondiente si se supera el umbral del motor de similitud.
3. **AuthorPlugin**: Llama a `system-service` de forma asíncrona, extrae el autor de los metadatos y genera la respuesta final de forma determinista.
4. **VersionPlugin**: Consume `system-service` para obtener y formatear la versión del sistema de forma limpia.
5. **HelpPlugin**: Devuelve una respuesta estática inmediata y breve con una guía rápida de interacción, sin dependencias externas.
6. **System Service**: Microservicio central que expone los metadatos globales del sistema mediante endpoints REST.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `plugins/identity/main.py`: Añadir la implementación de las clases `AuthorPlugin`, `VersionPlugin` y `HelpPlugin` heredando de la interfaz base `Plugin`.  <br>- `tests/test_identity_plugin.py`: Añadir la suite de pruebas unitarias para cada uno de los tres plugins cubriendo los escenarios exitosos y de error.  <br>- `tests/test_plugin_registration.py`: Actualizar las aserciones del mock de registro de capacidades para incluir `author`, `version` y `help`.  <br>- `README.md`: Actualizar la tabla de prioridades e identificadores de plugins en la sección `6. Estrategia de selección de plugins`.  <br>- `CHANGELOG.md`: Registrar en `[Sin publicar]` la incorporación de los tres nuevos plugins públicos de identidad y sus correspondientes tests unitarios. |
| `home-assistant` | Modificar | - `docs/services.md`: Actualizar la sección de `system-service` (líneas 347 y 369) para incluir los identificadores `author`, `version` y `help` en el catálogo y los ejemplos de capacidades registradas.  <br>- `CHANGELOG.md`: Registrar la adición de los nuevos plugins y sus capacidades en el ecosistema. |
| Todos los demás servicios | Ninguno | Las interfaces HTTP REST públicas del asistente y la comunicación de red entre contenedores no se ven afectadas por esta implementación interna de plugins. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
No se requiere un nuevo ADR. El contrato de red entre Orchestrator y `system-service` ya fue aceptado, y las políticas de formateo y gestión homogénea de errores ante fallos de conectividad están completamente alineadas con el `ADR-002`.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Consulta del autor del asistente exitosa
```gherkin
Dado que el servicio system-service responde con HTTP 200 y el JSON {"name": "Nova", "author": "Xeretre Studios", "version": "2.0.0", "description": "..."}
Cuando el usuario pregunta "¿Quién es el autor de Nova?" y el Orchestrator enruta la petición a AuthorPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Nova ha sido desarrollada por Xeretre Studios."
Y el JSON de data contiene "author": "Xeretre Studios"
```

### Escenario 2: Indisponibilidad de conexión para obtener el autor
```gherkin
Dado que el contenedor system-service no está disponible en la red o la petición tiene timeout
Cuando el usuario pregunta "¿Quién te ha creado?"
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "Servicio no disponible."
```

### Escenario 3: Respuesta con error HTTP de system-service al consultar autor
```gherkin
Dado que el servicio system-service responde con un código de error HTTP 500 o 503
Cuando el usuario pregunta "¿Quién te desarrolló?"
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

### Escenario 4: Consulta de la versión instalada de Nova exitosa
```gherkin
Dado que el servicio system-service responde con HTTP 200 y el JSON {"name": "Nova", "author": "David", "version": "2.5.1", "description": "..."}
Cuando el usuario pregunta "¿Qué versión de Nova es esta?" y el Orchestrator enruta la petición a VersionPlugin
Entonces el plugin responde con success=True
Y el speech devuelto es exactamente "Versión 2.5.1."
Y el JSON de data contiene "version": "2.5.1"
```

### Escenario 5: Indisponibilidad de conexión al consultar versión
```gherkin
Dado que el contenedor system-service no responde a la petición de red
Cuando el usuario pregunta "¿Cuál es tu versión?"
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "Servicio no disponible."
```

### Escenario 6: Consulta de ayuda en el uso del asistente
```gherkin
Dado que el usuario pregunta "¿Cómo se usa Nova?" y el Orchestrator enruta la petición a HelpPlugin
Cuando el plugin ejecuta su método execute
Entonces responde con success=True
Y el speech devuelto es exactamente "Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: \"¿Qué tiempo hace?\" o \"Enciende la luz del salón.\""
Y el JSON de data está vacío
```

### Escenario 7: Excepción inesperada al consultar el autor
```gherkin
Dado que se produce una excepción inesperada durante la ejecución del AuthorPlugin (distinta de errores de red o HTTP)
Cuando el usuario pregunta "¿Quién te ha creado?"
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

### Escenario 8: Excepción inesperada al consultar la versión
```gherkin
Dado que se produce una excepción inesperada durante la ejecución del VersionPlugin (distinta de errores de red o HTTP)
Cuando el usuario pregunta "¿Cuál es tu versión?"
Entonces el plugin responde con success=False
Y el speech devuelto es exactamente "No he podido obtener la información."
```

### Escenario 9: Validación de enrutamiento correcto por similitud semántica
```gherkin
Dado que el Orchestrator tiene activos AuthorPlugin, VersionPlugin, HelpPlugin e IdentityPlugin con sus frases de ejemplo registradas
Cuando el usuario pregunta "¿Quién es el autor de Nova?"
Entonces el Orchestrator selecciona AuthorPlugin y no IdentityPlugin

Cuando el usuario pregunta "¿Qué versión tienes?"
Entonces el Orchestrator selecciona VersionPlugin

Cuando el usuario pregunta "Ayuda"
Entonces el Orchestrator selecciona HelpPlugin
```

---

## 4. Diseño Técnico y Contratos

### Estructura de Clases y Métodos (`plugins/identity/main.py`)

Añadir las clases de los nuevos plugins al archivo existente. La inicialización del cliente HTTP se realizará en `initialize()` y las llamadas a red se realizarán de forma asíncrona dentro del método `execute()`.

```python
class AuthorPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "AuthorPlugin"

    @property
    def description(self) -> str:
        return "Información sobre el autor de Nova"

    @property
    def id(self) -> str:
        return "author"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Quién te ha creado?",
            "¿Quién te hizo?",
            "¿Quién es tu creador?",
            "¿Quién es el autor de Nova?",
            "¿Quién desarrolló Nova?",
            "¿Quién te desarrolló?",
            "Dame el nombre del autor de Nova.",
            "¿Quién programó Nova?",
            "¿Quién escribió el código de Nova?",
            "¿Quién es tu autor?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing AuthorPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of AuthorPlugin")
        try:
            try:
                system_info = await self.client.get_system_info()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving system info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving system info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            speech = f"Nova ha sido desarrollada por {system_info.author}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "author": system_info.author
                }
            )
        except Exception as e:
            logger.error(f"Unexpected exception in AuthorPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class VersionPlugin(Plugin):
    def __init__(self):
        super().__init__()
        self.client = None

    @property
    def name(self) -> str:
        return "VersionPlugin"

    @property
    def description(self) -> str:
        return "Información sobre la versión instalada de Nova"

    @property
    def id(self) -> str:
        return "version"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Qué versión eres?",
            "¿Qué versión tienes?",
            "¿Qué versión de Nova es esta?",
            "¿Cuál es tu versión?",
            "¿En qué versión estás?",
            "Dime tu versión.",
            "¿Qué versión está instalada?",
            "¿Qué release tienes?",
            "¿Qué build estás ejecutando?",
            "¿Cuál es la versión actual?"
        ]

    def initialize(self) -> None:
        logger.info("Initializing VersionPlugin")
        self.client = SystemServiceClient()

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of VersionPlugin")
        try:
            try:
                system_info = await self.client.get_system_info()
            except (httpx.ConnectError, httpx.TimeoutException) as conn_err:
                logger.error(f"Connection error or timeout connecting to System Service: {conn_err}")
                return PluginResult(
                    success=False,
                    speech="Servicio no disponible."
                )
            except httpx.HTTPError as http_err:
                logger.error(f"HTTP error retrieving system info: {http_err}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )
            except Exception as e:
                logger.error(f"Error retrieving system info: {e}", exc_info=True)
                return PluginResult(
                    success=False,
                    speech="No he podido obtener la información."
                )

            speech = f"Versión {system_info.version}."
            return PluginResult(
                success=True,
                speech=speech,
                data={
                    "version": system_info.version
                }
            )
        except Exception as e:
            logger.error(f"Unexpected exception in VersionPlugin execution: {e}", exc_info=True)
            return PluginResult(
                success=False,
                speech="No he podido obtener la información."
            )


class HelpPlugin(Plugin):
    @property
    def name(self) -> str:
        return "HelpPlugin"

    @property
    def description(self) -> str:
        return "Explica cómo utilizar Nova"

    @property
    def id(self) -> str:
        return "help"

    @property
    def priority(self) -> int:
        return 60

    @property
    def examples(self) -> List[str]:
        return [
            "¿Cómo se usa Nova?",
            "¿Cómo te utilizo?",
            "¿Cómo puedo hablar contigo?",
            "¿Cómo funcionas?",
            "¿Cómo debo usarte?",
            "Explícame cómo utilizar Nova.",
            "¿Cómo puedo darte órdenes?",
            "Ayuda.",
            "Necesito ayuda.",
            "¿Cómo empiezo?"
        ]

    async def execute(self, context: PluginContext) -> PluginResult:
        logger.info("Starting execution of HelpPlugin")
        speech = "Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: \"¿Qué tiempo hace?\" o \"Enciende la luz del salón.\""
        return PluginResult(
            success=True,
            speech=speech,
            data={}
        )
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Error de conexión / Timeout** | Retornar success en `False` y mensaje de voz `"Servicio no disponible."`. | Capturar las excepciones `httpx.ConnectError` y `httpx.TimeoutException` en el bloque de llamadas asíncronas de red. |
| **Error HTTP de red (5xx, 4xx)** | Retornar success en `False` y mensaje de voz `"No he podido obtener la información."`. | Capturar `httpx.HTTPError` mediante la invocación automática de `response.raise_for_status()`. |
| **Excepción inesperada** | Evitar la caída del servicio FastAPI; retornar `"No he podido obtener la información."`. | Captura genérica de excepciones `except Exception` que registra el traceback del error por log y responde con el mensaje genérico estándar (`ADR-002`). |
| **JSON malformado en system-service** | Evitar errores de atributo o de validación de esquemas en Pydantic. | El constructor `SystemInfo` deserializa los campos; si falla, la excepción se captura en el bloque `except Exception` general retornando error controlado. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias (`tests/test_identity_plugin.py`)
Se añadirán las siguientes aserciones y tests mockeados utilizando `unittest.mock.patch`:
1. **AuthorPlugin - Éxito**: Mockear la llamada HTTP a `get_system_info()` retornando `author="Xeretre Studios"`. Verificar que la respuesta de voz es exactamente `"Nova ha sido desarrollada por Xeretre Studios."` y que `data` contiene el autor.
2. **AuthorPlugin - Conexión caída**: Mockear `ConnectError` y verificar la respuesta de voz `"Servicio no disponible."` y éxito en `False`.
3. **AuthorPlugin - Error HTTP**: Mockear `HTTPError` y verificar la respuesta de voz `"No he podido obtener la información."` y éxito en `False`.
4. **VersionPlugin - Éxito**: Mockear la llamada HTTP a `get_system_info()` retornando `version="2.0.0"`. Verificar la respuesta de voz `"Versión 2.0.0."` y que `data` contiene la versión.
5. **VersionPlugin - Conexión caída**: Verificar la respuesta de voz `"Servicio no disponible."`.
6. **HelpPlugin - Éxito**: Invocar el plugin con cualquier contexto. Verificar la respuesta de voz `"Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: \"¿Qué tiempo hace?\" o \"Enciende la luz del salón.\""` y que `success` es `True`.
7. **Verificación de Propiedades**: Validar las propiedades de los tres plugins: IDs (`author`, `version`, `help`), prioridad `60` para todos y la existencia de sus listas de ejemplos.
8. **AuthorPlugin - Excepción inesperada**: Mockear una excepción genérica (`Exception`) durante `get_system_info()` y verificar que `success` es `False` y el speech es exactamente `"No he podido obtener la información."` (cubre Escenario 7).
9. **VersionPlugin - Excepción inesperada**: Mockear una excepción genérica (`Exception`) durante `get_system_info()` y verificar que `success` es `False` y el speech es exactamente `"No he podido obtener la información."` (cubre Escenario 8).

### Pruebas de Registro (`tests/test_plugin_registration.py`)
* Actualizar el test `test_successful_plugin_registration` para verificar que la lista de capacidades enviada a `system-service` contiene a `"author"`, `"version"` y `"help"`.

### Pruebas de Enrutamiento (`tests/test_routing.py`)
* Añadir tests de integración del router que validen el enrutamiento correcto frente a los plugins existentes (cubre Escenario 9):
  * Verificar que `"¿Quién es el autor de Nova?"` selecciona `AuthorPlugin` y no `IdentityPlugin`.
  * Verificar que `"¿Qué versión tienes?"` selecciona `VersionPlugin`.
  * Verificar que `"Ayuda"` selecciona `HelpPlugin`.

### Verificación local
Ejecutar la suite completa para asegurar la ausencia de regresiones:
```bash
PYTHONPATH=. pytest tests/test_identity_plugin.py
PYTHONPATH=. pytest tests/test_plugin_registration.py
PYTHONPATH=. pytest tests/test_routing.py
PYTHONPATH=. pytest
```

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Implementación de Plugins en Orchestrator**
  - [ ] Modificar [plugins/identity/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/identity/main.py) añadiendo las clases `AuthorPlugin`, `VersionPlugin` y `HelpPlugin` con sus propiedades, inicialización y método `execute()`.
- [ ] **Fase 2: Adición de Tests Unitarios e Integración**
  - [ ] Modificar [tests/test_identity_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_identity_plugin.py) implementando las pruebas para los nuevos plugins (casos de éxito, fallos de conexión y excepciones HTTP).
  - [ ] Modificar [tests/test_plugin_registration.py](file:///home/danuser2018/workspace/orchestrator/tests/test_plugin_registration.py) para incorporar la aserción de registro de capacidades de `author`, `version` y `help`.
  - [ ] Modificar [tests/test_routing.py](file:///home/danuser2018/workspace/orchestrator/tests/test_routing.py) añadiendo tests de enrutamiento que validen que `"¿Quién es el autor de Nova?"` selecciona `AuthorPlugin` (y no `IdentityPlugin`), `"¿Qué versión tienes?"` selecciona `VersionPlugin` y `"Ayuda"` selecciona `HelpPlugin`.
  - [ ] Ejecutar `PYTHONPATH=. pytest` localmente en el contenedor o terminal del Orchestrator y validar que todos los casos pasan sin error.
- [ ] **Fase 3: Actualización de Documentación**
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en el Orchestrator para incluir los nuevos plugins en la tabla de prioridades.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) en el Orchestrator resumiendo la incorporación de los nuevos plugins de identidad.
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en Home Assistant para incluir las nuevas capacidades en el catálogo (líneas 347 y 369).
  - [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en Home Assistant para corregir la descripción de `system-service` eliminando la referencia a que es consumido "exclusivamente por el Identity Plugin" y reflejando que también lo consumen `AuthorPlugin` y `VersionPlugin`.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) en Home Assistant para registrar las nuevas capacidades del asistente a nivel global.
