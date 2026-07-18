# ADR 0005: Adición de campos correlation_id y channel en UserRequest y PluginContext

* **Fecha**: 2026-07-18
* **Estado**: Aceptado

## Contexto

Con la integración de la arquitectura basada en eventos a través de `nova-event-bus`, el orquestador debe publicar el evento `ResponseGeneratedEvent` ante cada ejecución exitosa de un plan de plugins.
Para permitir que los servicios consumidores puedan rastrear y correlacionar peticiones de extremo a extremo (end-to-end), se requiere propagar un identificador de correlación (`correlation_id`) y el canal de entrada (`channel`) a través de todo el ciclo de vida de la petición.

Dado que la estructura recibida por la API pública está definida por el modelo `UserRequest`, cualquier cambio en este modelo afecta al contrato público de comunicación del sistema.

## Decisión

1. Añadir el campo opcional `correlation_id: Optional[str] = None` al modelo de datos `UserRequest` y al contexto interno `PluginContext`.
2. Añadir el campo opcional `channel: Optional[str] = "voice"` al modelo de datos `UserRequest` y al contexto interno `PluginContext`.
3. Si el cliente no provee un `correlation_id`, el motor del orquestador generará un UUID aleatorio en tiempo de resolución y lo propagará en el plan.
4. Si el cliente no provee un `channel`, se asumirá `"voice"` por defecto.

Esto garantiza una compatibilidad total hacia atrás con clientes antiguos que realizan peticiones sin estos campos.

## Consecuencias

* **Positivas**:
  - Habilita la trazabilidad distribuida y el rastreo de interacciones a través de múltiples servicios.
  - Ofrece compatibilidad hacia atrás transparente.
  - Permite segmentar eventos de respuesta según el canal de origen (ej. voz, texto).
* **Negativas**:
  - Aumenta levemente el tamaño de los payloads JSON transmitidos y almacenados.
