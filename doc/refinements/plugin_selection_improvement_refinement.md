# Refinamiento de la Feature: Nuevo motor de selección de plugins basado en similitud (Fase 2)

- **Archivo de origen**: [plugin_selection_improvement.md](file:///home/danuser2018/workspace/orchestrator/doc/features/plugin_selection_improvement.md)
- **Fecha**: 2026-07-03
- **Estado**: Refinado

---

## 1. Resumen y Contexto de Negocio

### Objetivo Principal
Sustituir el mecanismo heredado de enrutamiento y selección de plugins del servicio `orchestrator` (el cual utiliza palabras clave y expresiones regulares en `Router`) por un motor de matching semántico basado en similitud textual determinista. Este cambio mejora la tolerancia del asistente frente a variaciones de redacción y errores de transcripción del subsistema de STT (Speech-to-Text).

### Actores y Reglas de Negocio
1. **Desarrollador de Plugins**: Declara frases representativas de uso de la capacidad en la propiedad `examples`. El desarrollador ya no necesita preocuparse por definir expresiones regulares complejas ni listas exhaustivas de palabras clave.
2. **Orchestrator**: Calcula el score de similitud del texto de entrada frente a todas las frases de ejemplo de los plugins activos (excluyendo el plugin de Fallback) utilizando la librería `rapidfuzz`.
3. **Resolución por similitud y prioridad**:
   - Cada plugin obtiene una puntuación final correspondiente al score máximo de sus frases de ejemplo comparadas con la del usuario.
   - Se requiere superar un umbral de similitud configurable (`similarity_threshold`).
   - Los empates o puntuaciones demasiado cercanas se resuelven utilizando la propiedad `priority` de cada plugin si la diferencia de puntuación es inferior a un umbral de desempate configurable (`tie_breaker_threshold`).
   - Si tras aplicar la prioridad persiste la ambigüedad, o si ningún plugin supera el umbral de similitud, se deriva la petición al `FallbackPlugin`.

---

## 2. Análisis de Servicios e Impacto

| Servicio | Tipo de Cambio | Descripción del Impacto |
| :--- | :--- | :--- |
| `orchestrator` | Modificar | - `requirements.txt`: Incorporar la dependencia de `rapidfuzz`.<br> - `core/config.py`: Definir nuevas propiedades de configuración para umbrales (`similarity_threshold`, `tie_breaker_threshold`) y pesos de los algoritmos de similitud (`weight_ratio`, `weight_partial_ratio`, `weight_token_sort_ratio`, `weight_token_set_ratio`).<br> - `core/engine.py`: Reemplazar la lógica de selección de `Router` por la invocación del nuevo `PluginMatcher`. Mantener la clase `Router` heredando de `PluginMatcher` para conservar la retrocompatibilidad estructural.<br> - `tests/test_engine.py`: Adaptar la suite de pruebas unitarias al nuevo motor basado en similitud, cubriendo el desempate por prioridad, empates persistentes, normalización y validación de pesos.<br> - `README.md`: Reemplazar las referencias al motor basado en palabras clave (keywords) y expresiones regulares por el nuevo motor de similitud y el desempate por prioridad. |
| `home-assistant` | Modificar | - `config/orchestrator.env`: Declarar y documentar las nuevas variables de entorno de similitud con sus valores por defecto para que estén disponibles en el despliegue del ecosistema Docker.<br> - `docs/services.md`: Modificar la sección del `orchestrator` para actualizar la descripción del mecanismo de selección (reemplazando keywords/regex por similitud y prioridad).<br> - `docs/architecture.md`: Actualizar la descripción del servicio `orchestrator` **y la tabla de decisiones de diseño clave (ADRs)** para reemplazar la entrada de `ADR-003` por la referencia al nuevo `ADR-004` local de `orchestrator` con la descripción del motor de similitud determinista. Esta tarea es obligatoria antes del merge para evitar que la tabla global de ADRs quede apuntando a una decisión obsoleta.<br> - `.agent/skills/domains/plugin-domain/SKILL.md`: Actualizar la sección de Responsabilidades, Invariantes y Referencias para alinearlas con la sustitución de keywords/regex por similitud de texto y prioridad, referenciando el nuevo ADR local en lugar del global `ADR-003`. **⚠️ Esta actualización es crítica y debe realizarse como parte de la Fase 6 antes del cierre del PR**, ya que la skill contiene un invariante (🔴 hard constraint) que actualmente entra en conflicto directo con la nueva arquitectura: *"Las derivaciones de voz se resuelven exclusivamente mediante scoring matemático determinista sobre keywords/regex."* Mientras no se actualice, la skill refleja un estado inconsistente con el código en producción. |
| Todos los demás servicios | Ninguno | Las interfaces REST externas (`POST /api/v1/execute`) del `orchestrator` y las respuestas devueltas no varían, por lo que no hay impacto en otros servicios. |

### Evaluación de necesidad de ADR (Architectural Decision Record)
Conforme a la skill `architecture-decisions`, el cambio propuesto constituye una reestructuración interna del motor de selección de intenciones del servicio `orchestrator` y reemplaza la estrategia determinista anterior definida en el documento global `ADR-003: Scoring Determinista de Plugins de Intenciones`. 
Se propone:
1. Crear un ADR local en el repositorio de orchestrator: `doc/adr/adr-004-motor-seleccion-plugins-similitud.md`.
2. Actualizar el estado del global `ADR-003` en `home-assistant/docs/adr/adr-003.md` a "Superado" (Superseded) haciendo referencia al nuevo ADR local de similitud determinista local.

---

## 3. Especificación de Comportamiento (Criterios de Aceptación)

### Escenario 1: Selección exitosa por similitud de texto
```gherkin
Dado que el PluginMatcher está inicializado con un similarity_threshold de 60.0
Y el plugin con ID "greeting" tiene la frase de ejemplo "¿Cómo te va?"
Cuando el usuario envía una petición con el texto "Hola Nova qué tal te va hoy"
Entonces el PluginMatcher calcula la similitud con las frases de ejemplo
Y selecciona el plugin "greeting" por superar el umbral de 60.0
```

### Escenario 2: Derivación a Fallback por baja similitud (NoMatch)
```gherkin
Dado que el PluginMatcher está inicializado con un similarity_threshold de 60.0
Cuando el usuario envía una petición no relacionada como "dibuja un dinosaurio azul"
Entonces todas las puntuaciones calculadas son inferiores a 60.0
Y el PluginMatcher devuelve NoMatch
Y el Orchestrator ejecuta FallbackPlugin
```

### Escenario 3: Resolución de ambigüedad mediante prioridad (Desempate)
```gherkin
Dado que el PluginMatcher tiene un similarity_threshold de 60.0 y un tie_breaker_threshold de 5.0
Y el plugin A ("weather") tiene prioridad 80 y obtiene un score de 72.0
Y el plugin B ("identity") tiene prioridad 60 y obtiene un score de 70.0
Cuando se evalúa la petición del usuario
Entonces la diferencia de scores (2.0) es menor que el tie_breaker_threshold (5.0)
Y el PluginMatcher selecciona el plugin A por tener mayor prioridad (80 > 60)
```

### Escenario 4: Empate persistente por igual prioridad
```gherkin
Dado que el PluginMatcher tiene un similarity_threshold de 60.0 y un tie_breaker_threshold de 5.0
Y el plugin A tiene prioridad 80 y obtiene un score de 71.0
Y el plugin B tiene prioridad 80 y obtiene un score de 70.0
Cuando se evalúa la petición
Entonces la diferencia de scores (1.0) es menor que el tie_breaker_threshold (5.0)
Y ambos plugins tienen la misma prioridad (80)
Entonces el PluginMatcher devuelve NoMatch
Y el Orchestrator ejecuta FallbackPlugin
```

### Escenario 5: Registro de diagnóstico en logs
```gherkin
Dado que el PluginMatcher está inicializado con un logger mockeado
Y existe al menos un plugin activo con frases de ejemplo
Cuando el usuario envía una petición con el texto "pon música"
Y se completa la selección del plugin
Entonces el logger recibe al menos una llamada a nivel DEBUG con el texto normalizado del usuario
Y el logger recibe al menos una llamada a nivel DEBUG que incluye el nombre y score del plugin candidato
Y el logger recibe al menos una llamada a nivel INFO que identifica el plugin finalmente seleccionado o el FallbackPlugin en caso de NoMatch
```

---

## 4. Diseño Técnico y Contratos

### Configuración (`core/config.py`)
Añadir a la clase `Settings` las variables del motor de similitud y un validador de Pydantic para asegurar la consistencia de los pesos.

```python
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # ... configuraciones existentes ...
    
    # Parámetros del motor de similitud
    similarity_threshold: float = 60.0
    tie_breaker_threshold: float = 5.0
    
    # Pesos de los algoritmos de RapidFuzz
    weight_ratio: float = 0.20
    weight_partial_ratio: float = 0.30
    weight_token_sort_ratio: float = 0.20
    weight_token_set_ratio: float = 0.30

    @model_validator(mode="after")
    def validate_weights(self) -> 'Settings':
        total = (
            self.weight_ratio + 
            self.weight_partial_ratio + 
            self.weight_token_sort_ratio + 
            self.weight_token_set_ratio
        )
        if not abs(total - 1.0) < 1e-6:
            raise ValueError(f"The sum of similarity weights must be exactly 1.0, got {total}")
        return self

    model_config = SettingsConfigDict(env_file=".env")
```

### Contrato de Similarity Engine (`core/similarity.py`)
```python
from abc import ABC, abstractmethod

class SimilarityEngine(ABC):
    @abstractmethod
    def score(self, user_text: str, example_phrase: str) -> float:
        """
        Calculates the similarity score between the user text and an example phrase.
        Returns a value between 0.0 and 100.0.
        """
        pass
```

### Implementación del Similarity Engine con RapidFuzz (`core/similarity.py`)
```python
from rapidfuzz import fuzz
from .config import settings

class RapidFuzzSimilarityEngine(SimilarityEngine):
    def __init__(
        self, 
        weight_ratio: float = settings.weight_ratio,
        weight_partial_ratio: float = settings.weight_partial_ratio,
        weight_token_sort_ratio: float = settings.weight_token_sort_ratio,
        weight_token_set_ratio: float = settings.weight_token_set_ratio
    ):
        self.weight_ratio = weight_ratio
        self.weight_partial_ratio = weight_partial_ratio
        self.weight_token_sort_ratio = weight_token_sort_ratio
        self.weight_token_set_ratio = weight_token_set_ratio

    def score(self, user_text: str, example_phrase: str) -> float:
        # RapidFuzz returns scores between 0.0 and 100.0
        score_ratio = fuzz.ratio(user_text, example_phrase)
        score_partial = fuzz.partial_ratio(user_text, example_phrase)
        score_sort = fuzz.token_sort_ratio(user_text, example_phrase)
        score_set = fuzz.token_set_ratio(user_text, example_phrase)
        
        combined_score = (
            self.weight_ratio * score_ratio +
            self.weight_partial_ratio * score_partial +
            self.weight_token_sort_ratio * score_sort +
            self.weight_token_set_ratio * score_set
        )
        return combined_score
```

### Motor de Selección de Plugins (`core/engine.py`)
El `PluginMatcher` reemplaza la lógica heredada del `Router`. Se mantiene la clase `Router` heredando de `PluginMatcher` para no romper la compatibilidad con el servidor API FastAPI y lifespan.

```python
import re
import unicodedata
from typing import Tuple, List, Optional
from plugins.base import Plugin
from .models import UserRequest, PluginContext
from .plugin_manager import PluginManager
from .similarity import SimilarityEngine
from .logger import logger
from .config import settings

class PluginMatcher:
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
        text = text.lower()
        text = ''.join(c for c in unicodedata.normalize('NFD', text) if unicodedata.category(c) != 'Mn')
        text = re.sub(r'[^\w\s]', ' ', text)
        return ' '.join(text.split())

    async def route_request(self, request: UserRequest) -> Tuple[Plugin | None, PluginContext]:
        normalized_text = self.normalize_text(request.text)
        context = PluginContext(raw_text=request.text, normalized_text=normalized_text)
        
        # Guard short-circuit if user text is empty
        if not normalized_text:
            logger.info("Empty user query. Defaulting to FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context
            
        plugins = self.plugin_manager.get_active_plugins()
        candidate_scores = []

        for plugin in plugins:
            if plugin.id == "fallback":
                continue
                
            best_phrase_score = 0.0
            best_phrase = ""
            
            for example in plugin.examples:
                normalized_example = self.normalize_text(example)
                phrase_score = self.similarity_engine.score(normalized_text, normalized_example)
                if phrase_score > best_phrase_score:
                    best_phrase_score = phrase_score
                    best_phrase = example
            
            candidate_scores.append({
                "plugin": plugin,
                "score": best_phrase_score,
                "priority": plugin.priority,
                "best_phrase": best_phrase
            })

        # Sort candidate plugins by score desc
        candidate_scores.sort(key=lambda x: x["score"], reverse=True)

        # Diagnose logging
        logger.debug(f"Input request: '{request.text}' | Normalized: '{normalized_text}'")
        logger.debug("Plugin candidates ranking:")
        for idx, entry in enumerate(candidate_scores):
            p = entry["plugin"]
            logger.debug(f"  [{idx + 1}] Plugin: {p.name} (id: {p.id}) | Score: {entry['score']:.2f} | Priority: {entry['priority']} | Winning Phrase: '{entry['best_phrase']}'")

        if not candidate_scores:
            logger.info("No active plugins found. Using FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context

        first = candidate_scores[0]
        
        # Check minimum similarity threshold
        if first["score"] < self.similarity_threshold:
            logger.info(f"Top candidate {first['plugin'].name} score {first['score']:.2f} below threshold {self.similarity_threshold}. Using FallbackPlugin.")
            fallback = self.plugin_manager.get_plugin("FallbackPlugin")
            return fallback, context

        # Check for ties/ambiguities with the runner-up
        if len(candidate_scores) > 1:
            second = candidate_scores[1]
            score_difference = first["score"] - second["score"]
            
            if score_difference < self.tie_breaker_threshold:
                logger.info(
                    f"Ambiguity detected between {first['plugin'].name} (score: {first['score']:.2f}) "
                    f"and {second['plugin'].name} (score: {second['score']:.2f}). Difference: {score_difference:.2f} < tie_breaker_threshold: {self.tie_breaker_threshold}"
                )
                
                if first["priority"] > second["priority"]:
                    logger.info(f"Resolved tie in favor of {first['plugin'].name} by higher priority ({first['priority']} > {second['priority']})")
                    return first["plugin"], context
                elif second["priority"] > first["priority"]:
                    logger.info(f"Resolved tie in favor of {second['plugin'].name} by higher priority ({second['priority']} > {first['priority']})")
                    return second["plugin"], context
                else:
                    logger.warning(
                        f"Persistent tie between {first['plugin'].name} and {second['plugin'].name}. Both have priority {first['priority']}. Defaulting to FallbackPlugin."
                    )
                    fallback = self.plugin_manager.get_plugin("FallbackPlugin")
                    return fallback, context

        logger.info(f"Selected plugin: {first['plugin'].name} with score: {first['score']:.2f} and winning phrase: '{first['best_phrase']}'")
        return first["plugin"], context

class Router(PluginMatcher):
    # Kept for backward compatibility with external code using Router class name.
    pass
```

---

## 5. Casos de Borde y Manejo de Errores

| Caso de Borde | Comportamiento Esperado | Implementación Técnica |
| :--- | :--- | :--- |
| **Lista de `examples` vacía en un plugin** | El plugin no debe poder ser seleccionado si carece de ejemplos para emparejar. | **Nota:** La validación de que `examples` no esté vacío es responsabilidad del `PluginManager` en el momento de carga del plugin (prerrequisito implementado en la feature anterior *Plugins Examples and Priority*). El score `0.0` en el `PluginMatcher` actúa únicamente como segunda línea de defensa para mayor robustez, pero no es el mecanismo principal de control. El score por defecto del plugin se evalúa en `0.0`. Al ordenar, quedará al final del ranking y no superará el umbral mínimo. |
| **Pesos de RapidFuzz no suman 1.0** | El inicio de la aplicación debe fallar inmediatamente para evitar cálculos de score inconsistentes. | Añadir la validación `@model_validator(mode="after")` en `Settings` de Pydantic. Si falla la validación, la carga de `settings` levantará una excepción en la inicialización (lifespan). |
| **Falta de biblioteca `rapidfuzz`** | El arranque del servicio `orchestrator` debe fallar inmediatamente con un error claro. | El import de `fuzz` desde `rapidfuzz` en `core/similarity.py` fallará arrojando un `ImportError` nativo de Python en la fase de carga del lifespan del servicio. |
| **Texto de usuario vacío** | No se debe perder tiempo en calcular similitudes con textos vacíos o con solo espacios. | Añadir un guard en `route_request` que valide `if not normalized_text`. Si se cumple, devuelve directamente el `FallbackPlugin` sin iterar sobre los plugins. |

---

## 6. Estrategia de Testing

### Pruebas Unitarias
1. **Validación del motor de similitud (`tests/test_similarity.py`)**:
   - `test_rapid_fuzz_similarity_engine_calculation`: Verificar que se aplique la fórmula ponderada correctamente.
   - `test_settings_weights_validation`: Validar que lanzar pesos que no sumen 1.0 arroje un error de validación de Pydantic.
2. **Validación del Plugin Matcher (`tests/test_engine.py` / `tests/test_matcher.py`)**:
   - `test_route_request_successful_match`: Simular peticiones que coincidan estrechamente con frases de ejemplo y verificar que se enruten al plugin correcto.
   - `test_route_request_below_threshold_fallback`: Probar frases de usuario completamente inconexas y confirmar que se seleccione el Fallback.
   - `test_route_request_tie_breaker_by_priority`: Configurar dos plugins con scores muy cercanos y prioridades distintas; comprobar que se elija el de mayor prioridad.
   - `test_route_request_persistent_tie_fallback`: Configurar dos plugins con scores muy cercanos e idéntica prioridad; comprobar que se devuelva el Fallback.
   - `test_route_request_empty_input_fallback`: Validar que la cadena de texto vacía derive en Fallback sin levantar excepciones.
   - `test_route_request_normalization_coherence`: Validar que la normalización se aplique tanto al texto de usuario como al texto de ejemplo.
   - `test_route_request_diagnostic_logging`: Verificar, mediante mocking del logger, que `route_request` emite al menos una llamada `debug` con el texto normalizado del usuario, al menos una llamada `debug` con el nombre y score de un plugin candidato, y al menos una llamada `info` que identifica el plugin seleccionado o el `FallbackPlugin`. Cubre el Escenario 5 de los criterios de aceptación.

---

## 7. Plan de Implementación (Checklist)

- [ ] **Fase 1: Configuración de Dependencias y Modelos**
  - [ ] Añadir la dependencia `rapidfuzz>=3.3.0` al archivo [requirements.txt](file:///home/danuser2018/workspace/orchestrator/requirements.txt).
  - [ ] Crear el Architectural Decision Record local [adr-004-motor-seleccion-plugins-similitud.md](file:///home/danuser2018/workspace/orchestrator/doc/adr/adr-004-motor-seleccion-plugins-similitud.md) describiendo el nuevo diseño del motor y la sustitución de keywords/regex.
  - [ ] Modificar [core/config.py](file:///home/danuser2018/workspace/orchestrator/core/config.py) para añadir los parámetros `similarity_threshold`, `tie_breaker_threshold` y los 4 pesos de `rapidfuzz`, implementando la validación de suma igual a 1.0.
  - [ ] Modificar el archivo [config/orchestrator.env](file:///home/danuser2018/workspace/home-assistant/config/orchestrator.env) en `home-assistant` para incorporar las nuevas variables de entorno y documentar sus valores recomendados por defecto.
- [ ] **Fase 2: Desarrollo del Motor de Similitud**
  - [ ] Crear el archivo `core/similarity.py` e implementar las clases `SimilarityEngine` y `RapidFuzzSimilarityEngine`.
- [ ] **Fase 3: Desarrollo del PluginMatcher y Refactorización del Router**
  - [ ] Implementar la clase `PluginMatcher` en [core/engine.py](file:///home/danuser2018/workspace/orchestrator/core/engine.py), definiendo el algoritmo completo (normalización, cálculo del mejor score por plugin, ranking, validación de umbral, desempate por prioridad y fallback en caso de empate persistente o NoMatch).
  - [ ] Declarar en [core/engine.py](file:///home/danuser2018/workspace/orchestrator/core/engine.py) la clase `Router` heredando de `PluginMatcher` para retrocompatibilidad.
- [ ] **Fase 4: Adaptación del Arranque de la Aplicación**
  - [ ] Modificar [main.py](file:///home/danuser2018/workspace/orchestrator/main.py) en el método `lifespan` para inicializar el `RapidFuzzSimilarityEngine` y pasar la instancia a `Router` (la cual hereda de `PluginMatcher`).
- [ ] **Fase 5: Pruebas Unitarias**
  - [ ] Actualizar y crear los casos de test unitarios en [tests/test_engine.py](file:///home/danuser2018/workspace/orchestrator/tests/test_engine.py) para cubrir todos los escenarios de similitud, desempate y normalización.
  - [ ] Ejecutar la suite de pruebas local (`PYTHONPATH=. pytest`) verificando el correcto funcionamiento del motor de enrutamiento.
- [ ] **Fase 6: Registro de Cambios e Integración**
  - [ ] Actualizar el archivo `CHANGELOG.md` del `orchestrator` bajo la sección `[Sin publicar]` detallando la adopción de `rapidfuzz` y la eliminación del enrutamiento basado en keywords/regex.
  - [ ] Actualizar el estado de `ADR-003` en [home-assistant/docs/adr/adr-003.md](file:///home/danuser2018/workspace/home-assistant/docs/adr/adr-003.md) a `Superado` por la nueva arquitectura basada en similitud determinista.
  - [ ] Actualizar [README.md](file:///home/danuser2018/workspace/orchestrator/README.md) en `orchestrator` para reemplazar las descripciones y el ejemplo del motor de keywords/regex por el nuevo motor de similitud y prioridad.
  - [ ] Actualizar [docs/services.md](file:///home/danuser2018/workspace/home-assistant/docs/services.md) en `home-assistant` para adecuar la descripción del `orchestrator` y de la selección de plugins.
  - [ ] Actualizar [docs/architecture.md](file:///home/danuser2018/workspace/home-assistant/docs/architecture.md) en `home-assistant` para: (1) reflejar el uso de similitud determinista en la descripción del servicio `orchestrator`; (2) **reemplazar la entrada de `ADR-003` en la tabla de decisiones de diseño clave** añadiendo la referencia al nuevo `ADR-004` local de `orchestrator` con la descripción del motor de similitud determinista, para que el índice global de ADRs no quede apuntando a una decisión obsoleta tras el merge.
  - [ ] ⚠️ **[CRÍTICO — obligatorio antes del cierre del PR]** Actualizar la skill [plugin-domain/SKILL.md](file:///home/danuser2018/workspace/home-assistant/.agent/skills/domains/plugin-domain/SKILL.md) en `home-assistant` sustituyendo las responsabilidades, invariantes y referencias del motor anterior por las del nuevo motor de similitud y prioridad, y su correspondiente ADR. Esta tarea es crítica porque la skill contiene un invariante (🔴 hard constraint) que entra en conflicto directo con el código en producción hasta que sea actualizado.
