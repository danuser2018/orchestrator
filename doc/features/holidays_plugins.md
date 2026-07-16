# Nova Plugins - Civil Calendar

**Version:** 1.3

---

# Objetivo

Implementar los primeros plugins que integran Nova con el Calendar Service.

Estos plugins permitirán consultar información básica sobre el calendario civil utilizando el API REST del Calendar Service.

Todos los plugins consumirán exclusivamente el Calendar Service y no implementarán lógica relacionada con el cálculo de festivos.

Además, se incorporará una utilidad común para transformar intervalos de tiempo expresados en días en expresiones naturales adecuadas para interacción por voz.

---

# Plugins incluidos

Se implementarán los siguientes plugins:

1. TodayHolidayPlugin
2. NextHolidayPlugin
3. DaysUntilNextHolidayPlugin
4. HolidaysOfYearPlugin

---

# Arquitectura

## Servicio compartido

Los plugins **NextHolidayPlugin** y **DaysUntilNextHolidayPlugin** compartirán una única implementación interna.

Se implementará un servicio común, por ejemplo:

```
NextHolidayService
```

Este servicio será responsable de:

- Consumir el Calendar Service.
- Procesar la respuesta REST.
- Construir el modelo de datos utilizado por ambos plugins.
- Gestionar errores de comunicación.

Los plugins únicamente transformarán dicho modelo en la respuesta correspondiente para el usuario.

De esta forma se evita duplicar:

- llamadas REST
- modelos
- lógica de tratamiento de errores
- lógica de comunicación

---

## Utilidad común TimeFormatter

Se implementará una utilidad reutilizable dentro del Orchestrator denominada:

```
TimeFormatter
```

Su objetivo será transformar un número de días en una expresión natural para interacción por voz.

La utilidad será compartida por todos los plugins de Nova que necesiten expresar intervalos temporales.

No pertenece al dominio del calendario, sino a la capa de presentación de Nova.

### API

```
TimeFormatter.humanize_days(days: int) -> str
```

### Ejemplos

| Entrada | Salida esperada |
|---------:|-----------------|
| 0 | hoy |
| 1 | mañana |
| 2 | pasado mañana |
| 5 | cinco días |
| 7 | una semana |
| 14 | dos semanas |
| 21 | tres semanas |
| 30 | un mes |
| 45 | un mes y medio |
| 60 | dos meses |
| 88 | casi tres meses |
| 365 | un año |

La implementación no pretende ofrecer precisión matemática, sino una representación natural y fácilmente comprensible para el usuario.

---

# Requisitos funcionales

## RF-1. TodayHolidayPlugin

### Objetivo

Determinar si la fecha actual es festiva.

### Endpoint utilizado

```
GET /api/v1/holidays?date=<today>
```

### Ejemplos de frases

- ¿Hoy es festivo?
- ¿Es festivo hoy?
- ¿Hoy hay fiesta?
- ¿Hoy se trabaja?
- ¿Es fiesta hoy?

### Respuesta

Si hoy es festivo:

> Sí. Hoy es festivo. Se celebra <nombre del festivo>. Es un festivo <ámbito>.

Ejemplo:

> Sí. Hoy es festivo. Se celebra la Fiesta Nacional de España. Es un festivo nacional.

Si no es festivo:

> No. Hoy no es festivo.

---

## RF-2. NextHolidayPlugin

### Objetivo

Informar del siguiente festivo.

### Servicio utilizado

```
NextHolidayService
```

### Endpoint consumido

```
GET /api/v1/holidays/next?from=<today>
```

### Ejemplos de frases

- ¿Cuál es el próximo festivo?
- ¿Cuándo es el próximo festivo?
- ¿Qué festivo viene ahora?
- ¿Cuál es la próxima fiesta?
- ¿Cuál es el siguiente festivo?

### Respuesta

El plugin utilizará `TimeFormatter.humanize_days()` para expresar el tiempo restante.

Ejemplo:

> El próximo festivo es el lunes 12 de octubre. Se celebra la Fiesta Nacional de España. Es un festivo nacional. Falta casi tres meses.

---

## RF-3. DaysUntilNextHolidayPlugin

### Objetivo

Informar únicamente del tiempo restante hasta el siguiente festivo.

### Servicio utilizado

```
NextHolidayService
```

### Endpoint consumido

```
GET /api/v1/holidays/next?from=<today>
```

### Ejemplos de frases

- ¿Cuánto queda para el próximo festivo?
- ¿Cuántos días faltan para el siguiente festivo?
- ¿Cuándo descansamos otra vez?
- ¿Cuánto falta para el próximo festivo?

### Respuesta

El plugin utilizará `TimeFormatter.humanize_days()`.

Ejemplos:

> Falta casi un mes.

> Falta una semana.

> Falta mañana.

---

## RF-4. HolidaysOfYearPlugin

### Objetivo

Obtener el listado completo de festivos del año.

### Endpoint utilizado

```
GET /api/v1/holidays?year=<currentYear>
```

### Ejemplos de frases

- ¿Qué festivos hay este año?
- Dime los festivos de este año.
- ¿Cuáles son los festivos de este año?
- ¿Qué días festivos hay?

### Respuesta por voz

Como el listado puede ser demasiado largo para interacción por voz, el plugin responderá:

> Este año hay <N> festivos. Te he enviado el listado completo por correo electrónico.

---

## Correo electrónico

