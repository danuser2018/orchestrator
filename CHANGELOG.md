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

---

## Sin publicar

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

[Sin publicar]: https://github.com/danuser2018/tts-capability/compare/HEAD...HEAD
