# Análisis – Plugins Aleatorios (Random)

**Documento de Análisis Funcional**

Versión: 1.0

---

# Objetivo

Incorporar tres nuevos plugins públicos relacionados con la generación de resultados aleatorios:

* CoinPlugin
* DicePlugin
* RandomNumberPlugin

Todos los plugins deberán utilizar un generador de números pseudoaleatorios del sistema y generar respuestas compatibles con el Tone Guide de Nova.

---

# Plugins

## 1. CoinPlugin

### Objetivo

Simular el lanzamiento de una moneda.

El resultado será siempre uno de los siguientes:

* Cara
* Cruz

---

### Fuente de datos

Generador pseudoaleatorio del lenguaje (Python `random`).

---

### Prioridad

60 (Media)

---

### Frases de ejemplo

1. Lanza una moneda.
2. Tira una moneda.
3. Cara o cruz.
4. Decide con una moneda.
5. Haz un cara o cruz.
6. Lanza una moneda al aire.
7. Necesito un cara o cruz.
8. Elige cara o cruz.
9. Vamos a lanzar una moneda.
10. Moneda.

---

### Respuestas esperadas

```text
Cara.
```

o

```text
Cruz.
```

---

### Casos de error

No aplica.

---

# 2. DicePlugin

### Objetivo

Simular el lanzamiento de un dado clásico de seis caras.

---

### Fuente de datos

Generador pseudoaleatorio del lenguaje.

---

### Prioridad

60 (Media)

---

### Frases de ejemplo

1. Tira un dado.
2. Lanza un dado.
3. Necesito un dado.
4. Haz una tirada de dado.
5. Dime un número del dado.
6. Lanza el dado.
7. Vamos a tirar un dado.
8. Tira los dados.
9. Quiero lanzar un dado.
10. Dado.

---

### Respuestas esperadas

```text
Ha salido un 1.
```

```text
Ha salido un 2.
```

...

```text
Ha salido un 6.
```

---

### Casos de error

No aplica.

---

# 3. RandomNumberPlugin

### Objetivo

Generar un número aleatorio comprendido entre **1 y 99**, ambos inclusive.

El rango es fijo y no configurable en esta versión.

---

### Fuente de datos

Generador pseudoaleatorio del lenguaje.

---

### Prioridad

60 (Media)

---

### Frases de ejemplo

1. Elige un número.
2. Dime un número.
3. Dame un número aleatorio.
4. Escoge un número.
5. Número al azar.
6. Piensa un número.
7. Necesito un número.
8. Elige un número para mí.
9. Genera un número.
10. Número aleatorio.

---

### Respuestas esperadas

Ejemplos:

```text
37.
```

```text
82.
```

```text
5.
```

Siempre será un entero comprendido entre **1 y 99**.

---

### Casos de error

No aplica.

---

# Requisitos funcionales

## RF-01

El sistema deberá incorporar un plugin denominado **CoinPlugin**.

---

## RF-02

CoinPlugin devolverá únicamente uno de los siguientes valores:

* Cara.
* Cruz.

---

## RF-03

El sistema deberá incorporar un plugin denominado **DicePlugin**.

---

## RF-04

DicePlugin devolverá un número entero comprendido entre **1 y 6**, ambos inclusive.

---

## RF-05

El sistema deberá incorporar un plugin denominado **RandomNumberPlugin**.

---

## RF-06

RandomNumberPlugin devolverá un número entero comprendido entre **1 y 99**, ambos inclusive.

---

## RF-07

Los tres plugins utilizarán el generador pseudoaleatorio estándar del lenguaje.

---

## RF-08

Los tres plugins participarán en el algoritmo estándar de selección mediante RapidFuzz.

---

## RF-09

Los tres plugins registrarán automáticamente sus capacidades durante el arranque del Orchestrator.

---

## RF-10

Los tres plugins devolverán un `PluginResult` compatible con el resto del ecosistema.

---

## RF-11

Las respuestas deberán cumplir el Tone Guide.

---

# Requisitos no funcionales

## RNF-01

Tiempo máximo de ejecución:

**< 5 ms**

---

## RNF-02

Los plugins no realizarán llamadas HTTP.

---

## RNF-03

No dependerán de servicios externos.

---

## RNF-04

No mantendrán estado interno.

---

## RNF-05

No almacenarán información persistente.

---

## RNF-06

Cada ejecución será independiente de las anteriores.

---

## RNF-07

El generador aleatorio deberá distribuir uniformemente los resultados posibles.

---

## RNF-08

Los plugins deberán registrar cualquier excepción inesperada mediante el sistema estándar de logging.

---

# Capacidades registradas

| Plugin             | id              | Descripción                             |
| ------------------ | --------------- | --------------------------------------- |
| CoinPlugin         | `coin`          | Lanza una moneda y devuelve cara o cruz |
| DicePlugin         | `dice`          | Lanza un dado de seis caras             |
| RandomNumberPlugin | `random-number` | Genera un número aleatorio entre 1 y 99 |

---

# Criterios de aceptación

* El Orchestrator descubre automáticamente los tres plugins.
* Los tres aparecen registrados en `system-service`.
* CoinPlugin devuelve exclusivamente **Cara.** o **Cruz.**
* DicePlugin devuelve exclusivamente valores entre **1 y 6**.
* RandomNumberPlugin devuelve exclusivamente valores entre **1 y 99**.
* Las respuestas cumplen el Tone Guide.
* Los tres plugins son seleccionados correctamente mediante el motor de similitud semántica.
* No existen dependencias externas ni llamadas de red durante la ejecución.

### Recomendación de diseño

Dado que ya tienes varias capacidades que dependen de una funcionalidad común (y probablemente crecerán con "elige una opción", "baraja una carta", "sortea un nombre", etc.), empezaría a introducir un pequeño **RandomService** interno, igual que comentamos para fecha y hora. Sería una utilidad compartida (no un microservicio) con métodos como:

```python
flip_coin() -> str
roll_dice() -> int
random_int(min_value: int, max_value: int) -> int
```

Así los plugins quedan reducidos prácticamente a traducir la intención del usuario en una llamada al servicio y construir el `PluginResult`, manteniendo una arquitectura muy limpia y preparada para futuras capacidades aleatorias.