El plugin generará directamente el HTML del correo.

No utilizará plantillas Markdown.

El correo será enviado mediante el Mail Service.

### Asunto

```
Festivos de <AÑO>
```

### Formato

El correo incluirá:

- título
- año consultado
- tabla de festivos
- número total de festivos

La tabla contendrá las siguientes columnas:

| Fecha | Día | Festivo | Ámbito |
|-------|-----|----------|---------|

Donde el ámbito podrá ser:

- Nacional
- Regional
- Local

Los festivos aparecerán:

- ordenados cronológicamente
- incluyendo la fecha
- incluyendo el día de la semana
- incluyendo el nombre
- incluyendo el ámbito

Ejemplo:

| Fecha | Día | Festivo | Ámbito |
|-------|-----|----------|---------|
| 01/01/2026 | Jueves | Año Nuevo | Nacional |
| 06/01/2026 | Martes | Epifanía del Señor | Nacional |
| 15/06/2026 | Lunes | Festivo Local | Local |
| 12/10/2026 | Lunes | Fiesta Nacional de España | Nacional |

El correo finalizará indicando el número total de festivos.

---

# Requisitos no funcionales

## RNF-1

Los plugins no implementarán lógica relacionada con el calendario.

Toda la información deberá obtenerse mediante el Calendar Service.

---

## RNF-2

Los plugins utilizarán el cliente REST común de Nova.

---

## RNF-3

Las respuestas deberán ser breves y adecuadas para interacción por voz.

---

## RNF-4

Los errores de comunicación con Calendar Service deberán gestionarse de forma controlada.

Respuesta recomendada:

> Lo siento, ahora mismo no puedo consultar el calendario.

---

## RNF-5

El HolidaysOfYearPlugin generará directamente el HTML del correo electrónico y utilizará el Mail Service únicamente para su envío.

---

## RNF-6

La implementación compartida (`NextHolidayService`) será reutilizada por todos los plugins que necesiten consultar el siguiente festivo.

---

## RNF-7

La utilidad `TimeFormatter` deberá ser independiente del dominio del calendario para facilitar su reutilización por futuros plugins relacionados con eventos, recordatorios, temporizadores o aniversarios.

---

# Integración

## Dependencias

Todos los plugins dependerán de:

- Calendar Service

Además:

- HolidaysOfYearPlugin dependerá de Mail Service.

---

# Prioridad

Todos los plugins tendrán prioridad **normal**.

---

# Frases de entrenamiento

## TodayHolidayPlugin

- ¿Hoy es festivo?
- ¿Es festivo hoy?
- Hoy hay fiesta
- Hoy se trabaja
- ¿Hoy es fiesta?
- ¿Es día festivo?
- Dime si hoy es festivo
- ¿Tenemos fiesta hoy?
- Hoy es laboral
- ¿Hoy descansamos?

---

## NextHolidayPlugin

- ¿Cuál es el próximo festivo?
- ¿Cuándo es el siguiente festivo?
- ¿Qué festivo viene ahora?
- ¿Cuál es la próxima fiesta?
- Próximo festivo
- ¿Qué día es el próximo festivo?
- ¿Cuál será el siguiente festivo?
- Dime el próximo festivo
- ¿Qué fiesta viene después?
- Próxima fiesta

---

## DaysUntilNextHolidayPlugin

- ¿Cuánto queda para el próximo festivo?
- ¿Cuántos días faltan para el siguiente festivo?
- ¿Cuándo descansamos otra vez?
- ¿Cuánto falta para el próximo festivo?
- ¿Cuántos días quedan para la próxima fiesta?
- Dime cuánto falta para el siguiente festivo
- ¿Falta mucho para el próximo festivo?
- ¿Cuándo será la próxima fiesta?
- ¿En cuántos días es fiesta?
- ¿Cuánto queda para descansar?

---

## HolidaysOfYearPlugin

- ¿Qué festivos hay este año?
- Dime los festivos de este año
- ¿Cuáles son los festivos?
- Muéstrame los festivos
- Lista de festivos
- ¿Qué días festivos hay?
- ¿Qué fiestas hay este año?
- Enséñame el calendario laboral
- Quiero ver los festivos
- ¿Cuáles son los días festivos?

---

# Criterios de aceptación

- Los cuatro plugins se registran correctamente en el Orchestrator.
- Todos consumen el Calendar Service mediante su API REST.
- Ningún plugin implementa lógica de cálculo de fechas o festivos.
- TodayHolidayPlugin informa correctamente del nombre y del ámbito del festivo cuando corresponde.
- NextHolidayPlugin utiliza `TimeFormatter` para expresar el tiempo restante de forma natural.
- DaysUntilNextHolidayPlugin utiliza `TimeFormatter` para expresar el tiempo restante de forma natural.
- NextHolidayPlugin y DaysUntilNextHolidayPlugin reutilizan la misma implementación interna (`NextHolidayService`).
- `TimeFormatter` puede ser reutilizado por cualquier otro plugin del Orchestrator.
- HolidaysOfYearPlugin genera correctamente el HTML del correo electrónico con la tabla especificada.
- El correo incluye la fecha, el día de la semana, el nombre y el ámbito de todos los festivos.
- Todos los plugins gestionan correctamente errores de comunicación con Calendar Service.
- Todos los plugins incluyen pruebas unitarias.
- Todos los plugins superan la revisión DoD de Nova.