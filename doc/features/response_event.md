# Especificación Funcional - Integración del primer evento del dominio (Fase 3)

## Objetivo

Integrar el primer evento del dominio de Nova dentro del `orchestrator`.

Cada vez que el Orchestrator genere una respuesta válida mediante la ejecución de un plugin, deberá publicar un evento denominado `ResponseGeneratedEvent` en el Event Bus antes de devolver la respuesta al llamante.

Esta fase constituye la primera utilización real de `nova-event-bus` dentro del ecosistema.

---

# Motivación

Con la incorporación del Event Bus, Nova introduce un nuevo mecanismo de comunicación basado en eventos.

El objetivo de esta fase es comenzar a desacoplar los servicios permitiendo que otros componentes puedan reaccionar a la generación de una respuesta sin necesidad de modificar el Orchestrator.

Inicialmente no existirá ningún consumidor.

El objetivo es únicamente publicar el evento.

---

# Alcance

Esta fase incluye:

- integración de `nova-event-bus` en Orchestrator;
- conexión al broker durante el arranque del servicio;
- desconexión ordenada durante el apagado;
- publicación del primer evento del dominio;
- definición del evento `ResponseGeneratedEvent`.

No incluye:

- consumidores del evento;
- métricas;
- contexto;
- almacenamiento;
- workflows;
- modificaciones en otros servicios.

---

# Requisitos funcionales

## RF-1. Dependencia

El proyecto `orchestrator` incorporará la dependencia:

```python
from nova_event_bus import EventBus
```

El resto de la implementación permanecerá desacoplada de NATS.

No estará permitido importar directamente la librería oficial del broker.

---

## RF-2. Inicialización

Durante el arranque del servicio deberá crearse una instancia del EventBus.

Ejemplo:

```python
from nova_event_bus import EventBus

event_bus = EventBus()
```

---

## RF-3. Conexión

Durante el startup del servicio deberá establecerse la conexión con el broker.

```python
await event_bus.connect()
```

---

## RF-4. Desconexión

Durante el apagado del servicio deberá cerrarse correctamente la conexión.

```python
await event_bus.disconnect()
```

---

## RF-5. Publicación del evento

Una vez finalizada correctamente la ejecución del plugin y antes de devolver la respuesta al llamante, el Orchestrator publicará un evento.

Secuencia:

```
Resolver intención

↓

Ejecutar plugin

↓

Construir respuesta

↓

Publicar ResponseGeneratedEvent

↓

Responder al cliente
```

---

## RF-6. Evento

El evento publicado será:

```
ResponseGeneratedEvent
```

Representa el hecho:

> Nova ha generado una respuesta.

No representa la ejecución interna de un plugin.

---

## RF-7. Información publicada

El evento contendrá como mínimo los siguientes campos:

| Campo | Descripción |
|--------|-------------|
| response | Texto generado por Nova |
| plugin | Plugin responsable de la respuesta |
| confidence | Confianza obtenida durante la resolución |
| timestamp | Fecha y hora del evento |
| correlation_id | Identificador de la interacción |
| execution_time_ms | Tiempo empleado por el plugin |
| channel | Canal de entrada (voice, api, etc.) |
| metadata | Información adicional |

---

## RF-8. Ejemplo de publicación

Ejemplo de uso de la librería:

```python
await event_bus.publish(
    ResponseGeneratedEvent(
        response=response.text,
        plugin=plugin.name,
        confidence=plugin.confidence,
        timestamp=datetime.now(),
        correlation_id=correlation_id,
        execution_time_ms=execution_time,
        channel="voice",
        metadata={}
    )
)
```

---

# Requisitos no funcionales

## RNF-1

La publicación del evento no modificará el comportamiento observable del Orchestrator.

La respuesta enviada al cliente será exactamente la misma que antes de introducir el Event Bus.

---

## RNF-2

El Orchestrator permanecerá completamente desacoplado de cualquier consumidor.

No conocerá:

- quién consume el evento;
- cuántos consumidores existen;
- si existe algún consumidor.

---

## RNF-3

La publicación del evento se realizará exclusivamente mediante `nova-event-bus`.

El código del Orchestrator no contendrá referencias a NATS.

---

## RNF-4

El evento representará un hecho del dominio y no un detalle interno de implementación.

Por este motivo se utilizará:

```
ResponseGeneratedEvent
```

en lugar de eventos como:

```
PluginExecutedEvent
```

---

# Cambios esperados

Se modificará únicamente el Orchestrator.

Los cambios se limitarán a:

- inicialización del EventBus;
- conexión durante el startup;
- desconexión durante el shutdown;
- publicación de `ResponseGeneratedEvent`.

No se modificará ningún otro servicio del ecosistema.

---

# Criterios de aceptación

La fase se considerará completada cuando:

- el Orchestrator arranque correctamente con `nova-event-bus`;
- la conexión al broker se establezca durante el startup;
- la desconexión se realice correctamente durante el shutdown;
- cada respuesta generada produzca exactamente un `ResponseGeneratedEvent`;
- el evento se publique antes de devolver la respuesta al llamante;
- no exista ninguna regresión funcional en el comportamiento del Orchestrator.

---

# Fuera de alcance

Quedan expresamente fuera de esta fase:

- creación de consumidores;
- métricas;
- auditoría;
- contexto conversacional;
- almacenamiento de eventos;
- reintentos;
- persistencia;
- workflows;
- publicación de otros tipos de eventos.