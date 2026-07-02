# Identity Plugin - Especificación de Implementación

## Objetivo

Implementar el plugin `IdentityPlugin` para Nova-2.

Este plugin será responsable exclusivamente de responder preguntas relacionadas con la identidad del asistente.

Su única función es responder a preguntas equivalentes a:

* ¿Quién eres?
* Quién eres
* Qué eres
* Cómo te llamas
* Dime quién eres

El plugin NO debe responder preguntas sobre:

* Autor
* Creador
* Desarrollador
* Propietario

Esas consultas serán gestionadas por otros plugins especializados.

---

# Responsabilidad funcional

El plugin debe identificar consultas cuya intención sea conocer la identidad del asistente.

La respuesta siempre se construye utilizando la información obtenida desde el System Service.

El plugin no contiene información de identidad hardcoded.

---

# Arquitectura

Flujo esperado:

Usuario
→ Orchestrator
→ IdentityPlugin
→ System Service
→ GET /system/info
→ JSON
→ PluginResult
→ Usuario

El plugin actúa únicamente como adaptador entre el Orchestrator y el System Service.

---

# Dependencias

El plugin realizará una petición HTTP al System Service.

Tecnologías recomendadas:

* httpx (preferido)
* aiohttp

Las llamadas deben ser asíncronas.

---

# Configuración

La URL base del servicio se obtiene mediante:

```bash
SYSTEM_SERVICE_BASE_URL
```

Valor por defecto:

```bash
http://system-service:8000
```

Endpoint consumido:

```text
{SYSTEM_SERVICE_BASE_URL}/v1/system/info
```

Ejemplo:

```text
http://system-service:8000/v1/system/info
```

---

# Endpoint consumido

## Request

```http
GET /v1/system/info
```

## Response esperada

```json
{
  "name": "Nova",
  "author": "David",
  "version": "2.5.0",
  "description": "Asistente personal de voz y automatización"
}
```

---

# Modelo esperado

```python
class SystemInfo(BaseModel):
    name: str
    author: str
    version: str
    description: str
```

---

# Regla de construcción del Display Name

El nombre visible utilizado por Nova debe construirse dinámicamente a partir de los campos:

* `name`
* `version`

obtenidos desde `/system/info`.

El plugin nunca debe utilizar nombres hardcoded.

---

## Objetivo

Generar un identificador estable para que Nova pueda presentarse al usuario de forma consistente independientemente de la versión menor o de mantenimiento instalada.

La versión visible para el usuario se construye utilizando únicamente el número de versión mayor (major version).

---

## Algoritmo

A partir de:

```json
{
  "name": "Nova",
  "version": "2.5.0"
}
```

Extraer:

```text
major = 2
```

Construir:

```text
Nova-2
```

---

## Regla formal

Si:

```text
name = <nombre del sistema>
version = MAJOR.MINOR.PATCH
```

Entonces:

```text
display_name = "{name}-{MAJOR}"
```

Donde:

* MAJOR se obtiene de la primera parte de la versión semántica.
* MINOR se ignora.
* PATCH se ignora.

---

## Ejemplos válidos

### Ejemplo 1

Entrada:

```json
{
  "name": "Nova",
  "version": "1.0.0"
}
```

Resultado:

```text
Nova-1
```

---

### Ejemplo 2

Entrada:

```json
{
  "name": "Nova",
  "version": "1.0.3"
}
```

Resultado:

```text
Nova-1
```

---

### Ejemplo 3

Entrada:

```json
{
  "name": "Nova",
  "version": "2.5.0"
}
```

Resultado:

```text
Nova-2
```

---

### Ejemplo 4

Entrada:

```json
{
  "name": "Nova",
  "version": "3.12.8"
}
```

Resultado:

```text
Nova-3
```

---

## Preservación del nombre

El plugin no debe asumir que el nombre del producto es siempre "Nova".

Debe utilizar exactamente el valor recibido desde el System Service.

El campo `name` debe preservarse íntegramente.

---

### Ejemplo

Entrada:

```json
{
  "name": "Nova Enterprise",
  "version": "2.5.0"
}
```

Resultado:

```text
Nova Enterprise-2
```

---

### Ejemplo

Entrada:

```json
{
  "name": "Nova Home",
  "version": "4.0.1"
}
```

Resultado:

```text
Nova Home-4
```

---

## Implementación recomendada

