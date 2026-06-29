# ADR 0002: Alineación de mensajes de error genéricos en plugins

* **Fecha**: 2026-06-29
* **Estado**: Aceptado

## Contexto

Cada plugin de la plataforma Nova-2 maneja excepciones internas de forma independiente. Anteriormente, existían discrepancias entre los mensajes de error devueltos en las especificaciones (como `doc/greetings.md`) y las implementaciones reales de los plugins ante fallos inesperados. 

Para mantener la consistencia del asistente de voz y adherirse a las directrices de `TONE_GUIDE.md`, es imperativo que los mensajes de error genéricos sigan patrones idénticos según la categoría del plugin.

## Decisión

Se adopta una política de alineación estricta para los mensajes de error genéricos devueltos en el campo `speech` del `PluginResult` ante excepciones no capturadas/inesperadas:

1. **Plugins Conversacionales y de Acción** (ej. `GreetingPlugin`, `FarewellPlugin`, `FallbackPlugin`):
   * Mensaje estándar: `"No he podido completar la operación."`
   * Razón: Estos plugins realizan acciones o flujos conversacionales directos y simples.

2. **Plugins de Consulta de Información y Servicios Externos** (ej. `IdentityPlugin`, `CapabilitiesPlugin`, `WeatherPlugin`):
   * Mensaje estándar: `"No he podido obtener la información."` o `"Servicio no disponible."` (si es un fallo de conectividad directa).
   * Razón: Estos plugins actúan mayoritariamente como clientes de API o lectores de estado del sistema.

Cualquier nueva especificación de plugin deberá adherirse a esta nomenclatura.

## Consecuencias

* **Positivas**:
  * Consistencia del comportamiento de voz del asistente ante fallos de ejecución.
  * Mayor facilidad de mantenimiento al definir una plantilla clara para la gestión de errores en nuevos plugins.
* **Neutras**:
  * Requiere actualizar la documentación de especificación técnica de los plugins existentes (`doc/greetings.md`, `doc/identity.md`, etc.) para reflejar esta consistencia.
