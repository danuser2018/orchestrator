# Refinamiento de la Feature: Incorporación de frases de ejemplo y prioridad en los plugins

- **Archivo de origen**: [plugins_examples_and_priority.md](file:///home/danuser2018/workspace/orchestrator/doc/features/plugins_examples_and_priority.md)
- **Fecha**: 2026-07-03
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Modificar el contrato público de la clase base `Plugin` y sus implementaciones concretas en el servicio `orchestrator` para introducir los campos declarativos de identificador único (`id`), nivel de prioridad (`priority`) y colección de frases de ejemplo de invocación del usuario (`examples`). 

### Actores y Reglas de Negocio
1. **Desarrollador de Plugins**: Declara de forma estática la prioridad y ejemplos de uso de la capacidad.
2. **Orchestrator (Fase 1)**: Durante esta fase, el motor de selección (`Router`) continuará utilizando el motor determinista actual basado en `keywords` y `regex_patterns`. Los nuevos atributos coexistirán pacíficamente sin alterar el enrutamiento. La inicialización del sistema (`main.py`) se beneficiará de la propiedad `id` para registrar las capacidades en el `system-service`.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `plugins/base.py`: Se añaden propiedades abstractas y con valores por defecto para `id`, `priority` y `examples`. <br> - Plugins individuales: Se actualiza cada plugin para implementar las nuevas propiedades. <br> - `main.py`: Se simplifica la lógica de registro de capacidades en `system-service` sustituyendo el parsing de nombres de clase por la propiedad `plugin.id`. <br> - `README.md`: Se actualizan los contratos de la clase base `Plugin` y del plugin de ejemplo (`WeatherPlugin`) para reflejar los nuevos atributos, y se documenta la tabla de prioridades para desarrolladores. <br> - Tests unitarios: Se amplía la suite de pruebas para verificar los nuevos atributos de cada plugin y evitar regresiones. |
| Todos los demás servicios | Ninguno | No se altera la API externa del `orchestrator` ni el payload enviado a `system-service` (ya que el ID resultante es idéntico al calculado anteriormente). |

> **Evaluación de necesidad de ADR:** Se ha analizado el impacto de esta feature conforme a la skill `architecture-decisions`. Los cambios introducidos son estrictamente internos al contrato de extensibilidad del `orchestrator` (clase base `Plugin`) y no alteran ninguna API pública entre servicios, ningún patrón de comunicación entre contenedores ni las responsabilidades de ningún componente del ecosistema. Se concluye que **no es necesario crear un nuevo ADR**.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Inicialización correcta de propiedades en plugins
```gherkin
Dado que el PluginManager carga los plugins del sistema
Cuando se inspecciona cualquier plugin activo en el sistema
Entonces el plugin debe exponer una propiedad "id" que retorne su identificador en minúsculas y sin el sufijo "plugin"
Y debe exponer una propiedad "priority" con un valor entero entre 0 y 100
Y debe exponer una lista de cadenas de texto en "examples" correspondientes a sus frases de ejemplo (o vacía si es el plugin de Fallback)
```

### Escenario 2: Publicación de capacidades en System Service usando ID nativo
```gherkin
Dado que el Orchestrator se inicializa correctamente
Cuando construye la lista de capacidades del sistema para registrar en System Service
Entonces utiliza el valor de la propiedad "id" de cada plugin en lugar de procesar el nombre de la clase
Y envía con éxito un payload JSON a POST /v1/system/capabilities con los IDs correctos
```

### Escenario 3: Compatibilidad hacia atrás del motor de selección
```gherkin
Dado que los plugins implementan las nuevas propiedades "id", "priority" y "examples"
Cuando el usuario envía una petición de texto como "hola"
Entonces el Router selecciona GreetingPlugin utilizando las palabras clave y expresiones regulares tradicionales
Y el enrutamiento y la ejecución de la petición funcionan exactamente de la misma manera que antes
```

### Escenario 4: Actualización de documentación técnica
```gherkin
Dado que la feature ha sido implementada
Cuando se consulta el README.md del orchestrator
Entonces la sección de Contratos incluye las propiedades "id", "priority" y "examples" en la definición de la clase base Plugin
Y el ejemplo completo de WeatherPlugin refleja los nuevos atributos
Y el CHANGELOG.md contiene una entrada en la sección "Sin publicar" describiendo los cambios introducidos por esta funcionalidad
```

---

## 4. Diseño Técnico y Contratos

### Contrato de la Clase Base `Plugin` (`plugins/base.py`)
```python
from abc import ABC, abstractmethod
from typing import List
from core.models import PluginContext, PluginResult

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of the plugin."""
        pass
        
    @property
    @abstractmethod
    def description(self) -> str:
        """Functional description of the capability."""
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

    @property
    def keywords(self) -> List[str]:
        return []

    @property
    def regex_patterns(self) -> List[str]:
        return []

    @property
    def exclusive_regex(self) -> str | None:
        return None

    def initialize(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
```

### Detalle de Atributos por Plugin

| Clase de Plugin | `id` | `priority` | `examples` |
| :--- | :--- | :--- | :--- |
| `GreetingPlugin` | `"greeting"` | `100` | Lista de 10 frases (ver abajo) |
| `FarewellPlugin` | `"farewell"` | `100` | Lista de 10 frases (ver abajo) |
| `WeatherPlugin` | `"weather"` | `80` | Lista de 10 frases (ver abajo) |
| `IdentityPlugin` | `"identity"` | `60` | Lista de 10 frases (ver abajo) |
| `CapabilitiesPlugin`| `"capabilities"` | `60` | Lista de 10 frases (ver abajo) |
| `FallbackPlugin` | `"fallback"` | `0` | `[]` (lista vacía) |

#### Frases de Ejemplo por Plugin

##### `GreetingPlugin`
```python
examples = [
    "Hola.",
    "Buenos días.",
    "Buenas tardes.",
    "Buenas noches.",
    "Hola, Nova.",
    "Buenos días, Nova.",
    "¿Hay alguien?",
    "¿Estás ahí?",
    "¿Me escuchas?",
    "Hola, ¿qué tal?"
]
```

##### `FarewellPlugin`
```python
examples = [
    "Adiós.",
    "Hasta luego.",
    "Hasta pronto.",
    "Nos vemos.",
    "Chao.",
    "Me voy.",
    "Eso es todo.",
    "Ya hemos terminado.",
    "Gracias, hasta luego.",
    "Puedes irte."
]
```

##### `WeatherPlugin`
```python
examples = [
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
```

##### `IdentityPlugin`
```python
examples = [
    "¿Quién eres?",
    "¿Cómo te llamas?",
    "¿Qué eres?",
    "Cuéntame quién eres.",
    "Preséntate.",
    "Háblame de ti.",
    "¿Eres una inteligencia artificial?",
    "¿Para qué sirves?",
    "¿Cuál es tu función?",
    "Dime quién eres."
]
```

##### `CapabilitiesPlugin`
```python
examples = [
    "¿Qué puedes hacer?",
    "¿En qué me puedes ayudar?",
    "¿Qué funciones tienes?",
    "¿Qué sabes hacer?",
    "Muéstrame tus capacidades.",
    "¿Qué comandos conoces?",
    "¿Qué cosas puedo pedirte?",
    "¿Cómo puedo usarte?",
    "¿Qué opciones tengo?",
    "Enséñame lo que puedes hacer."
]
```

##### `FallbackPlugin`
```python
examples = []
```

### Modificación en `main.py` (Carga de Capacidades)
```python
    capabilities = []
    for plugin in plugins:
        if plugin.id == "fallback":
            continue
            
        capabilities.append({
            "id": plugin.id,
            "description": plugin.description
        })
```

> **Nota (coherencia con ADR-003 del orchestrator):** El filtrado por `plugin.id == "fallback"` es el mecanismo oficial de exclusión del `FallbackPlugin` del registro de capacidades, conforme a lo establecido en [`ADR-003: Exclusión de FallbackPlugin del registro automático de capacidades`](file:///home/danuser2018/workspace/orchestrator/doc/adr/adr-003-exclusion-fallbackplugin-registro-capacidades.md). La propiedad `id = "fallback"` declarada en `FallbackPlugin` actúa como su identificador de contrato oficial. Para mayor robustez, la implementación en `core/plugin_manager.py` puede complementar este filtrado con una comprobación de tipo (`isinstance(plugin, FallbackPlugin)`) si en el futuro se incorporaran plugins de terceros que pudieran declarar accidentalmente el mismo identificador.

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Identificadores duplicados (`id`)** | El arranque debe fallar o emitir un error crítico si se registran dos plugins con el mismo `id` para evitar inconsistencias. | En `PluginManager._register_plugins_from_module`, verificar si ya existe un plugin registrado con el mismo `id` antes de añadirlo a `self.plugins`. Si existe, lanzar `ValueError`. |
| **Prioridad fuera de rango** | Las prioridades deben estar limitadas entre `0` y `100`. | Añadir una validación en la clase base `Plugin` o validar al instanciar. En Python, se puede realizar una validación en el `PluginManager` durante el registro de plugins: verificar que `0 <= plugin.priority <= 100`. Si no, lanzar `ValueError`. |
| **Frases vacías en examples** | Se deben ignorar las cadenas vacías o espacios en blanco dentro de la lista de ejemplos. | Al recuperar `plugin.examples`, filtrar elementos vacíos o que contengan solo espacios en blanco. |

---

## 6. Estrategia de Testing

### Tests Unitarios
1. **Validación de Contratos (`tests/test_plugin_manager.py`)**:
   - Añadir una prueba que valide que todos los plugins activos heredan de `Plugin` y exponen correctamente las propiedades `id`, `priority` y `examples` con los tipos y rangos adecuados.
   - Validar que intentar registrar un plugin con un `id` duplicado lanza una excepción `ValueError`.
   - Validar que un plugin con prioridad fuera de rango (ej. `-10` o `120`) genera un error al registrarse.
2. **Validación Individual por Plugin (`tests/test_*_plugin.py`)**:
   - Añadir asserts específicos en cada test de plugin para asegurar que `id`, `priority` y `examples` coinciden exactamente con los valores definidos en la tabla del diseño técnico.
3. **Validación del Registro en System Service (`tests/test_plugin_registration.py`)**:
   - Actualizar el mock del cliente de System Service y validar que el payload enviado utiliza `plugin.id` correctamente.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Definición del Contrato**
  - [ ] Modificar `plugins/base.py` para añadir las propiedades abstractas `id`, `priority` y `examples` con tipos definidos.
- [ ] **Fase 2: Actualización de Plugins Existentes**
  - [ ] Actualizar `plugins/greeting/main.py` (id="greeting", priority=100, examples=10 frases).
  - [ ] Actualizar `plugins/farewell/main.py` (id="farewell", priority=100, examples=10 frases).
  - [ ] Actualizar `plugins/weather/main.py` (id="weather", priority=80, examples=10 frases).
  - [ ] Actualizar `plugins/identity/main.py` (id="identity", priority=60, examples=10 frases).
  - [ ] Actualizar `plugins/capabilities/main.py` (id="capabilities", priority=60, examples=10 frases).
  - [ ] Actualizar `plugins/fallback/main.py` (id="fallback", priority=0, examples=[]).
- [ ] **Fase 3: Refactorización de Core y Validación en Carga**
  - [ ] Modificar `core/plugin_manager.py` para validar identificadores únicos y rango de prioridad (`0 <= priority <= 100`) durante el método `_register_plugins_from_module`. Lanzar `ValueError` si falla.
  - [ ] Modificar `main.py` para sustituir el parsing de string `name_lower.endswith("plugin")` por el uso directo de `plugin.id` al registrar capacidades.
- [ ] **Fase 4: Actualización y Ejecución de Pruebas**
  - [ ] Modificar y ampliar los tests unitarios (`tests/test_*_plugin.py`, `tests/test_plugin_manager.py`, y `tests/test_plugin_registration.py`).
  - [ ] Ejecutar la suite de pruebas local (`PYTHONPATH=. pytest`) y verificar que todos los casos pasan correctamente sin warnings imprevistos o errores.
- [ ] **Fase 5: Documentación**
  - [ ] Actualizar el archivo `README.md` del `orchestrator`:
    - [ ] Actualizar la definición del contrato de la clase base `Plugin` en la sección 7 ("Contratos") incluyendo `id`, `priority` y `examples`.
    - [ ] Actualizar el ejemplo completo de `WeatherPlugin` en la sección 15 para incorporar la definición de los nuevos atributos.
    - [ ] Documentar detalladamente los niveles de prioridad y las directrices para desarrolladores a la hora de asignar prioridades a nuevos plugins.
  - [ ] Actualizar el archivo `CHANGELOG.md` del `orchestrator` agregando una sección `Sin publicar` detallando los cambios introducidos por esta funcionalidad (nuevas propiedades de los plugins, validaciones del core y simplificación de `main.py`).
