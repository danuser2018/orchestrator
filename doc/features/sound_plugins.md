# Especificación de Requisitos

# Plugins de Control de Volumen

**Versión:** 1.0
**Estado:** Propuesta

---

# 1. Introducción

## 1.1 Objetivo

Esta especificación define la segunda fase de integración del **Host Service** dentro del ecosistema Nova mediante la incorporación de cinco nuevos plugins de control de volumen.

Estos plugins permitirán al usuario consultar y modificar el volumen del sistema utilizando lenguaje natural, delegando todas las operaciones sobre el sistema operativo en el **host-service**.

---

## 1.2 Alcance

Esta fase incorpora los siguientes plugins:

* Volume Up Plugin
* Volume Down Plugin
* Volume Status Plugin
* Mute Plugin
* Unmute Plugin

Todos ellos consumirán exclusivamente la API REST del **host-service**.

---

# 2. Arquitectura

Los plugins no ejecutarán comandos del sistema.

Toda interacción con el host se realizará mediante llamadas HTTP al Host Service.

```text
Usuario
      │
      ▼
STT
      │
      ▼
Orchestrator
      │
      ▼
Volume Plugin
      │
 HTTP REST
      ▼
Host Service
      │
      ▼
Linux (pactl)
```

---

# 3. Requisitos Funcionales

## RF-001

El sistema deberá incorporar un plugin para incrementar el volumen.

---

## RF-002

El sistema deberá incorporar un plugin para disminuir el volumen.

---

## RF-003

El sistema deberá incorporar un plugin para consultar el volumen actual.

---

## RF-004

El sistema deberá incorporar un plugin para silenciar el sistema.

---

## RF-005

El sistema deberá incorporar un plugin para restaurar el sonido.

---

## RF-006

Todos los plugins deberán utilizar exclusivamente el Host Service.

---

## RF-007

Ningún plugin ejecutará comandos del sistema operativo.

---

# 4. Plugins

---

# 4.1 Volume Up Plugin

## Objetivo

Incrementar el volumen del sistema.

---

## Ejemplos de activación

* Sube el volumen
* Sube un poco el volumen
* Más volumen
* Pon el volumen más alto
* Aumenta el volumen
* Quiero más volumen
* Dale más volumen
* Súbelo
* Un poco más alto
* Se oye bajo

---

## Flujo

1. Invocar

```
POST /v1/audio/volume/up
```

2. El Host Service incrementará el volumen en un paso fijo.

3. El Host Service devolverá el nuevo estado.

4. El plugin generará la respuesta.

---

## Respuestas

### Caso normal

> El nuevo volumen es 40.

---

### Volumen máximo

> El volumen ya está al máximo.

No deberá considerarse un error.

---

## Reglas

El incremento será fijo.

Valor inicial recomendado:

```
10
```

---

# 4.2 Volume Down Plugin

## Objetivo

Reducir el volumen.

---

## Ejemplos

* Baja el volumen
* Menos volumen
* Baja un poco
* Está muy alto
* Reduce el volumen
* Bájalo
* Un poco menos
* Demasiado volumen
* Ponlo más bajo
* Quiero menos volumen

---

## Flujo

```
POST /v1/audio/volume/down
```

---

## Respuestas

### Caso normal

> El nuevo volumen es 30.

---

### Volumen mínimo

> El volumen ya está al mínimo.

No deberá considerarse un error.

---

## Reglas

La reducción será fija.

Valor recomendado:

```
10
```

---

# 4.3 Volume Status Plugin

## Objetivo

Consultar el volumen.

---

## Ejemplos

* ¿Cuál es el volumen?
* ¿Qué volumen tengo?
* ¿Cuál es el volumen actual?
* Dime el volumen
* ¿Cómo está el volumen?
* Nivel de volumen
* ¿A cuánto está el volumen?
* Volumen actual
* ¿Qué nivel de sonido hay?
* ¿Está muy alto el volumen?

---

## Flujo

```
GET /v1/audio/volume
```

---

## Respuestas

### Audio activo

> El volumen actual es 60.

---

### Sistema silenciado

> El volumen está al 60 y el sonido está silenciado.

---

# 4.4 Mute Plugin

## Objetivo

Silenciar el sistema.

---

## Ejemplos

