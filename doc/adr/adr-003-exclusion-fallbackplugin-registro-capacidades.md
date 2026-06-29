# ADR 0003: Exclusión de FallbackPlugin del registro automático de capacidades

* **Fecha**: 2026-06-29
* **Estado**: Aceptado

## Contexto

El servicio Orchestrator publica dinámicamente en el arranque sus capacidades cargadas al `system-service` mediante el endpoint `POST /v1/system/capabilities`. Estas capacidades registradas son consumidas por otros componentes del sistema (como `CapabilitiesPlugin` o `interaction-manager`) para informar al usuario de qué funciones puede realizar Nova-2.

Por diseño, el `FallbackPlugin` actúa como un mecanismo de último recurso (fallback) cuando ninguna intención o palabra clave de los plugins funcionales logra superar el umbral de scoring. Sin embargo, no representa una funcionalidad o comando específico que el usuario pueda solicitar de forma activa o consciente. 

Registrar el `FallbackPlugin` como una capacidad pública introduce ruido en la lista de intenciones disponibles y resulta confuso tanto para el usuario final como para la lógica de otros servicios que listan las capacidades.

## Decisión

Se decide excluir explícitamente a `FallbackPlugin` del listado de capacidades que el servicio Orchestrator envía al `system-service` durante el arranque (`main.py`):

1. Durante la construcción del payload de capacidades a enviar en el arranque, se filtra cualquier plugin cuyo identificador o clase corresponda a `FallbackPlugin`.
2. El plugin seguirá cargándose y ejecutándose normalmente a nivel local en el motor de routing para interceptar mensajes no reconocidos, pero no será visible externamente en la lista de capacidades del sistema.

## Consecuencias

* **Positivas**:
  * Lista de capacidades limpia y centrada únicamente en intenciones que el usuario puede invocar de forma real.
  * Mayor claridad en la salida del `CapabilitiesPlugin`.
* **Negativas**:
  * Requiere lógica ad-hoc de filtrado en el arranque de la aplicación (en `main.py`).
