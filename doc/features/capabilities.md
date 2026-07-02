# Capabilities Plugin

## Objetivo

Implementar un nuevo plugin del Orchestrator capaz de responder a preguntas como:

* ¿Qué puedes hacer?
* ¿Qué sabes hacer?
* ¿Qué funciones tienes?
* ¿Qué eres capaz de hacer?

El plugin deberá consultar las capacidades registradas en `system-service`, generar un correo con el listado completo y solicitar su envío mediante el `mail-watchdog`.

El usuario recibirá una respuesta breve por voz indicando el número de funciones disponibles y que el detalle ha sido enviado por correo.

---

# Responsabilidades

El plugin debe:

1. Consultar las capacidades disponibles en `system-service`.
2. Generar un correo en texto plano con el listado de funciones.
3. Depositar un artefacto JSON en `/shared/mail/pending` siguiendo el contrato de `mail-watchdog`.
4. Devolver una respuesta hablada mediante `PluginResult`.

El plugin **no debe**:

* enviar correos directamente mediante SMTP;
* conocer la implementación del Mail Watchdog;
* mantener información persistente;
* modificar el registro de capacidades.

---

# Flujo de ejecución

```text
Usuario
    ↓
Capabilities Plugin
    ↓
GET /system/capabilities
    ↓
Lista de capacidades
    ↓
Construcción del correo
    ↓
Creación de mail-<uuid>.json
    ↓
/shared/mail/pending
    ↓
PluginResult
```

---

# Dependencias

## system-service

Endpoint:

```
GET /system/capabilities
```

Respuesta esperada:

```json
{
  "capabilities": [
    {
      "id": "identity",
      "description": "Información sobre Nova"
    },
    {
      "id": "weather",
      "description": "Consultar el tiempo"
    }
  ]
}
```

---

## Mail Watchdog

El plugin deberá generar un artefacto compatible con el contrato existente:

```json
{
  "id": "mail-xxxxxxxx",
  "to": "<USER_EMAIL>",
  "subject": "Capacidades disponibles en Nova",
  "body": "...",
  "content_type": "text/plain"
}
```

El fichero deberá escribirse en:

```
/shared/mail/pending
```

No deberá esperar confirmación del envío.

---

# Configuración

Se añade una nueva variable de entorno al Orchestrator:

```env
USER_EMAIL=user@example.com
```

El plugin utilizará esta dirección como destinatario del correo.

No deberá solicitar el correo al usuario ni utilizar otros servicios.

---

# Formato del correo

Asunto:

```
Capacidades disponibles en Nova
```

Cuerpo:

```
Hola.

Actualmente puedo realizar N funciones.

Estas son las capacidades disponibles:

• Información sobre Nova
• Consultar el tiempo
• ...

Este listado se genera automáticamente a partir de las capacidades registradas en el sistema.
```

Las capacidades deberán aparecer ordenadas alfabéticamente por descripción para facilitar su consulta.

---

# Respuesta hablada

Si todo ha ido correctamente:

```
Actualmente puedo realizar N funciones. Te he enviado un correo con el listado completo para que puedas consultarlo cuando quieras.
```

---

# Gestión de errores

## Error consultando system-service

Si no es posible recuperar las capacidades:

* no debe generarse ningún correo;
* el plugin devolverá un `PluginResult(success=false)` indicando que no ha podido consultar las funciones disponibles.

Respuesta sugerida:

```
Lo siento, ahora mismo no puedo consultar las funciones disponibles.
```

---

## Error creando el artefacto

Si falla la escritura del fichero:

* devolver `PluginResult(success=false)`;
* registrar el error en logs.

Respuesta sugerida:

```
Lo siento, ha ocurrido un problema al preparar el correo.
```

---

# Matching

El plugin deberá responder, al menos, a expresiones como:

* qué puedes hacer
* qué sabes hacer
* qué funciones tienes
* qué eres capaz de hacer

Podrán añadirse sinónimos adicionales.

---

# Observabilidad

Registrar como mínimo:

* consulta a `system-service`;
* número de capacidades recuperadas;
* creación del artefacto de correo;
* ruta del fichero generado;
* errores durante la ejecución.

---

# Criterios de aceptación

* El plugin es descubierto automáticamente por el Orchestrator.
* Consulta correctamente `GET /system/capabilities`.
* Genera un correo con todas las descripciones registradas.
* Escribe un artefacto compatible con el Mail Watchdog.
* Devuelve una respuesta hablada indicando el número de funciones.
* No realiza llamadas SMTP.
* No mantiene estado.
* Cumple la arquitectura desacoplada de Nova.

# Metadatos del plugin

El plugin deberá exponer los siguientes metadatos:

## Nombre

```text
CapabilitiesPlugin
```

---

## Descripción

```text
Responde preguntas sobre las funciones disponibles en Nova y envía al usuario un correo con el listado completo de capacidades registradas.
```

---

## Keywords

Las keywords ayudan al motor de scoring del Orchestrator.

```python
[
    "hacer",
    "funciones",
    "capacidades",
    "puedes",
    "sabes",
    "ayuda"
]
```

---

## Expresiones regulares

El plugin deberá reconocer, al menos, las siguientes expresiones:

```python
[
    r".*qué.*puedes.*hacer.*",
    r".*que.*puedes.*hacer.*",
    r".*qué.*sabes.*hacer.*",
    r".*que.*sabes.*hacer.*",
    r".*qué.*funciones.*tienes.*",
    r".*que.*funciones.*tienes.*",
    r".*qué.*eres.*capaz.*de.*hacer.*",
    r".*que.*eres.*capaz.*de.*hacer.*"
]
```

Podrán añadirse expresiones adicionales para mejorar la cobertura.
