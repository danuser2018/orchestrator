# Especificación Funcional - Plugin "Repeat" v1.0.0

## Objetivo

Desarrollar un nuevo plugin denominado **Repeat**, cuya finalidad será permitir al usuario solicitar que Nova repita la última respuesta generada.

El plugin obtendrá la información consultando el `context-service`.

En ningún caso accederá directamente al Event Bus ni conocerá el origen del contexto.

---

# Motivación

El `context-service` mantiene el contexto conversacional de Nova de forma desacoplada mediante eventos.

Este plugin constituye el primer consumidor funcional de dicho contexto y demuestra la separación entre:

- generación del contexto;
- almacenamiento del contexto;
- utilización del contexto.

---

# Alcance

La versión 1.0.0 incluye:

- nuevo plugin `RepeatPlugin`;
- consulta al `context-service`;
- devolución de la última respuesta generada.

No incluye:

- historial de respuestas;
- repetición parcial;
- múltiples conversaciones;
- contexto de usuario.

---

# Funcionamiento

Cuando el usuario solicite repetir la última respuesta, el plugin realizará una petición REST al `context-service`.

Si existe una respuesta almacenada, devolverá exactamente el mismo texto.

Si no existe contexto disponible, devolverá un mensaje informativo.

---

# Requisitos funcionales

## RF-1. Nuevo plugin

Se implementará un nuevo plugin denominado:

```
RepeatPlugin
```

---

## RF-2. Intenciones

El plugin deberá reconocer expresiones equivalentes a:

- Repite.
- Repite, por favor.
- ¿Puedes repetir?
- ¿Qué has dicho?
- Dímelo otra vez.
- No te he oído.
- No lo he entendido.
- ¿Cómo has dicho?

La lista de ejemplos podrá ampliarse en futuras versiones.

---

## RF-3. Consulta del contexto

El plugin consultará el endpoint:

```
GET /context/last-response
```

---

## RF-4. Respuesta satisfactoria

Si el `context-service` devuelve una respuesta válida, el plugin responderá exactamente con el contenido recibido.

No modificará ni reinterpretará el texto.

Ejemplo:

```
Nova:
Hoy es lunes.

Usuario:
Repite.

Nova:
Hoy es lunes.
```

---

## RF-5. Ausencia de contexto

Si el `context-service` responde con:

```
404 Not Found
```

el plugin devolverá:

```
Todavía no tengo ninguna respuesta para repetir.
```

---

## RF-6. Error de comunicación

Si el `context-service` no está disponible o se produce un error durante la consulta, el plugin devolverá un mensaje indicando que no ha sido posible recuperar el contexto.

Mensaje propuesto:

```
Ahora mismo no puedo acceder al contexto de la conversación.
```

---

# Arquitectura

```
Usuario

↓

RepeatPlugin

↓

GET /context/last-response

↓

Context Service

↓

ContextStore
```

El plugin no accederá directamente al Event Bus.

Toda interacción con el contexto se realizará mediante la API REST del `context-service`.

---

# Configuración

La dirección del `context-service` deberá obtenerse mediante variable de entorno.

Variable propuesta:

```
CONTEXT_SERVICE_URL
```

Ejemplo:

```
http://context-service:8000
```

---

# Requisitos no funcionales

## RNF-1

El plugin no mantendrá estado interno.

---

## RNF-2

El plugin no conocerá la implementación interna del `context-service`.

Únicamente consumirá su API pública.

---

## RNF-3

El plugin permanecerá completamente desacoplado del Event Bus.

No utilizará `nova-event-bus`.

---

## RNF-4

El plugin no modificará el contexto.

Únicamente realizará operaciones de lectura.

---

# Flujo de ejecución

```
Usuario

↓

RepeatPlugin

↓

GET /context/last-response

↓

200 OK

↓

Devolver la respuesta
```

o bien

```
Usuario

↓

RepeatPlugin

↓

GET /context/last-response

↓

404

↓

"No tengo ninguna respuesta para repetir."
```

---

# Criterios de aceptación

La implementación se considerará finalizada cuando:

- el plugin sea seleccionado correctamente por el Orchestrator;
- consulte el `context-service`;
- devuelva exactamente la última respuesta registrada;
- gestione correctamente la ausencia de contexto;
- gestione correctamente los errores de comunicación;
- no acceda directamente al Event Bus;
- no mantenga estado interno.

---

# Fuera de alcance

Quedan expresamente fuera de esta versión:

- repetir respuestas anteriores;
- historial conversacional;
- navegación por el historial;
- contexto multiusuario;
- contexto persistente;
- integración con memoria a largo plazo.