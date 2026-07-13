# Análisis – Nuevos Plugins Públicos de Identidad

**Documento de Análisis Funcional**

Versión: 1.0

---

# Objetivo

Incorporar tres nuevos plugins públicos relacionados con la identidad del sistema Nova:

* AuthorPlugin
* VersionPlugin
* HelpPlugin

Estos plugins deberán integrarse en el sistema de selección semántica del Orchestrator y seguir el Tone Guide oficial de Nova.  

---

# Plugins

## 1. AuthorPlugin

### Objetivo

Responder preguntas relacionadas con el autor o creador de Nova.

Debe informar únicamente del autor configurado en `system-service`.

No debe añadir información adicional.

---

### Fuente de datos

```
GET /v1/system/info
```

Campo utilizado:

```
author
```

---

### Prioridad

60 (Media)

---

### Frases de ejemplo

1. ¿Quién te ha creado?
2. ¿Quién te hizo?
3. ¿Quién es tu creador?
4. ¿Quién es el autor de Nova?
5. ¿Quién desarrolló Nova?
6. ¿Quién te desarrolló?
7. ¿Quién está detrás de Nova?
8. ¿Quién programó Nova?
9. ¿Quién ha construido este asistente?
10. ¿Quién es tu autor?

---

### Respuesta esperada

Suponiendo:

```
author = "Xeretre Studios"
```

Respuesta:

```
Nova ha sido desarrollada por Xeretre Studios.
```

---

### Casos de error

Si `system-service` no está disponible:

```
Servicio no disponible.
```

---

# 2. VersionPlugin

### Objetivo

Responder consultas sobre la versión instalada de Nova.

---

### Fuente de datos

```
GET /v1/system/info
```

Campo:

```
version
```

---

### Prioridad

60 (Media)

---

### Frases de ejemplo

1. ¿Qué versión eres?
2. ¿Qué versión tienes?
3. ¿Qué versión de Nova es esta?
4. ¿Cuál es tu versión?
5. ¿En qué versión estás?
6. Dime tu versión.
7. ¿Qué versión está instalada?
8. ¿Qué release tienes?
9. ¿Qué build estás ejecutando?
10. ¿Cuál es la versión actual?

---

### Respuesta esperada

Suponiendo:

```
version = 2.0.0
```

Respuesta:

```
Versión 2.0.0.
```

---

### Casos de error

```
Servicio no disponible.
```

---

# 3. HelpPlugin

### Objetivo

Explicar brevemente cómo debe utilizarse Nova.

Este plugin no enumera capacidades.

Su finalidad es enseñar el modelo de interacción.

Para descubrir las capacidades existentes continúa utilizándose el `CapabilitiesPlugin`. 

---

### Prioridad

60 (Media)

---

### Dependencias

Ninguna.

---

### Frases de ejemplo

1. ¿Cómo se usa Nova?
2. ¿Cómo te utilizo?
3. ¿Cómo puedo hablar contigo?
4. ¿Cómo funcionas?
5. ¿Cómo debo usarte?
6. Explícame cómo utilizar Nova.
7. ¿Cómo puedo darte órdenes?
8. Ayuda.
9. Necesito ayuda.
10. ¿Cómo empiezo?

---

### Respuesta esperada

```
Habla con naturalidad. Puedes hacer preguntas o pedir acciones directamente. Por ejemplo: "¿Qué tiempo hace?" o "Enciende la luz del salón."
```

La respuesta debe mantenerse breve y alineada con el Tone Guide.

---

### Casos de error

No aplica.

---

# Requisitos funcionales

## RF-01

El sistema deberá incorporar un nuevo plugin denominado **AuthorPlugin**.

---

## RF-02

El AuthorPlugin consultará dinámicamente el autor mediante `system-service`.

---

## RF-03

El sistema deberá incorporar un nuevo plugin denominado **VersionPlugin**.

---

## RF-04

El VersionPlugin consultará dinámicamente la versión mediante `system-service`.

---

## RF-05

El sistema deberá incorporar un nuevo plugin denominado **HelpPlugin**.

---

## RF-06

HelpPlugin devolverá una explicación breve sobre el modo de utilización de Nova.

---

## RF-07

Los tres plugins deberán participar en el algoritmo estándar de selección mediante RapidFuzz.

---

## RF-08

Cada plugin registrará automáticamente su capacidad en `system-service` durante el arranque del Orchestrator.

---

## RF-09

Los tres plugins deberán devolver un `PluginResult` compatible con el resto del ecosistema.

---

## RF-10

Las respuestas deberán seguir el Tone Guide oficial.

---

# Requisitos no funcionales

## RNF-01

Tiempo máximo de ejecución:

**< 100 ms**

(excluyendo latencia de red hacia `system-service`).

---

## RNF-02

Los plugins deberán ser completamente deterministas.

No utilizarán IA generativa.

---

## RNF-03

No deberán mantener estado interno.

---

## RNF-04

No almacenarán información persistente.

---

## RNF-05

En caso de fallo de comunicación con `system-service`, responderán:

```
Servicio no disponible.
```

---

## RNF-06

Las respuestas deberán ser breves.

No deberán superar una frase salvo en el caso del `HelpPlugin`.

---

## RNF-07

La inicialización del plugin no realizará llamadas HTTP.

Las conexiones deberán establecerse únicamente durante `execute()`.

---

## RNF-08

Todos los errores deberán registrarse mediante el sistema estándar de logging del Orchestrator.

---

# Capacidades registradas

Los plugins deberán publicar las siguientes capacidades durante el arranque:

| Plugin        | id        | Descripción                                    |
| ------------- | --------- | ---------------------------------------------- |
| AuthorPlugin  | `author`  | Información sobre el autor de Nova             |
| VersionPlugin | `version` | Información sobre la versión instalada de Nova |
| HelpPlugin    | `help`    | Explica cómo utilizar Nova                     |

---

# Criterios de aceptación

* El Orchestrator descubre automáticamente los tres plugins.
* Cada plugin aparece registrado en `system-service`.
* Las consultas sobre autor devuelven el autor configurado.
* Las consultas sobre versión devuelven la versión configurada.
* Las consultas de ayuda explican correctamente cómo utilizar Nova.
* Las respuestas cumplen el Tone Guide.
* Los errores de comunicación con `system-service` generan la respuesta **"Servicio no disponible."**
* Los tres plugins son seleccionados correctamente mediante el motor de similitud semántica.
