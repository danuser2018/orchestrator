# Refinamiento de la Feature: Eliminación del mecanismo legado de selección de plugins (Fase 3)

- **Archivo de origen**: [remove_legacy_plugin_selection_process.md](file:///home/danuser2018/workspace/orchestrator/doc/features/remove_legacy_plugin_selection_process.md)
- **Fecha**: 2026-07-03
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Eliminar completamente la deuda técnica asociada al mecanismo de enrutamiento y selección legado basado en palabras clave (`keywords`) y expresiones regulares (`regex_patterns` / `exclusive_regex`) en el servicio `orchestrator`. A partir de esta fase, el sistema consolidará de manera exclusiva el motor de matching basado en similitud semántica determinista y desempate por prioridad (Fase 2) como la única vía oficial para resolver las intenciones del usuario.

### Actores y Reglas de Negocio
1. **Desarrollador de Plugins**: Desarrolla plugins declarando únicamente las propiedades esenciales (`name`, `description`, `id`, `priority` y `examples`), reduciendo la complejidad cognitiva y evitando la sobrecarga de prever expresiones regulares complejas o listas propensas a colisiones de palabras clave.
2. **Orchestrator**: Carga los plugins dinámicamente utilizando el `PluginManager` y selecciona la capacidad adecuada usando exclusivamente la similitud semántica contra la lista de frases de ejemplo (`examples`) de los plugins activos (excluyendo el `FallbackPlugin`), resolviendo empates por `priority`.
3. **Clase Base Plugin**: Se limpia de toda referencia y lógica relacionada con las propiedades deprecadas y sus correspondientes logs de advertencia.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `plugins/base.py`: Eliminar las propiedades obsoletas `keywords`, `regex_patterns` y `exclusive_regex`, junto con sus respectivas advertencias de obsolescencia (`warnings.warn`).<br>- `plugins/greeting/main.py`, `plugins/capabilities/main.py`, `plugins/farewell/main.py`, `plugins/weather/main.py`, `plugins/fallback/main.py`, `plugins/identity/main.py`: Remover las declaraciones y métodos de las propiedades `keywords` y `regex_patterns` (o cualquier otra propiedad legada similar).<br>- `tests/test_plugin_manager.py`: Eliminar la aserción `assert "tiempo" in weather_plugin.keywords` en `test_plugin_manager_loads_plugins`.<br>- `tests/test_greeting_plugin.py`: Eliminar el caso de test `test_greeting_plugin_keywords_and_regex`.<br>- `tests/test_identity_plugin.py`: Eliminar el caso de test `test_identity_plugin_keywords_and_regex`.<br>- `tests/test_farewell_plugin.py`: Eliminar el caso de test `test_farewell_plugin_keywords_and_regex`.<br>- `tests/test_capabilities_plugin.py`: Eliminar aserciones de `keywords` en `test_capabilities_plugin_metadata` y la validación de `regex_patterns` en `test_capabilities_plugin_properties`.<br>- `README.md`: Actualizar la interfaz base `Plugin`, remover las referencias y código de ejemplo de keywords/regex del ejemplo `WeatherPlugin`, y actualizar las secciones de explicación técnica del Router.<br>- `CHANGELOG.md`: Añadir un registro en la sección `[Sin publicar]` detallando la remoción total de la lógica de enrutamiento legada. |
| `home-assistant` | Modificar | - `docs/architecture.md`: Actualizar la descripción del rol de `orchestrator` en la sección de "Descripción de Componentes" para eliminar las menciones a keywords y expresiones regulares, alineándolo exclusivamente con el enrutamiento por similitud semántica y prioridad.<br>- `docs/troubleshooting.md`: Modificar la causa común 1 de la sección 10 ("El asistente responde 'no he entendido' a todo") para reemplazar la mención de keywords por la falta de similitud textual suficiente con las frases de ejemplo de los plugins.<br>- `.agent/skills/domains/plugin-domain/SKILL.md`: Actualizar la sección `Responsabilidades` para eliminar la mención a "coincidencia de keywords/regex" y sustituirla por "matching por similitud semántica determinista (RapidFuzz)", en cumplimiento de la regla de Sincronización de referencias en Skills de la skill `architecture-decisions`.<br>- `CONTRIBUTING.md`: **Sin impacto verificado.** El fichero no contiene referencias al modelo de selección legado (keywords/regex). No requiere modificación. |
| Todos los demás servicios | Ninguno | Las interfaces HTTP REST públicas y el flujo síncrono de ejecución de audio y orquestación externa no sufren alteraciones. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
Conforme a la skill `architecture-decisions`, la eliminación del código obsoleto representa una refactorización interna y una simplificación de código que no altera la topología física, los límites de servicios ni los contratos de red ya acordados en el `ADR-004` local de `orchestrator`. Por lo tanto, no se requiere la creación de un nuevo ADR global ni local, siendo suficiente con actualizar el historial de cambios y la documentación existente para reflejar el estado limpio del sistema.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Carga limpia de plugins en el arranque
```gherkin
Dado que el PluginManager está inicializado y escanea la carpeta plugins
Cuando se descubre y carga cada plugin en memoria
Entonces la inicialización se completa con éxito sin emitir advertencias de tipo DeprecationWarning
Y ninguna de las instancias de los plugins cargados expone los atributos keywords o regex_patterns
```

### Escenario 2: Verificación de la eliminación de propiedades legadas mediante test unitario
```gherkin
Dado que las propiedades keywords, regex_patterns y exclusive_regex han sido eliminadas de plugins/base.py
Cuando un test unitario intenta acceder a cualquiera de dichas propiedades sobre una instancia de Plugin
  usando pytest.raises(AttributeError)
Entonces el intérprete de Python lanza una excepción AttributeError
Y el test finaliza con estado de éxito (Passed)
```

### Escenario 3: Verificación de la suite de pruebas unitarias
```gherkin
Dado que la suite de pruebas se ha limpiado de aserciones de palabras clave y expresiones regulares
Y todos los tests que verificaban propiedades legadas han sido previamente eliminados de la suite
Cuando se ejecuta la suite completa de pruebas unitarias mediante pytest
Entonces todas las pruebas finalizan con estado de éxito (Passed)
```

### Escenario 4: Verificación de la documentación actualizada
```gherkin
Dado que el README.md del orchestrator y los documentos de arquitectura global han sido actualizados
Cuando un desarrollador consulta la sección de interfaz base del plugin o las guías de creación de plugins
Entonces no existe ninguna referencia a las propiedades keywords, regex_patterns ni exclusive_regex
  en los ejemplos de código ni en la descripción de la interfaz
```

---

## 4. Diseño Técnico y Contratos

### Contrato de la Interfaz Base `Plugin` (`plugins/base.py`)
El contrato resultante de la clase abstracta `Plugin` se simplifica para eliminar las referencias legadas:

```python
from abc import ABC, abstractmethod
from typing import List
from core.models import PluginContext, PluginResult

class Plugin(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
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

    def initialize(self) -> None:
        pass

    def teardown(self) -> None:
        pass

    def __getattribute__(self, name: str):
        val = super().__getattribute__(name)
        if name == "examples" and isinstance(val, list):
            return [e for e in val if isinstance(e, str) and e.strip()]
        return val

    @abstractmethod
    async def execute(self, context: PluginContext) -> PluginResult:
        pass
```

### Interfaces REST Públicas
No hay cambios en los esquemas de entrada/salida de la API del `orchestrator` (`POST /api/v1/execute`).

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Plugins externos o de terceros que intenten declarar `keywords` o `regex_patterns`** | Al no estar definidas en la clase base, no tendrán efecto en el enrutamiento del `PluginMatcher`. | Se documenta como cambio disruptivo (Breaking Change) en el `CHANGELOG.md` y `README.md`. |
| **Inconsistencias en guías técnicas de desarrollador** | Evitar que nuevos desarrolladores usen la nomenclatura vieja basándose en documentación desactualizada. | Actualizar el `README.md` del orquestador y los archivos de documentación global del repositorio `home-assistant`. |
| **Acceso por reflexividad en pruebas antiguas** | Que queden referencias a keywords/regex en pruebas que no fueron modificadas. | Limpieza exhaustiva de todos los ficheros de pruebas bajo el directorio `tests/` del orquestador. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias
1. **Verificación de Descubrimiento de Plugins (`tests/test_plugin_manager.py`)**:
   - `test_plugin_manager_loads_plugins`: Modificar el test para comprobar el nombre, id, prioridad y ejemplos del `WeatherPlugin` sin hacer referencias a su propiedad `keywords`.
2. **Alineación de Tests de Plugins Individuales**:
   - `tests/test_greeting_plugin.py`: Eliminar `test_greeting_plugin_keywords_and_regex` y mantener la verificación de propiedades básicas (`test_greeting_plugin_properties`) y de ejecución (`test_greeting_plugin_execution`).
   - `tests/test_identity_plugin.py`: Eliminar `test_identity_plugin_keywords_and_regex` y mantener el resto de tests de conectividad y formato de versión.
   - `tests/test_farewell_plugin.py`: Eliminar `test_farewell_plugin_keywords_and_regex`.
   - `tests/test_capabilities_plugin.py`: Limpiar `test_capabilities_plugin_metadata` de la comprobación de `keywords` y eliminar `test_capabilities_plugin_properties` en su validación de expresiones regulares de entrada.

### Verificación local
- Se ejecutará la suite completa mediante el comando:
  ```bash
  PYTHONPATH=. pytest
  ```
  Asegurando que el 100% de los tests pasan con éxito.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Limpieza del contrato y plugins en `orchestrator`**
  - [ ] Modificar [plugins/base.py](file:///home/danuser2018/workspace/orchestrator/plugins/base.py) para remover las propiedades `keywords`, `regex_patterns` y `exclusive_regex`, junto con el import de `warnings`.
  - [ ] Modificar [plugins/greeting/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/greeting/main.py) para eliminar `keywords` y `regex_patterns`.
  - [ ] Modificar [plugins/capabilities/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/capabilities/main.py) para eliminar `keywords` y `regex_patterns`.
  - [ ] Modificar [plugins/farewell/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/farewell/main.py) para eliminar `keywords` y `regex_patterns`.
  - [ ] Modificar [plugins/weather/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/weather/main.py) para eliminar `keywords` y `regex_patterns`.
  - [ ] Modificar [plugins/fallback/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/fallback/main.py) para eliminar `keywords` y `regex_patterns`.
  - [ ] Modificar [plugins/identity/main.py](file:///home/danuser2018/workspace/orchestrator/plugins/identity/main.py) para eliminar `keywords` y `regex_patterns`.
- [ ] **Fase 2: Adaptación de la suite de pruebas**
  - [ ] Modificar [tests/test_plugin_manager.py](file:///home/danuser2018/workspace/orchestrator/tests/test_plugin_manager.py) para remover la aserción sobre keywords.
  - [ ] Modificar [tests/test_greeting_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_greeting_plugin.py) para remover el test de keywords/regex.
  - [ ] Modificar [tests/test_identity_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_identity_plugin.py) para remover el test de keywords/regex.
  - [ ] Modificar [tests/test_farewell_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_farewell_plugin.py) para remover el test de keywords/regex.
  - [ ] Modificar [tests/test_capabilities_plugin.py](file:///home/danuser2018/workspace/orchestrator/tests/test_capabilities_plugin.py) para remover las aserciones sobre keywords/regex.
- [ ] **Fase 3: Actualización de documentación**
  - [ ] Modificar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) para reflejar la clase base limpia y remover keywords/regex del ejemplo del plugin.
  - [ ] Modificar [docs/architecture.md](file:///home/danuser2018/workspace/home-assistant/docs/architecture.md) en `home-assistant` para actualizar la descripción del rol del Orchestrator.
  - [ ] Modificar [docs/troubleshooting.md](file:///home/danuser2018/workspace/home-assistant/docs/troubleshooting.md) en `home-assistant` para actualizar las causas comunes del Fallback en la sección 10.
  - [ ] Modificar [CHANGELOG.md](file:///home/danuser2018/workspace/orchestrator/CHANGELOG.md) para añadir la nota de remoción del mecanismo legado.
  - [ ] Modificar [.agent/skills/domains/plugin-domain/SKILL.md](file:///home/danuser2018/workspace/home-assistant/.agent/skills/domains/plugin-domain/SKILL.md) en `home-assistant` para actualizar la sección `Responsabilidades`, eliminando la referencia a "coincidencia de keywords/regex" y sustituyéndola por "matching por similitud semántica determinista (RapidFuzz)".
