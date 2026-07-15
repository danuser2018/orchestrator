# Refinamiento de la Feature: Consolidación del modelo ExecutionPlan y eliminación del endpoint legado

- **Archivo de origen**: [remove_legacy_endpoint.md](file:///home/danuser2018/workspace/orchestrator/doc/features/remove_legacy_endpoint.md)
- **Fecha**: 2026-07-15
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Consolidar definitivamente el flujo de procesamiento desacoplado en el servicio `orchestrator` introducido en el ADR-014. Esto implica la eliminación completa del endpoint de compatibilidad legado `POST /api/v1/execute` y su lógica interna asociada (`resolve() -> execute_plan()`), estableciendo el modelo basado en `ExecutionPlan` como el contrato único y central del sistema. Asimismo, se alineará la nomenclatura interna del código fuente renombrando los componentes clave (`IntentResolver` pasará a ser `ExecutionPlanner`, y `PluginExecutor` pasará a ser `PlanExecutor`) y eliminando el componente de compatibilidad obsoleto `Router`.

### Actores y Reglas de Negocio
1. **Interaction Manager**: Actúa como el cliente exclusivo del orquestador, invocando de forma desacoplada los endpoints `POST /api/v1/resolve` para planificar y `POST /api/v1/execute-plan` para ejecutar el plan resultante.
2. **ExecutionPlanner (anteriormente IntentResolver)**: Clase interna del orquestador responsable de analizar la petición del usuario (`UserRequest`), normalizar el texto, calcular las similitudes semánticas frente a las frases de ejemplo de los plugins y generar un `ExecutionPlan`.
3. **PlanExecutor (anteriormente PluginExecutor)**: Clase interna del orquestador encargada de recibir un `ExecutionPlan` estructurado, validar la disponibilidad de los plugins y ejecutar secuencialmente cada uno de sus pasos, deteniéndose ante cualquier fallo.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `core/engine.py`: Renombrar `IntentResolver` -> `ExecutionPlanner` y `PluginExecutor` -> `PlanExecutor`. Eliminar la clase obsoleta `Router` y su método `route_request`. <br>- `core/api.py`: Eliminar el endpoint `POST /api/v1/execute` y su handler. Actualizar los handlers `/resolve` y `/execute-plan` para utilizar los nuevos nombres de clase e inyecciones de estado (`planner` en lugar de `resolver`).<br>- `main.py`: Importar y registrar en `app.state` las instancias con los nuevos nombres (`app.state.planner` y `app.state.executor`). <br>- `tests/test_resolver.py`: Renombrar el archivo a `test_planner.py` y actualizar las referencias internas de `IntentResolver` a `ExecutionPlanner` y de `resolver` a `planner`.<br>- `tests/test_executor.py`: Actualizar las referencias internas de `PluginExecutor` a `PlanExecutor` y de `executor` a `executor` (manteniendo coherencia semántica).<br>- `tests/test_api.py`: Eliminar todos los tests que verifiquen el funcionamiento o la propagación de errores en el endpoint `/execute` (ej. `test_execute_weather`, `test_execute_greetings`, etc.).<br>- `tests/test_engine.py`: Adaptar la suite de pruebas para verificar el comportamiento de `ExecutionPlanner.resolve` en lugar de `Router.route_request`.<br>- `tests/test_routing.py`: Adaptar todos los tests de enrutamiento de plugins para verificar los planes resueltos por `ExecutionPlanner.resolve` en lugar de `Router.route_request`.<br>- `README.md`: Eliminar las referencias a `/api/v1/execute` y documentar la arquitectura actualizada basada en `ExecutionPlanner` y `PlanExecutor`.<br>- `CHANGELOG.md`: Añadir un registro en la sección `[Sin publicar]` detallando los cambios destructivos en la API y los cambios de nomenclatura interna. |
| `home-assistant` | Modificar | - `docs/architecture.md`: Actualizar el diagrama de secuencia para mostrar la comunicación explícita usando `POST /api/v1/resolve` seguido de `POST /api/v1/execute-plan`. Actualizar la descripción del orquestador en la sección "Descripción de Componentes" reemplazando `IntentResolver` y `PluginExecutor` por `ExecutionPlanner` y `PlanExecutor`, y remover el endpoint `/execute` de su API.<br>- `docs/services.md`: Eliminar la sección y el ejemplo de payload correspondiente al endpoint `POST /api/v1/execute`.<br>- `CHANGELOG.md`: Añadir un registro en la sección `[Sin publicar]` indicando la consolidación de la API del orquestador.<br>- `docs/adr/adr-015-consolidacion-execution-plan.md` **[Nuevo]**: Crear un nuevo ADR que registre formalmente la consolidación del modelo `ExecutionPlan`, la remoción de compatibilidad hacia atrás (`POST /api/v1/execute` y clase `Router`) y el renombrado de las clases internas.<br>- `.agent/skills/transversal/api-contracts/SKILL.md`: Añadir una referencia enlazando al nuevo `ADR-015`.<br>- `.agent/skills/transversal/service-responsibilities/SKILL.md`: Añadir una referencia enlazando al nuevo `ADR-015`. |
| Todos los demás | Ninguno | `interaction-manager` ya consume la API desacoplada, por lo que no hay impacto operacional en otros servicios del ecosistema. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
De acuerdo con las reglas de la skill `architecture-decisions`, la eliminación del endpoint público `/api/v1/execute` altera la interfaz pública de comunicación y el contrato del microservicio (`api-contracts`). Por tanto, **es obligatorio crear un nuevo ADR global** (`adr-015-consolidacion-execution-plan.md`) en el repositorio `home-assistant`. Este nuevo ADR establecerá de forma permanente el flujo en dos pasos como el único soportado por el ecosistema y declarará obsoleta la compatibilidad anterior descrita en `ADR-014`.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Petición a endpoint eliminado devuelve 404 Not Found
```gherkin
Dado que el microservicio orchestrator está en ejecución
Cuando un cliente envía una petición HTTP POST a "/api/v1/execute" con un payload de tipo UserRequest
Entonces el servidor responde con un código de estado HTTP 404 Not Found
Y la petición no es procesada por ninguna clase interna
```

### Escenario 2: Generación exitosa de plan de ejecución mediante ExecutionPlanner
```gherkin
Dado que el ExecutionPlanner está inicializado con un PluginManager cargado
Cuando se llama a resolver un UserRequest válido con texto "hola"
Entonces se genera una instancia de ExecutionPlan
Y el plan contiene un único paso (ExecutionPlanStep) con plugin igual a "GreetingPlugin"
Y la confianza (confidence) es mayor o igual al umbral de similitud configurado
```

### Escenario 3: Ejecución correcta del plan mediante PlanExecutor
```gherkin
Dado que el PlanExecutor está inicializado
Y recibe un ExecutionPlan estructurado con un paso para "GreetingPlugin"
Cuando se invoca el método execute_plan
Entonces se ejecuta secuencialmente el plugin GreetingPlugin
Y el resultado es un AssistantResponse exitoso (success=True) conteniendo la respuesta del plugin
```

### Escenario 4: Inicialización del sistema con la nueva nomenclatura
```gherkin
Dado que la aplicación principal del orquestador se inicia mediante FastAPI
Cuando se ejecuta el ciclo de vida lifespan de la aplicación
Entonces se instancian correctamente ExecutionPlanner y PlanExecutor
Y se registran en app.state con los nombres "planner" y "executor" respectivamente
Y el servidor inicia y escucha en el puerto configurado sin errores
```

### Escenario 5: Manejo de plan de ejecución vacío o sin pasos en PlanExecutor
```gherkin
Dado que el PlanExecutor está inicializado
Cuando se invoca el método execute_plan con un ExecutionPlan con cero pasos (steps vacío)
Entonces el método retorna un AssistantResponse con success=True y speech vacío sin lanzar ninguna excepción
```

---

## 4. Diseño Técnico y Contratos

### Contratos de Clases Internas (`core/engine.py`)

#### Clase `ExecutionPlanner` (anteriormente `IntentResolver`)
```python
class ExecutionPlanner:
    def __init__(
        self, 
        plugin_manager: PluginManager, 
        similarity_engine: SimilarityEngine,
        similarity_threshold: float = settings.similarity_threshold,
        tie_breaker_threshold: float = settings.tie_breaker_threshold
    ):
        self.plugin_manager = plugin_manager
        self.similarity_engine = similarity_engine
        self.similarity_threshold = similarity_threshold
        self.tie_breaker_threshold = tie_breaker_threshold

    def normalize_text(self, text: str) -> str:
        """Normaliza el texto quitando acentos, caracteres especiales y convirtiendo a minúsculas."""
        ...

    async def resolve(self, request: UserRequest) -> ExecutionPlan:
        """Calcula similitudes de ejemplo y genera el plan correspondiente."""
        ...
```

#### Clase `PlanExecutor` (anteriormente `PluginExecutor`)
```python
class PlanExecutor:
    def __init__(self, plugin_manager: PluginManager):
        self.plugin_manager = plugin_manager

    async def execute_plan(self, plan: ExecutionPlan) -> AssistantResponse:
        """Ejecuta secuencialmente los pasos del plan y recopila las respuestas."""
        ...
```

### Rutas de la API de FastAPI (`core/api.py`)

```python
from fastapi import APIRouter, Request
from .models import UserRequest, AssistantResponse, ExecutionPlan
from .engine import ExecutionPlanner, PlanExecutor

router = APIRouter()

@router.post("/resolve", response_model=ExecutionPlan)
async def resolve_intent(request: Request, user_request: UserRequest):
    planner: ExecutionPlanner = request.app.state.planner
    plan = await planner.resolve(user_request)
    return plan

@router.post("/execute-plan", response_model=AssistantResponse)
async def execute_plan(request: Request, plan: ExecutionPlan):
    executor: PlanExecutor = request.app.state.executor
    response = await executor.execute_plan(plan)
    return response
```

> [!NOTE]
> El fragmento de código anterior representa el estado objetivo tras completar la Fase 2 del checklist. En particular, la actualización en `main.py` de `app.state.resolver` a `app.state.planner` y de `app.state.executor` a `app.state.executor` es una precondición indispensable para que las rutas expuestas en `core/api.py` funcionen correctamente.

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Llamada de cliente al endpoint legado `/execute`** | Debe fallar inmediatamente indicando recurso no encontrado. | Remoción física de la ruta en `core/api.py`. FastAPI lanza 404 de forma nativa. |
| **Plan vacío o sin pasos en ejecución** | Debe completarse con éxito indicando éxito y devolviendo un speech vacío o fallback. | Validar longitud de pasos en `PlanExecutor.execute_plan`. Si es cero, retornar un `AssistantResponse` vacío de forma controlada. |
| **Plugin del plan no registrado** | Debe lanzar un error HTTP 400. | `PlanExecutor` lanza `PluginNotFoundError` que es capturado y mapeado a HTTP 400 por el exception handler global en `main.py`. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias e Integración Locales
1. **Pruebas del Planificador (`tests/test_planner.py`)**:
   - Reemplazar el fixture `resolver` por `planner` instanciando `ExecutionPlanner`.
   - Modificar las aserciones de llamadas a `resolver.resolve` y verificar que retornan el `ExecutionPlan` adecuado.
2. **Pruebas del Ejecutor (`tests/test_executor.py`)**:
   - Reemplazar las instancias de `PluginExecutor` por `PlanExecutor`.
   - Verificar la ejecución de mock plugins usando `PlanExecutor.execute_plan`.
3. **Pruebas de la API (`tests/test_api.py`)**:
   - Eliminar por completo todas las pruebas unitarias que llaman a `/api/v1/execute`.
   - Asegurar que existan pruebas válidas para `/api/v1/resolve` y `/api/v1/execute-plan`.
4. **Pruebas de Enrutamiento (`tests/test_routing.py` y `tests/test_engine.py`)**:
   - Cambiar la inicialización de `Router` por `ExecutionPlanner`.
   - Modificar las pruebas de `route_request` para invocar a `resolve` y verificar las propiedades del paso planificado.

### Comando de Verificación
La suite completa de tests debe ser ejecutada de manera exitosa desde el directorio raíz del proyecto:
```bash
PYTHONPATH=. pytest
```

---

## 7. Plan de Implementación (Checklist)

### Fase 1: Creación del ADR en `home-assistant`
- [ ] Crear el archivo [adr-015-consolidacion-execution-plan.md](file:///home/danuser2018/workspace/home-assistant/docs/adr/adr-015-consolidacion-execution-plan.md) formalizando la decisión arquitectónica.

### Fase 2: Refactorización de Clases e Interfaces en `orchestrator`
- [ ] Modificar [core/engine.py](file:///home/danuser2018/workspace/orchestrator/core/engine.py):
  - [ ] Cambiar nombre de `IntentResolver` a `ExecutionPlanner`.
  - [ ] Cambiar nombre de `PluginExecutor` a `PlanExecutor`.
  - [ ] Eliminar la clase obsoleta `Router`.
- [ ] Modificar [core/api.py](file:///home/danuser2018/workspace/orchestrator/core/api.py):
  - [ ] Eliminar el endpoint `POST /api/v1/execute`.
  - [ ] Actualizar las importaciones de `IntentResolver` y `PluginExecutor` a `ExecutionPlanner` y `PlanExecutor` en `core/api.py`.
  - [ ] Modificar `resolve_intent` para recuperar `request.app.state.planner` en lugar de `resolver`.
  - [ ] Modificar `execute_plan` para recuperar `request.app.state.executor` (actualizando la anotación de tipo a `PlanExecutor`).
- [ ] Modificar [main.py](file:///home/danuser2018/workspace/orchestrator/main.py):
  - [ ] Actualizar importaciones a `ExecutionPlanner` y `PlanExecutor`.
  - [ ] Asignar `app.state.planner` y `app.state.executor` en el ciclo de vida lifespan.

### Fase 3: Actualización de la Suite de Pruebas en `orchestrator`
- [ ] Renombrar [tests/test_resolver.py](file:///home/danuser2018/workspace/orchestrator/tests/test_resolver.py) a `tests/test_planner.py` y actualizar su contenido con `ExecutionPlanner` y `planner`.
- [ ] Modificar [tests/test_executor.py](file:///home/danuser2018/workspace/orchestrator/tests/test_executor.py) para usar `PlanExecutor`.
- [ ] Modificar [tests/test_api.py](file:///home/danuser2018/workspace/orchestrator/tests/test_api.py):
  - [ ] Eliminar los 9 tests antiguos relacionados con el endpoint `/execute`.
- [ ] Modificar [tests/test_engine.py](file:///home/danuser2018/workspace/orchestrator/tests/test_engine.py) para testear `ExecutionPlanner.resolve` en lugar de `Router.route_request`.
- [ ] Modificar [tests/test_routing.py](file:///home/danuser2018/workspace/orchestrator/tests/test_routing.py) para usar `ExecutionPlanner.resolve`.

### Fase 4: Actualización de Documentación y Metadatos de Skills
- [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en el orquestador para eliminar las referencias al endpoint legado y documentar los nuevos componentes.
- [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) en el orquestador registrando los cambios.
- [ ] Modificar [docs/architecture.md](file:///home/danuser2018/workspace/home-assistant/docs/architecture.md) en `home-assistant` actualizando el diagrama de secuencia y los componentes.
- [ ] Modificar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en `home-assistant` eliminando la referencia a `/execute`.
- [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/home-assistant/CHANGELOG.md) en `home-assistant`.
- [ ] Modificar [.agent/skills/transversal/api-contracts/SKILL.md](file:///home/danuser2018/workspace/hid-daemon/.agent/skills/transversal/api-contracts/SKILL.md) para añadir la referencia a `ADR-015`.
- [ ] Modificar [.agent/skills/transversal/service-responsibilities/SKILL.md](file:///home/danuser2018/workspace/hid-daemon/.agent/skills/transversal/service-responsibilities/SKILL.md) para añadir la referencia a `ADR-015`.

### Fase 5: Validación final
- [ ] Ejecutar la suite de pruebas completa: `PYTHONPATH=. pytest` en el orquestador.