```python
def build_display_name(name: str, version: str) -> str:
    major = version.split(".")[0]
    return f"{name}-{major}"
```

---

## Validación

Si el campo `version` no tiene un formato válido:

```text
MAJOR.MINOR.PATCH
```

el plugin debe registrar el error y devolver:

```python
PluginResult(
    success=False,
    speech="No he podido obtener la información."
)
```

No se deben realizar intentos de inferencia ni corrección automática.

El comportamiento debe ser completamente determinista.

---

# Estructura física

```text
plugins/
└── identity/
    ├── main.py
    └── requirements.txt
```

La configuración del plugin se define de manera centralizada en `core/config.py` y la comunicación HTTP asíncrona se realiza utilizando el cliente central `SystemServiceClient` ubicado en `core/system_service_client.py` (evitando así lógica HTTP duplicada o dispersa por los directorios de los plugins).

---

# Definición del plugin

## Nombre

```text
IdentityPlugin
```

## Descripción

Responde consultas sobre la identidad de Nova.

---

# Keywords

```python
[
    "quien",
    "eres",
    "nova",
    "llamas",
    "identidad"
]
```

---

# Regex

```python
[
    r"quien.*eres",
    r"que.*eres",
    r"como.*te.*llamas",
    r"dime.*quien.*eres"
]
```

No deben añadirse patrones relacionados con:

* autor
* creador
* desarrollado por

Estas consultas pertenecen a otros plugins.

---

# Respuesta principal

La respuesta estándar debe seguir el Tone Guide oficial.

Formato:

```text
Soy {display_name}, tu sistema local de automatización.
```

---

## Ejemplo

Entrada:

```text
¿Quién eres?
```

Respuesta:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

## Ejemplo

Entrada:

```text
¿Cómo te llamas?
```

Respuesta:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

## Ejemplo

Entrada:

```text
¿Qué eres?
```

Respuesta:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

# Tone Guide

Las respuestas deben cumplir:

* Breves
* Claras
* Deterministas
* Sin conversación adicional
* Sin personalidad excesiva
* Sin humor

Prohibido:

* Explicaciones largas
* Frases promocionales
* Información adicional no solicitada

Incorrecto:

```text
Hola. Soy Nova, una avanzada inteligencia artificial diseñada para ayudarte.
```

Correcto:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

# Gestión de errores

## Error de conexión

```python
PluginResult(
    success=False,
    speech="Servicio no disponible."
)
```

---

## Timeout

```python
PluginResult(
    success=False,
    speech="Servicio no disponible."
)
```

---

## JSON inválido

```python
PluginResult(
    success=False,
    speech="No he podido obtener la información."
)
```

---

## Excepción inesperada

```python
PluginResult(
    success=False,
    speech="No he podido obtener la información."
)
```

No exponer detalles internos al usuario.

---

# Logging

Nivel INFO:

* Inicio de ejecución
* URL consumida
* Respuesta recibida
* Display name generado

Nivel ERROR:

* Timeout
* Error HTTP
* Error de serialización
* Excepciones inesperadas

---

# Datos opcionales de debug

```python
data={
    "name": system_info.name,
    "version": system_info.version,
    "display_name": display_name
}
```

Estos datos son únicamente para observabilidad.

No deben formar parte del speech.

---

# Criterios de aceptación

## Escenario 1

Entrada:

```text
¿Quién eres?
```

Resultado:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

## Escenario 2

Entrada:

```text
¿Cómo te llamas?
```

Resultado:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

## Escenario 3

Entrada:

```text
¿Qué eres?
```

Resultado:

```text
Soy Nova-2, tu sistema local de automatización.
```

---

## Escenario 4

System Service no disponible.

Resultado:

```text
Servicio no disponible.
```

---

## Escenario 5

La identidad se obtiene completamente desde:

```http
GET /v1/system/info
```

No existen datos de identidad hardcoded dentro del plugin.

---

# Restricciones

Obligatorio:

* Plugin asíncrono
* Uso de PluginContext
* Uso de PluginResult
* Consumo de GET /v1/system/info
* Uso de SYSTEM_SERVICE_BASE_URL
* Construcción dinámica del display name usando únicamente el major version

Prohibido:

* Uso de LLMs
* Datos de identidad hardcoded
* Consultas sobre autor o creador
* Conversación libre

El comportamiento debe ser completamente determinista.
