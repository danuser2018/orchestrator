Perfecto. Además, después de leer la especificación del `IdentityPlugin`, cambiaría ligeramente la propuesta. Ya existe un patrón claro en el Orchestrator para acceder a `system-service` (configuración, cliente HTTP, etc.), así que no intentaría introducir una arquitectura distinta. La evolución más natural es **reutilizar ese mismo patrón**.

Yo le pediría a Antigravity algo como esto:

# Orchestrator — Publicación de capacidades en System Service

## Objetivo

Modificar el proceso de inicialización del Orchestrator para que, una vez descubiertos y registrados todos los plugins, publique automáticamente la lista de capacidades disponibles en el `system-service`.

Esta modificación amplía la integración ya existente con `system-service`.

Actualmente el `IdentityPlugin` consume:

```text
GET /system/info
```

Tras esta implementación, el propio Orchestrator también consumirá:

```text
POST /v1/system/capabilities
```

utilizando la misma configuración base del servicio.

---

# Contexto

El Orchestrator es la única fuente de verdad sobre las capacidades disponibles.

Durante el arranque:

1. Descubre los plugins.
2. Los registra.
3. Publica la lista completa de capacidades.

Posteriormente cualquier componente podrá consultar dicha información mediante:

```text
GET /system/capabilities
```

sin depender del Orchestrator.

---

# Flujo de arranque

El flujo de inicialización pasa a ser:

```text
Inicio

↓

Cargar configuración

↓

Inicializar PluginManager

↓

Descubrir plugins

↓

Registrar plugins

↓

Construir lista de capacidades

↓

POST /system/capabilities

↓

Finalizar inicialización

↓

Aceptar peticiones
```

La publicación debe ejecutarse exactamente una vez durante el arranque.

---

# Configuración

No crear nuevas variables de configuración.

Debe reutilizarse la configuración ya existente para acceder al System Service.

Actualmente existe:

```bash
SYSTEM_SERVICE_BASE_URL
```

La publicación utilizará:

```text
{SYSTEM_SERVICE_BASE_URL}/v1/system/capabilities
```

---

# Cliente HTTP

Seguir el mismo patrón utilizado por el `IdentityPlugin`.

No realizar llamadas HTTP directamente desde el código de inicialización.

Extraer la comunicación con `system-service` a un cliente reutilizable.

Si ya existe un cliente reutilizable para el `IdentityPlugin`, ampliarlo.

Si el cliente pertenece únicamente al plugin, mover la lógica común a un módulo compartido del Orchestrator para evitar duplicación.

El objetivo es disponer de un único lugar responsable de la comunicación HTTP con `system-service`.

---

# Obtención de capacidades

Una vez cargados los plugins, recorrer la colección registrada por el `PluginManager`.

Para cada plugin construir un descriptor público.

Modelo:

```json
{
    "id": "weather",
    "description": "Consultar información meteorológica"
}
```

No deben enviarse:

* keywords
* regex
* prioridades
* configuración
* permisos
* información interna

Únicamente información pública.

---

# Publicación

Enviar:

```http
POST /v1/system/capabilities
```

Body:

```json
{
    "capabilities": [
        {
            "id": "identity",
            "description": "Información sobre Nova"
        },
        {
            "id": "weather",
            "description": "Consultar información meteorológica"
        },
        {
            "id": "mail",
            "description": "Enviar y consultar correo"
        }
    ]
}
```

La lista enviada representa el estado completo del sistema.

Cada publicación reemplaza completamente el contenido anterior.

---

# Gestión de errores

La publicación de capacidades no debe impedir el arranque del Orchestrator.

## Publicación correcta

Registrar un mensaje INFO.

Ejemplo:

```text
Published 8 capabilities to System Service.
```

---

## Error HTTP

Registrar WARNING.

Continuar el proceso de inicialización.

---

## Timeout

Registrar WARNING.

Continuar el proceso de inicialización.

---

## Error inesperado

Registrar ERROR.

Continuar el proceso de inicialización.

El Orchestrator debe permanecer completamente operativo incluso si el `system-service` no está disponible.

---

# Logging

Registrar al menos:

* número de plugins descubiertos
* número de capacidades publicadas
* URL utilizada
* resultado de la operación

---

# Restricciones

Obligatorio:

* reutilizar `SYSTEM_SERVICE_BASE_URL`
* reutilizar el patrón de acceso HTTP existente al `system-service`
* publicar una única vez durante el arranque
* enviar la lista completa de capacidades
* continuar el arranque aunque falle la publicación

Prohibido:

* llamadas HTTP dispersas por el código
* descubrimiento adicional de plugins
* duplicar la configuración existente
* detener el Orchestrator si la publicación falla

---

# Criterios de aceptación

## Escenario 1

El Orchestrator arranca correctamente.

Se descubren los plugins.

Se realiza un único:

```http
POST /v1/system/capabilities
```

con todas las capacidades registradas.

---

## Escenario 2

El `system-service` no está disponible.

Se registra el error.

El Orchestrator termina de arrancar normalmente.

---

## Escenario 3

Tras añadir un nuevo plugin al sistema y reiniciar el Orchestrator, la nueva capacidad aparece automáticamente en la publicación realizada al `system-service`, sin necesidad de modificar ningún otro componente.

Lo único que añadiría como mejora respecto a tu diseño actual es un pequeño cambio en el contrato base de los plugins: hacer que `description` sea **obligatoria** en lugar de opcional. Ya la estás usando para documentar los plugins (como el `IdentityPlugin`), y ahora pasa a formar parte de una API pública (`/system/capabilities`). Eso convierte la descripción en parte del contrato del plugin, no solo en documentación, y garantiza que el listado de capacidades siempre sea útil para otros servicios y para el futuro plugin "¿Qué puedes hacer?".
