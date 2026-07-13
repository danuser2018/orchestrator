# Análisis – Plugins de Fecha y Hora

**Documento de Análisis Funcional**

Versión: 1.0

---

# Objetivo

Incorporar dos nuevos plugins públicos relacionados con la fecha y la hora del sistema:

* TimePlugin
* DatePlugin

Ambos plugins deberán obtener la información directamente del reloj del sistema y generar respuestas compatibles con el Tone Guide de Nova.

---

# Plugins

## 1. TimePlugin

### Objetivo

Responder consultas relacionadas con la hora actual del sistema.

---

### Fuente de datos

Reloj del sistema operativo.

---

### Prioridad

80 (Alta)

Se considera una consulta frecuente y completamente determinista.

---

### Frases de ejemplo

1. ¿Qué hora es?
2. Dime la hora.
3. ¿Me dices la hora?
4. ¿Qué hora tenemos?
5. ¿Puedes decirme la hora?
6. Necesito saber la hora.
7. Hora actual.
8. ¿Cuál es la hora?
9. ¿Qué hora marca el reloj?
10. ¿Tienes la hora?

---

### Respuesta esperada

Suponiendo que son las 15:42:

```text
Son las 15:42.
```

---

### Casos de error

Si por cualquier motivo no pudiera obtenerse la hora del sistema:

```text
No he podido obtener la hora.
```

---

# 2. DatePlugin

### Objetivo

Responder consultas relacionadas con la fecha actual.

El usuario podrá preguntar por:

* la fecha
* el día
* el mes
* el año

En todos los casos la respuesta será la fecha completa.

---

### Fuente de datos

Reloj del sistema operativo.

---

### Prioridad

80 (Alta)

---

### Frases de ejemplo

1. ¿Qué día es hoy?
2. ¿Cuál es la fecha de hoy?
3. ¿Qué fecha es?
4. ¿En qué mes estamos?
5. ¿En qué año estamos?
6. Dime la fecha.
7. ¿Qué día tenemos hoy?
8. ¿Qué mes es?
9. ¿Qué año es?
10. Fecha actual.

---

### Respuesta esperada

Suponiendo:

* lunes
* 13 de julio de 2026

Respuesta:

```text
Hoy es lunes, 13 de julio de 2026.
```

Siempre se devolverá la fecha completa independientemente de la pregunta.

Ejemplos:

Usuario:

> ¿Qué mes es?

Respuesta:

```text
Hoy es lunes, 13 de julio de 2026.
```

Usuario:

> ¿En qué año estamos?

Respuesta:

```text
Hoy es lunes, 13 de julio de 2026.
```

Usuario:

> ¿Qué día es hoy?

Respuesta:

```text
Hoy es lunes, 13 de julio de 2026.
```

---

### Casos de error

```text
No he podido obtener la fecha.
```

---

# Requisitos funcionales

## RF-01

El sistema deberá incorporar un plugin denominado **TimePlugin**.

---

## RF-02

El TimePlugin devolverá la hora actual del sistema.

---

## RF-03

La respuesta utilizará formato de 24 horas.

Ejemplo:

```text
Son las 08:05.
```

---

## RF-04

El sistema deberá incorporar un plugin denominado **DatePlugin**.

---

## RF-05

El DatePlugin responderá consultas sobre:

* fecha
* día
* mes
* año

---

## RF-06

Todas las consultas devolverán la fecha completa.

Ejemplo:

```text
Hoy es lunes, 13 de julio de 2026.
```

---

## RF-07

El nombre de los días de la semana deberá generarse en español.

---

## RF-08

El nombre de los meses deberá generarse en español.

---

## RF-09

Ambos plugins deberán participar en el algoritmo estándar de selección mediante RapidFuzz.

---

## RF-10

Ambos plugins deberán registrar automáticamente sus capacidades durante el arranque del Orchestrator.

---

## RF-11

Ambos plugins devolverán un `PluginResult` compatible con el resto del ecosistema.

---

## RF-12

Las respuestas deberán cumplir el Tone Guide.

---

# Requisitos no funcionales

## RNF-01

Tiempo máximo de ejecución:

**< 10 ms**

No existen llamadas de red.

---

## RNF-02

Los plugins serán completamente deterministas.

---

## RNF-03

No dependerán de servicios externos.

---

## RNF-04

No realizarán llamadas HTTP.

---

## RNF-05

No mantendrán estado interno.

---

## RNF-06

No almacenarán información persistente.

---

## RNF-07

Toda la información procederá exclusivamente del reloj del sistema operativo.

---

## RNF-08

Las respuestas deberán ser breves.

---

## RNF-09

Los errores deberán registrarse mediante el sistema estándar de logging del Orchestrator.

---

# Capacidades registradas

| Plugin     | id     | Descripción              |
| ---------- | ------ | ------------------------ |
| TimePlugin | `time` | Consulta la hora actual  |
| DatePlugin | `date` | Consulta la fecha actual |

---

# Criterios de aceptación

* El Orchestrator descubre automáticamente ambos plugins.
* Ambos aparecen registrados en `system-service`.
* Las consultas sobre la hora devuelven correctamente la hora del sistema en formato de 24 horas.
* Las consultas sobre fecha, día, mes o año devuelven siempre la fecha completa.
* Los nombres de los días y los meses aparecen en español.
* Las respuestas cumplen el Tone Guide.
* Ambos plugins son seleccionados correctamente mediante el motor de similitud semántica.

### Recomendación de diseño

Hay un pequeño detalle que creo que merece la pena añadir al documento: crear un **DateTimeService** interno (una utilidad compartida, no un microservicio) que encapsule la obtención y el formateo de la fecha y la hora. Así ambos plugins reutilizan la misma lógica para el locale español, el formato de 24 horas y la construcción de textos como *"Hoy es lunes, 13 de julio de 2026."*. Esto evita duplicar código y hace que cualquier cambio de formato futuro se realice en un único punto.
