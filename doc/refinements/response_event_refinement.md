# Refinamiento de la Feature: Integración del primer evento del dominio (Fase 3)

- **Archivo de origen**: [response_event.md](file:///home/danuser2018/workspace/orchestrator/doc/features/response_event.md)
- **Fecha**: 2026-07-18
- **Estado**: Refinado / Listo para revisión de DoR

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Integrar la librería unificada de mensajería `nova-event-bus` en el servicio `orchestrator` para publicar el primer evento del dominio de Nova: `ResponseGeneratedEvent`. Este evento se publicará de manera asíncrona cada vez que el Orchestrator genere una respuesta válida mediante la ejecución exitosa de un plugin, permitiendo desacoplar el sistema y habilitar a futuros consumidores a reaccionar ante respuestas sin acoplarse directamente al ciclo de ejecución de la intención.

### Actores y Reglas de Negocio
1. **Orchestrator**: 
   - Durante el arranque (startup), inicializa y conecta la instancia de `EventBus` a NATS de forma no bloqueante.
   - Al finalizar la ejecución de un plan de plugins con éxito (`success=True`), publica el evento `ResponseGeneratedEvent` antes de responder al cliente.
   - En caso de desconexión del broker o error en la publicación, registra un error en logs pero continúa respondiendo normalmente (resiliencia y transparencia para el usuario).
   - Durante la parada (shutdown), cierra limpiamente la conexión del Event Bus.
2. **Consumidores (Futuros)**: Reaccionan a `ResponseGeneratedEvent` leyendo la respuesta generada, el plugin ejecutado, la confianza y metadatos de la interacción.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `requirements.txt`: Se añade la dependencia de `nova-event-bus` con su referencia de producción. <br> - `core/models.py`: Se añaden los campos opcionales `correlation_id` y `channel` a `UserRequest` y `PluginContext` para mantener retrocompatibilidad. <br> - `main.py`: Conexión y desconexión en lifespan, captura y log de fallos de conexión. <br> - `core/engine.py`: Modificación del planificador para propagar `correlation_id` y `channel` al contexto, y actualización de `PlanExecutor` para publicar el evento. <br> - `tests/conftest.py`: Mocking del arranque de NATS para no interferir en las pruebas unitarias locales. <br> - `CHANGELOG.md`: Registro cronológico en la sección `[Sin publicar]`. |
| `orchestrator` | **[NEW]** | - `core/events.py`: Definición de la clase de evento tipado `ResponseGeneratedEvent`. <br> - `tests/test_event_publishing.py`: Suite de tests unitarios y de integración con mocks para verificar la publicación del evento y la resiliencia ante caídas del broker. |
| `home-assistant` (Despliegue) | Modificar | - `docker-compose.yml`: Adición de la variable `NATS_URL` al contenedor del orquestador y dependencia de arranque `nats` (siguiendo el ADR-010 para variables de infraestructura inline). |

> **Evaluación de necesidad de ADR:** Se ha analizado el impacto arquitectónico conforme a la skill `architecture-decisions`. Dado que se añade el campo `correlation_id` y `channel` a `UserRequest` (modificando la estructura del modelo público de datos del orquestador), y siguiendo la convención establecida en `adr-001-adicion-timestamp-userrequest.md`, **se requiere crear un nuevo ADR local** (ADR-005) para documentar esta extensión del contrato de la API de forma explícita y transparente.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Arranque correcto y conexión al broker NATS
```gherkin
Dado que el Orchestrator se inicializa correctamente
Cuando se ejecuta el hook de arranque (startup)
Entonces debe instanciarse el cliente NatsEventBus de la librería "nova-event-bus"
Y debe establecer la conexión asíncrona con el broker NATS configurado en la variable "NATS_URL"
Y el servicio debe quedar en estado listo sin bloquearse ante demoras de conexión
```

### Escenario 2: Publicación del evento tras la generación de una respuesta válida
```gherkin
Dado que el Orchestrator tiene una conexión activa con el Event Bus
Y recibe una petición HTTP "POST /api/v1/execute-plan" con un plan de ejecución válido
Cuando los plugins se ejecutan correctamente y se construye una respuesta con success=True
Entonces el Orchestrator debe instanciar "ResponseGeneratedEvent" conteniendo:
  | Campo              | Origen/Valor                                      |
  | response           | El texto de la respuesta ("speech")               |
  | plugin             | El nombre del plugin usado ("plugin_used")        |
  | confidence         | La confianza del último paso ejecutado            |
  | timestamp          | Fecha y hora UTC del sistema                      |
  | correlation_id     | ID de correlación asociado a la interacción       |
  | execution_time_ms  | Tiempo empleado en la ejecución en milisegundos   |
  | channel            | Canal de entrada (ej: "voice")                    |
  | metadata           | Diccionario de metadatos adicionales del contexto |
Y debe publicar el evento asíncronamente bajo el subject "orchestrator.response.generated" antes de responder al cliente HTTP
```

### Escenario 3: Desconexión ordenada del broker durante el apagado
```gherkin
Dado que el Orchestrator está en ejecución y conectado al Event Bus
Cuando se recibe una señal de parada del contenedor (teardown/shutdown)
Entonces el Orchestrator debe invocar el método de desconexión del Event Bus
Y debe cerrar ordenadamente la conexión TCP con NATS antes de finalizar el proceso
```

### Escenario 4: Resiliencia ante fallos del broker NATS
```gherkin
Dado que el broker NATS no está disponible o la conexión se interrumpe
Cuando el Orchestrator procesa una petición y genera una respuesta exitosa
Entonces el intento de publicar "ResponseGeneratedEvent" lanzará un error "EventBusConnectionError"
Y el Orchestrator debe capturar esta excepción y registrar un mensaje de advertencia (warning/error) en logs
Y debe devolver la respuesta HTTP con éxito al cliente con el código y payload idénticos al caso feliz
```

### Escenario 5: Compatibilidad hacia atrás de peticiones antiguas sin correlation_id ni channel
```gherkin
Dado que un cliente antiguo realiza una petición HTTP "POST /api/v1/resolve" con un payload que carece de los campos "correlation_id" y "channel"
Cuando la petición es recibida por el Orchestrator
Entonces la validación Pydantic debe superar el parsing asumiendo correlation_id=None y channel="voice"
Y el planificador debe generar un UUID aleatorio para rellenar el "correlation_id" y propagarlo al "PluginContext"
Y el flujo de enrutamiento y ejecución debe completarse con éxito publicando el evento con dicho UUID
```

---

## 4. Diseño Técnico y Contratos

### Definición del Evento (`core/events.py` - English)
```python
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any
from nova_event_bus import Event, event

@event("orchestrator.response.generated")
@dataclass
class ResponseGeneratedEvent(Event):
    response: str
    plugin: str
    confidence: float
    timestamp: datetime
    correlation_id: str
    execution_time_ms: int
    channel: str
    metadata: Dict[str, Any]
```

### Modelos de Datos Actualizados (`core/models.py` - English)
```python
from pydantic import BaseModel
from typing import Dict, Any, List, Optional

class UserRequest(BaseModel):
    text: str
    timestamp: Optional[float] = None
    correlation_id: Optional[str] = None
    channel: Optional[str] = "voice"

class PluginContext(BaseModel):
    raw_text: str
    normalized_text: str
    correlation_id: Optional[str] = None
    channel: Optional[str] = "voice"
    metadata: Dict[str, Any] = {}
```

### Inicialización en lifespan (`main.py` - English)
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Initializing Orchestrator...")
    
    # Initialize and connect Event Bus
    from nova_event_bus import NatsEventBus
    event_bus = NatsEventBus()
    try:
        await event_bus.connect()
        logger.info("Successfully connected to Event Bus.")
    except Exception as exc:
        logger.error(f"Failed to connect to Event Bus during startup: {exc}", exc_info=True)
    
    app.state.event_bus = event_bus
    
    # Rest of initialization...
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestrator...")
    try:
        await event_bus.disconnect()
        logger.info("Successfully disconnected from Event Bus.")
    except Exception as exc:
        logger.error(f"Error disconnecting from Event Bus during shutdown: {exc}", exc_info=True)
        
    plugin_manager.teardown()
```

### Publicación de Evento en `PlanExecutor` (`core/engine.py` - English)
```python
from datetime import datetime, timezone
from typing import Optional
from nova_event_bus import EventBusInterface
from core.events import ResponseGeneratedEvent

class PlanExecutor:
    def __init__(self, plugin_manager: PluginManager, event_bus: Optional[EventBusInterface] = None):
        self.plugin_manager = plugin_manager
        self.event_bus = event_bus

    async def execute_plan(self, plan: ExecutionPlan) -> AssistantResponse:
        import time
        start_time = time.time()
        
        last_plugin_name = "None"
        last_speech = ""
        success = True
        
        for step in plan.steps:
            plugin = self.plugin_manager.get_plugin(step.plugin)
            if not plugin:
                logger.error(f"Plugin {step.plugin} not found in execution plan.")
                raise PluginNotFoundError(f"El plugin '{step.plugin}' no está registrado en el sistema.")
            
            last_plugin_name = plugin.name
            try:
                result = await plugin.execute(step.context)
                last_speech = result.speech
                if not result.success:
                    logger.warning(f"Plugin {plugin.name} execution failed.")
                    success = False
                    break
            except Exception as e:
                logger.error(f"Exception during execution of plugin {plugin.name}: {e}", exc_info=True)
                success = False
                last_speech = "Ha ocurrido un error interno al ejecutar la acción."
                break
                
        execution_time = int((time.time() - start_time) * 1000)
        
        response = AssistantResponse(
            success=success,
            plugin_used=last_plugin_name,
            speech=last_speech,
            execution_time_ms=execution_time
        )
        
        # Publish event if execution succeeded and event bus is available
        if success and self.event_bus:
            try:
                correlation_id = None
                channel = "voice"
                confidence = 0.0
                metadata = {}
                
                if plan.steps:
                    last_step = plan.steps[-1]
                    correlation_id = last_step.context.correlation_id
                    channel = last_step.channel or last_step.context.channel or "voice"
                    confidence = last_step.confidence or 0.0
                    metadata = last_step.context.metadata
                
                import uuid
                if not correlation_id:
                    correlation_id = str(uuid.uuid4())
                
                event = ResponseGeneratedEvent(
                    response=response.speech,
                    plugin=response.plugin_used,
                    confidence=confidence,
                    timestamp=datetime.now(timezone.utc),
                    correlation_id=correlation_id,
                    execution_time_ms=response.execution_time_ms,
                    channel=channel,
                    metadata=metadata
                )
                await self.event_bus.publish(event)
                logger.info(f"Published ResponseGeneratedEvent (correlation_id={correlation_id})")
            except Exception as exc:
                logger.error(f"Failed to publish ResponseGeneratedEvent: {exc}", exc_info=True)
                
        return response
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **NATS desconectado al arrancar** | El orquestador arranca normalmente, registrando un error pero sin bloquear el ciclo de vida de FastAPI. | El bloque `try-except` en el callback de startup de lifespan previene la propagación de la excepción hacia el servidor uvicorn. |
| **Caída de NATS en caliente** | Las peticiones siguen funcionando. El intento de publicación del evento falla de manera segura. | En `execute_plan`, se encapsula la llamada a `publish` en un bloque `try-except Exception` que registra el error en log a nivel `error` y permite el flujo de retorno HTTP normal. |
| **Petición vacía (Fallback directo)** | Se genera el evento de igual forma asociándolo al `FallbackPlugin`. | En `ExecutionPlanner.resolve`, si el texto es vacío se crea una respuesta de Fallback con `confidence=0.0`, y el `PlanExecutor` publica el evento asociando `plugin="FallbackPlugin"`. |
| **Ausencia de `correlation_id`** | Se genera un ID de correlación único en la resolución para rastrear el ciclo de vida de la petición. | Se verifica si `UserRequest.correlation_id` es nulo; si lo es, se genera mediante `str(uuid.uuid4())` y se asocia a la instancia de `PluginContext`. |
| **Múltiples pasos en el plan** | Se utiliza la información del último paso de ejecución para mapear el evento de respuesta global. | Se extraen los atributos de contexto del último elemento de la lista `plan.steps` para construir el evento de salida. |

---

## 6. Estrategia de Testing

### Tests de Integración local y Unitarios
1. **Mocking de Lifespan (`tests/conftest.py`)**:
   - Se debe evitar que los tests unitarios intenten conectarse a un servidor NATS real en el host. Se parchearán los métodos `connect` y `disconnect` del cliente `NatsEventBus` para que actúen como noops asíncronos (`AsyncMock`).
2. **Suite de Publicación (`tests/test_event_publishing.py`)**:
   - **Caso Feliz**: Enviar una petición a `/api/v1/execute-plan` con un plan mockeado y verificar que se realiza exactamente una llamada a `publish` en el mock del event bus, comprobando que los datos serializados (response, plugin, correlation_id, channel, etc.) coinciden con lo esperado.
   - **Caso Fallido de NATS**: Configurar el mock de `publish` para que lance `EventBusConnectionError` y comprobar que la llamada al endpoint de ejecución devuelve un código 200 HTTP normal con la respuesta generada por los plugins, sin propagar el fallo.
   - **Caso Retrocompatibilidad**: Enviar un JSON de petición HTTP al endpoint `/api/v1/resolve` omitiendo `correlation_id` y `channel`, y validar que la respuesta HTTP se genera con éxito. Validar en un test unitario que el planificador genera un UUID aleatorio y lo propaga en el contexto.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Configuración de Dependencias**
  - [ ] Añadir la dependencia en `requirements.txt`:
    ```
    nova-event-bus @ git+https://github.com/danuser2018/nova-event-bus.git@v1.0.0
    ```
  - [ ] En desarrollo local, permitir la instalación en modo editable de forma aislada para pruebas unitarias:
    ```bash
    pip install -e ../nova-event-bus
    ```
- [ ] **Fase 2: Definición de Modelos y Contratos**
  - [ ] Crear el fichero `core/events.py` que contenga la estructura del evento `ResponseGeneratedEvent` registrada bajo el subject `"orchestrator.response.generated"`.
  - [ ] Modificar `core/models.py` para añadir `correlation_id` (str, opcional) y `channel` (str, opcional, por defecto "voice") a `UserRequest` y `PluginContext`.
  - [ ] Crear un nuevo ADR local (`doc/adr/adr-005-adicion-correlation-id-y-channel-userrequest.md`) para documentar y justificar la adición de los nuevos campos de correlación y canal en el modelo `UserRequest` de la API.
- [ ] **Fase 3: Modificación del Ciclo de Vida del Servicio (Lifespan)**
  - [ ] Modificar `main.py` para inicializar el cliente `NatsEventBus`, asignarlo al estado de la aplicación (`app.state.event_bus`) y gestionar la llamada a `connect` y `disconnect` en el lifespan capturando excepciones de conexión de forma resiliente.
- [ ] **Fase 4: Adaptación del Core del Motor (Planner y Executor)**
  - [ ] Modificar `core/engine.py`:
    - [ ] Actualizar `ExecutionPlanner.resolve` para generar un UUID aleatorio si `correlation_id` no viene provisto en la petición original, y propagar ambos campos (`correlation_id` y `channel`) a la inicialización de `PluginContext`.
    - [ ] Actualizar `PlanExecutor` para aceptar `event_bus` en su constructor.
    - [ ] Modificar `PlanExecutor.execute_plan` de modo que si la ejecución del plan finaliza con éxito (`success=True`), se extraigan los datos de correlación y contexto del paso correspondiente, se instancie `ResponseGeneratedEvent` y se publique a través del event bus atrapando de forma segura cualquier excepción durante la publicación.
  - [ ] Modificar `main.py` para pasar `app.state.event_bus` al inicializar `PlanExecutor` en el hook de startup.
- [ ] **Fase 5: Infraestructura de Pruebas**
  - [ ] Modificar `tests/conftest.py` para interceptar e inyectar mocks asíncronos en los métodos de conexión del Event Bus, previniendo fallos por ausencia de broker real en el entorno local de testing.
  - [ ] Crear la suite `tests/test_event_publishing.py` con las validaciones de publicación de evento, propagación de ID de correlación, canal y tests de resiliencia ante errores de publicación.
  - [ ] Ejecutar localmente `PYTHONPATH=. pytest` y asegurar el paso de todos los casos de prueba nuevos y existentes.
- [ ] **Fase 6: Puesta en Producción y Orquestación**
  - [ ] Modificar `/home/danuser2018/workspace/home-assistant/docker-compose.yml` para añadir `NATS_URL: nats://nats:4222` bajo el bloque de entorno de `orchestrator` (como variable de infraestructura inline según ADR-010), y configurar el servicio `nats` en la sección `depends_on`.
- [ ] **Fase 7: Documentación y Control de Cambios**
  - [ ] Actualizar el archivo `CHANGELOG.md` del orquestador en la sección `[Sin publicar]` detallando la adopción del event bus para publicar respuestas generadas y los cambios de retrocompatibilidad.
  
