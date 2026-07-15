# Registro de cambios

Todos los cambios notables de este proyecto se documentan en este fichero.

El formato está basado en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
y este proyecto adhiere a [Versionado Semántico](https://semver.org/lang/es/).

## Guía de uso

Cada versión se documenta bajo su número de versión y fecha de publicación.
Los cambios se agrupan en las siguientes categorías:

- **Añadido** — nuevas funcionalidades.
- **Cambiado** — cambios en funcionalidades existentes.
- **Obsoleto** — funcionalidades que serán eliminadas en versiones futuras.
- **Eliminado** — funcionalidades eliminadas en esta versión.
- **Corregido** — corrección de errores.
- **Seguridad** — correcciones de vulnerabilidades.

## [2.6.0] - 2026-07-15

### Añadido
- Nuevos endpoints `POST /api/v1/resolve` para resolver intenciones a un plan estructurado, y `POST /api/v1/execute-plan` para ejecutar planes secuenciales.
- Manejadores de excepciones globales para formatear los errores de validación (`ValidationError` en 422) y plugins no encontrados (`PluginNotFoundError` en 400) siguiendo la especificación global ADR-004.
- Nuevos modelos Pydantic `ExecutionPlanStep` y `ExecutionPlan`.
- Suite de pruebas unitarias específicas para resolver y ejecutar planes (`tests/test_resolver.py`, `tests/test_executor.py`) y pruebas de integración para los nuevos endpoints (`tests/test_api.py`).

### Cambiado
- Refactorizado el motor interno dividiendo el antiguo `PluginMatcher` en `IntentResolver` y `PluginExecutor`.
- Modificado el endpoint `POST /api/v1/execute` para que actúe como puente secuencial interno de `resolve` y `execute_plan` preservando la compatibilidad total.
- La clase `Router` ahora hereda de `IntentResolver` e implementa el método obsoleto `route_request` para compatibilidad de tests heredados.

## [2.5.0] - 2026-07-15

### Añadido
- Cinco nuevos plugins públicos de control de volumen: `VolumeUpPlugin` (`volume-up`), `VolumeDownPlugin` (`volume-down`), `VolumeStatusPlugin` (`volume-status`), `MutePlugin` (`mute`) y `UnmutePlugin` (`unmute`), con prioridad 60 y haciendo uso de la API REST del microservicio `host-service`.
- Nuevo cliente de servicio host asíncrono (`core/host_service_client.py`) para interactuar con la Capa de Abstracción de Host (HAL) y recuperar/modificar el estado de audio.
- Variable de configuración `host_service_base_url` agregada a la clase `Settings` en `core/config.py`.
- Suite de pruebas unitarias para `HostServiceClient` y los nuevos plugins en `tests/test_volume_plugin.py`.
- Integración de los nuevos plugins en las pruebas de enrutamiento (`tests/test_routing.py`) y de registro de capacidades (`tests/test_plugin_registration.py`).

## [2.4.0] - 2026-07-14

### Añadido
- Tres nuevos plugins públicos de generación aleatoria: `CoinPlugin` (`coin`), `DicePlugin` (`dice`) y `RandomNumberPlugin` (`random-number`), con prioridad 60 y haciendo uso de la utilidad centralizada `RandomService`.
- Nueva clase de utilidad centralizada `RandomService` (`core/random_service.py`) para encapsular la generación pseudoaleatoria de Python.
- Suite de pruebas unitarias para `RandomService` y los nuevos plugins en `tests/test_random_plugin.py`.
- Integración de los nuevos plugins en las pruebas de enrutamiento (`tests/test_routing.py`) y de registro de capacidades (`tests/test_plugin_registration.py`).
- Actualización de `README.md` para incluir los tres nuevos plugins en la tabla de prioridades y en el árbol de estructura de directorios.

## [2.3.0] - 2026-07-13

### Añadido
- Dos nuevos plugins públicos de información del sistema en el orquestador: `TimePlugin` (`time`) para la hora actual en formato de 24 horas y `DatePlugin` (`date`) para la fecha actual en formato extendido, con prioridad 80 y usando la utilidad centralizada `DateTimeService`.
- Pruebas unitarias completas para `DateTimeService` y los nuevos plugins `TimePlugin` y `DatePlugin` en `tests/test_datetime_plugin.py`, además de integrar su enrutamiento y registro en `tests/test_routing.py` y `tests/test_plugin_registration.py`.

---

## [2.2.0] - 2026-07-13

### Añadido
- Tres nuevos plugins públicos de identidad: `AuthorPlugin` (`author`), `VersionPlugin` (`version`) y `HelpPlugin` (`help`), integrados con el motor de similitud RapidFuzz y con gestión homogénea de errores según `ADR-002`.
- Suite de pruebas unitarias en `tests/test_identity_plugin.py` cubriendo casos de éxito, errores de red/HTTP y excepciones inesperadas.
- Pruebas de registro de capacidades en `tests/test_plugin_registration.py` para asegurar que los nuevos plugins publican sus capacidades en `system-service` durante el arranque.
- Pruebas de enrutamiento en `tests/test_routing.py` para validar la correcta selección de los plugins por similitud semántica.

---

## [2.1.0] - 2026-07-05

### Añadido
- Cliente de servicio meteorológico asíncrono (`core/weather_service_client.py`) para consumir datos meteorológicos reales en lugar de simulados.
- Suite de pruebas unitarias (`tests/test_weather_plugin.py`) para validar el comportamiento del plugin meteorológico con mocks de red.

### Cambiado
- Modificado `plugins/weather/main.py` para consumir `weather-service` y formatear el resultado de acuerdo con las especificaciones de negocio (redondeo de temperatura, mapeo de lluvia) y las pautas de tono de `TONE_GUIDE.md` y gestión de errores de `ADR-002`.
- Agregada la variable de configuración `weather_service_base_url` a la clase `Settings` en `core/config.py`.
- Actualizado `README.md` con el código real de producción de `WeatherPlugin`.
- Actualizados los tests de API en `tests/test_api.py` para mockear `WeatherServiceClient` y evitar llamadas a red.

---

## [2.0.0] - 2026-07-03

### Eliminado
- Eliminación total de las propiedades obsoletas `keywords`, `regex_patterns` y `exclusive_regex` en la interfaz base de plugins `Plugin` y en todos los plugins del sistema (`GreetingPlugin`, `FarewellPlugin`, `WeatherPlugin`, `CapabilitiesPlugin`, `IdentityPlugin`, `FallbackPlugin`), consolidando definitivamente el enrutamiento por similitud semántica y prioridad.
- Eliminación de la importación y emisión de advertencias de tipo `DeprecationWarning` asociadas a estas propiedades obsoletas.

### ⚠️ Cambios disruptivos (Breaking Changes)
- **Incompatibilidad con plugins externos que declaren propiedades legadas**: Cualquier plugin de terceros que definiera las propiedades `keywords`, `regex_patterns` o `exclusive_regex` debe migrar a declarar sus intenciones exclusivamente mediante la propiedad `examples`. Las propiedades legadas ya no están definidas en la clase base `Plugin` y no tendrán ningún efecto en el motor de selección `PluginMatcher`.

---

## [1.13.0] - 2026-07-03

### Añadido
- Integración de la librería `rapidfuzz` para comparación semántica de textos.
- Nuevo motor de comparación basado en similitud semántica ponderada (`PluginMatcher`) en `core/engine.py`.
- Nueva clase `RapidFuzzSimilarityEngine` en `core/similarity.py`.
- Parámetros de configuración configurables (`similarity_threshold`, `tie_breaker_threshold` y pesos de RapidFuzz) con validador de consistencia en `core/config.py`.
- Registro de decisión arquitectónica local `adr-004-motor-seleccion-plugins-similitud.md`.
- Suite de pruebas unitarias específicas para similitud y pesos en `tests/test_similarity.py` y refactorización completa de `tests/test_engine.py` para validar la lógica del PluginMatcher.

### Cambiado
- El motor de enrutamiento `Router` ahora hereda de `PluginMatcher` y utiliza la coincidencia semántica en lugar del scoring por palabras clave y expresiones regulares.
- El arranque en `main.py` ahora inicializa `RapidFuzzSimilarityEngine` y lo inyecta en el `Router`.

---

## [1.12.0] - 2026-07-03


### Añadido
- Propiedades declarativas de identificador único (`id`), nivel de prioridad (`priority`) y colección de frases de ejemplo (`examples`) en el contrato de la clase base `Plugin` y todos los plugins del sistema.
- Validaciones en `PluginManager` para garantizar que los identificadores de plugins registrados sean únicos y que el rango de prioridades sea estrictamente de 0 a 100 inclusive.
- Tests unitarios adicionales en la suite para verificar los nuevos atributos de los plugins, validación de prioridades, detección de identificadores duplicados y filtrado de frases de ejemplo vacías o con espacios en blanco.

### Cambiado
- Simplificación del registro de capacidades al arrancar el servicio en `main.py`, eliminando el procesamiento del nombre de clase y consumiendo la propiedad nativa `plugin.id`.

---

## [1.11.0] - 2026-07-02

### Eliminado

- Variable de configuración `user_email` eliminada de `core/config.py`. El destinatario de correo ya no es responsabilidad del orchestrator; pasa a ser resuelto dinámicamente por `mail-watchdog` consultando a `identity-service` (ver ADR-009).
- Campo `to` eliminado del payload JSON generado por `CapabilitiesPlugin` en `plugins/capabilities/main.py`.

### Cambiado

- Actualizados los tests de `tests/test_capabilities_plugin.py` para reflejar la ausencia del campo `to` en el payload y la eliminación de los mocks de `settings.user_email`.

---

## [1.10.0] - 2026-06-29

### Añadido

- Campo `timestamp` (opcional) en el modelo `UserRequest` (`core/models.py`).
- Registro de Decisión Arquitectónica [ADR 0001](file:///home/danuser2018/workspace/orchestrator/doc/adr/0001-adicion-timestamp-userrequest.md) documentando la adición del campo y su retrocompatibilidad.
- Prueba unitaria `test_execute_with_timestamp` en `tests/test_api.py`.
- Propiedad `exclusive_regex` en la interfaz base `Plugin` (`plugins/base.py`).
- Pruebas unitarias para validar la selección por coincidencia exclusiva en `tests/test_engine.py`.
- Registro de Decisión Arquitectónica [ADR 0002](file:///home/danuser2018/workspace/orchestrator/doc/adr/adr-002-alineacion-mensajes-error-plugins.md) para estandarizar los mensajes de error genéricos devueltos por los plugins de la plataforma.
- Registro de Decisión Arquitectónica [ADR 0003](file:///home/danuser2018/workspace/orchestrator/doc/adr/adr-003-exclusion-fallbackplugin-registro-capacidades.md) documentando la exclusión del `FallbackPlugin` del registro de capacidades dinámicas.

### Cambiado

- Motor de enrutamiento (`core/engine.py`) actualizado para interceptar y resolver peticiones mediante expresiones regulares exclusivas antes de iniciar el cálculo de scoring.
- Enriquecido el plugin de saludos (`GreetingPlugin` en `plugins/greeting/main.py`) con respuestas no interactivas respetuosas con el tono de Nova-2 y sin saludos simplistas (`"Hola."`).
- Exclusión automática del plugin de fallback (`FallbackPlugin`) en la publicación de capacidades al arrancar el servicio en `main.py`.
- Actualizadas las aserciones de pruebas unitarias (`tests/test_greeting_plugin.py`, `tests/test_api.py`, `tests/test_plugin_registration.py`) para alinearlas con la exclusión del fallback y las respuestas enriquecidas del plugin de saludos.

### Corregido

- Discrepancia en el modelo `UserRequest` el cual no incluía el campo `timestamp` definido en la sección de modelos de datos del `README.md`.
- Discrepancia técnica en la selección de plugins que omitía la funcionalidad de "Regex Exclusiva" descrita en el `README.md`.
- Discrepancias en `README.md` (árbol de directorios desactualizado, éxito de la respuesta del plugin de fallback en el ejemplo de API REST y expresión regular de ejemplo del clima con tildes incompatible con la normalización).
- Discrepancias en `doc/greetings.md` (presencia de saludos interactivos no permitidos por la guía de tono y mensaje de excepción no alineado con la directriz del nuevo ADR-002).
- Discrepancias en `doc/identity.md` (estructura física recomendada obsoleta y falta de prefijo `/v1/` en los endpoints del system service).
- Discrepancia en `doc/plugin_registration.md` (falta de prefijo `/v1/` en el endpoint de capacidades del system service).

## [1.9.0] - 2026-06-28

### Cambiado

- Actualizado `SystemServiceClient` para consumir los endpoints versionados `/v1/system/info` y `/v1/system/capabilities` de `system-service`.

### Añadido

- Nueva carpeta `.agent/skills` con información relevante para la IA

## [1.8.0] - 2026-06-28

### Añadido

- Documento `capabilities.md` donde se explica el plugin para listar capabilities disponibles.
- Implementación de `CapabilitiesPlugin` en `plugins/capabilities/main.py` para responder preguntas sobre las capacidades de Nova y enviar el detalle por correo electrónico a través de `mail-watchdog`.
- Nuevas propiedades `user_email` y `mail_pending_dir` añadidas a la configuración centralizada en `core/config.py`.
- Nuevo método `get_capabilities` y estructuras de datos asociadas en `SystemServiceClient`.
- Suite de pruebas unitarias en `tests/test_capabilities_plugin.py`.

## [1.7.0] - 2026-06-28

### Añadido

- Documento `plugin_registration.md` para implementar el registro de plugins al arranque del orchestrator.
- Publicación automática de capacidades en el System Service durante el arranque del Orchestrator utilizando el endpoint POST /system/capabilities.
- Nuevo cliente HTTP centralizado SystemServiceClient en core/system_service_client.py.
- Suite de pruebas unitarias y de integración para la inicialización y el flujo de publicación de capacidades en tests/test_plugin_registration.py.

### Cambiado

- Se ha hecho obligatorio el campo `description` en el contrato de los plugins (`Plugin`).
- Añadida la propiedad `description` a los plugins `FallbackPlugin` y `WeatherPlugin`.
- Eliminado cliente local duplicado client.py y config.py de plugins/identity, migrando a la configuración y cliente compartido.
- Actualizado README.md reflejando el nuevo flujo de inicialización e integración con el System Service.

## [1.6.0] - 2026-06-23

### Corregido

- Valor incorrecto de retorno para el plugin de fallback. Cuando responde este plugin, se estaba considerando la respuesta errónea, por lo que saltaba el control de errores.

## [1.5.0] - 2026-06-20

### Añadido

- Implementación del plugin de identidad (`IdentityPlugin`) para responder a consultas sobre quién es el asistente.
- Nuevo documento explicativo del plugin de identity.

### Corregido

- Valor incorrecto en los tests de api para el plugin de saludo.

## [1.4.0] - 2026-06-13

### Añadido

- Nuevo documento TONE_GUIDE.md donde se explica el tono que deben usar los plugins en sus respuestas.
- GreetingPlugin, FarewellPlugin y FallbackPlugin adaptados al tone guide.

## [1.3.0] - 2026-06-07

### Añadido

- Nuevo plugin de despedida (`FarewellPlugin`).

## [1.2.0] - 2026-06-06

### Añadido

- Nuevo endpoint /api/v1/healtcheck que permite comprobar si el servicio está levantado

## [1.1.0] - 2026-06-04

### Añadido

- Archivo doc/plugins/greetings.md donde se describe el plugin de saludo.
- Implementación del plugin de saludo (`GreetingPlugin`).

## [1.0.0] - 2026-06-01

### Añadido

- Configuración de GitHub Actions para ejecución automática de tests en Pull Requests.
- Archivo CONTRIBUTING.md para guiar el desarrollo y las contribuciones al proyecto.
- Archivo CHAGENLOG.md para registrar los cambios de manera consistente.
- Especificación técnica definida en README.md
- Implementación inicial del motor del Orchestrator y API (FastAPI).
- Modelos Pydantic para `UserRequest`, `PluginContext`, `PluginResult`, `AssistantResponse`.
- Motor de enrutamiento basado en puntuación (keywords y regex).
- `PluginManager` para descubrimiento dinámico de plugins.
- Plugins integrados: `FallbackPlugin` y `WeatherPlugin`.
- Suite completa de tests unitarios y de integración con pytest.
- Dockerfile multiplataforma para levantar el servicio.

---

<!-- Plantilla para nuevas versiones:

## [X.Y.Z] - AAAA-MM-DD

### Añadido
-

### Cambiado
-

### Obsoleto
-

### Eliminado
-

### Corregido
-

### Seguridad
-

-->

[Sin publicar]: https://github.com/danuser2018/orchestrator/compare/HEAD...HEAD