* Mutéate
* Silénciate
* Quítate el sonido
* Ponte en silencio
* Deja de hacer ruido
* No hables
* Silencio
* Apaga el sonido
* Enmudece
* No quiero oírte

---

## Flujo

```
POST /v1/audio/mute
```

---

## Respuestas

El plugin generará una respuesta de confirmación.

Ejemplo:

> De acuerdo.

Sin embargo, el usuario no la escuchará porque el sistema habrá quedado silenciado.

Este comportamiento es completamente válido.

---

### Sistema ya silenciado

No deberá producir error.

El Host Service deberá responder correctamente y el plugin finalizará normalmente.

---

# 4.5 Unmute Plugin

## Objetivo

Restaurar el sonido.

---

## Ejemplos

* Desmutéate
* Activa el sonido
* Recupera el sonido
* Vuelve a hablar
* Quita el silencio
* Ya puedes hablar
* Activa el audio
* Devuelve el sonido
* Sal del modo silencio
* Ya puedes hacer ruido

---

## Flujo

```
POST /v1/audio/unmute
```

---

## Respuesta

> Ya puedo hablar otra vez.

---

### Sistema ya desmuteado

No deberá producir error.

Puede responder igualmente:

> Ya puedo hablar otra vez.

---

# 5. Reglas de negocio

## RN-001

Los incrementos de volumen serán constantes.

Valor inicial:

```
10
```

---

## RN-002

El volumen nunca podrá superar 100.

---

## RN-003

El volumen nunca podrá ser inferior a 0.

---

## RN-004

Cuando se alcance el límite superior se responderá:

> El volumen ya está al máximo.

---

## RN-005

Cuando se alcance el límite inferior se responderá:

> El volumen ya está al mínimo.

---

## RN-006

Llegar al máximo o al mínimo no constituye un error.

---

## RN-007

Mutear un sistema ya silenciado no constituye un error.

---

## RN-008

Desmutear un sistema que ya tiene sonido tampoco constituye un error.

---

## RN-009

Las respuestas deberán construirse utilizando el estado devuelto por Host Service.

Los plugins nunca mantendrán estado propio.

---

# 6. Requisitos No Funcionales

## RNF-001

Los plugins deberán ser completamente stateless.

---

## RNF-002

Todos los plugins utilizarán exclusivamente la API REST del Host Service.

---

## RNF-003

No se permitirá el uso de `subprocess`, `os.system` o llamadas equivalentes desde los plugins.

---

## RNF-004

Las respuestas deberán seguir el Tone Guide de Nova.

---

## RNF-005

Los tiempos de respuesta deberán ser inferiores a 250 ms excluyendo la síntesis de voz.

---

# Anexo A

# Dependencias

Todos los plugins dependerán de:

```
HOST_SERVICE_BASE_URL
```

Ejemplo:

```
http://host-service:8000
```

---

# Anexo B

# Endpoints utilizados

| Plugin        | Endpoint                   |
| ------------- | -------------------------- |
| Volume Up     | POST /v1/audio/volume/up   |
| Volume Down   | POST /v1/audio/volume/down |
| Volume Status | GET /v1/audio/volume       |
| Mute          | POST /v1/audio/mute        |
| Unmute        | POST /v1/audio/unmute      |

---

# Anexo C

# Contrato esperado

Todas las operaciones deberán devolver una estructura equivalente a:

```json
{
    "volume": 40,
    "muted": false
}
```

De este modo los plugins no necesitan conocer cómo se implementa el Host Service ni consultar el estado mediante llamadas adicionales.

---

# Anexo D

# Consideraciones de UX

Las operaciones de mute presentan una característica especial: la respuesta hablada generada por Nova puede no ser escuchada porque el sistema queda silenciado inmediatamente antes de reproducirse.

Este comportamiento se considera aceptable y no requiere tratamiento específico. Los plugins mantendrán el mismo flujo de ejecución que cualquier otro plugin, preservando la consistencia del pipeline de interacción de Nova.

Asimismo, las operaciones sobre estados ya alcanzados (máximo, mínimo, mute o unmute) se tratarán como operaciones idempotentes. En lugar de devolver errores, el sistema informará al usuario de que el estado solicitado ya estaba aplicado, proporcionando una experiencia de uso natural y predecible.
