# GreetingPlugin - Especificación Técnica

## 1. Objetivo

Implementar un plugin de saludo (`GreetingPlugin`) para el Orchestrator.

El objetivo de este plugin es detectar saludos del usuario y responder con una frase amigable y natural, variando las respuestas y adaptándose a la hora del día.

Este plugin servirá como primera implementación real del ecosistema de plugins y como referencia para futuros desarrollos.

---

## 2. Alcance

### Incluido

* Detección de saludos mediante keywords.
* Detección de saludos mediante expresiones regulares.
* Respuestas aleatorias.
* Adaptación automática según la hora local del sistema.
* Integración completa con el sistema de scoring del Orchestrator.
* Respuestas deterministas sin uso de LLM.

### No incluido

* Personalización por usuario.
* Gestión de contexto conversacional.
* Detección de despedidas.
* Persistencia de estado.
* Integración con servicios externos.

---

## 3. Casos de uso

### Caso 1 - Saludo simple

**Entrada**

```text
hola
```

**Salida esperada**

```text
Hola.
```

o

```text
Buenos días.
```

o

```text
Hola, dime.
```

---

### Caso 2 - Saludo formal

**Entrada**

```text
buenos días
```

**Salida esperada**

```text
Buenos días.
```

o

```text
Buenos días, te escucho.
```

---

### Caso 3 - Saludo informal

**Entrada**

```text
hey
```

**Salida esperada**

```text
Hola.
```

---

### Caso 4 - Saludo combinado con otra intención

**Entrada**

```text
hola, qué tiempo hace hoy
```

**Comportamiento esperado**

El plugin debe obtener puntuación positiva.

Sin embargo, NO debe bloquear al plugin del clima.

El Router será quien determine el ganador final según el scoring global.

---

## 4. Comportamiento funcional

### 4.1 Detección

El plugin debe detectar saludos mediante:

#### Keywords

```python
[
    "hola",
    "buenos dias",
    "buenas tardes",
    "buenas noches",
    "saludos",
    "hey",
    "ey",
    "buenas"
]
```

---

#### Regex

```python
[
    r"^hola$",
    r"^hola[.!?]?$",
    r"^buenos dias[.!?]?$",
    r"^buenas tardes[.!?]?$",
    r"^buenas noches[.!?]?$",
    r"^saludos[.!?]?$",
    r"^hey[.!?]?$",
    r"^ey[.!?]?$"
]
```

---

### 4.2 Selección de saludo según hora

El plugin debe obtener la hora local del sistema.

Reglas:

| Franja        | Saludo        |
| ------------- | ------------- |
| 06:00 - 11:59 | Buenos días   |
| 12:00 - 20:59 | Buenas tardes |
| 21:00 - 05:59 | Buenas noches |

---

### 4.3 Aleatoriedad

El plugin debe disponer de varias respuestas por franja horaria.

La respuesta se seleccionará aleatoriamente.

---

## 5. Catálogo inicial de respuestas

### Buenos días

```python
[
    "Buenos días.",
    "Buenos días, te escucho.",
    "Hola, buenos días.",
    "Buenos días. ¿Qué necesitas?",
    "Hola. ¿En qué puedo ayudarte?"
]
```

---

### Buenas tardes

```python
[
    "Buenas tardes.",
    "Buenas tardes, te escucho.",
    "Hola, buenas tardes.",
    "Buenas tardes. ¿Qué necesitas?",
    "Hola. ¿En qué puedo ayudarte?"
]
```

---

### Buenas noches

```python
[
    "Buenas noches.",
    "Buenas noches, te escucho.",
    "Hola, buenas noches.",
    "Buenas noches. ¿Qué necesitas?",
    "Hola. ¿En qué puedo ayudarte?"
]
```

---

## 6. Contrato del plugin

El plugin debe implementar la interfaz oficial definida por el Orchestrator.

### Nombre

```python
GreetingPlugin
```

---

### Descripción

```python
@property
def description(self) -> str:
    return "Responde a saludos del usuario."
```

---

### Keywords

Implementar la lista definida en la sección 4.

---

### Regex

Implementar la lista definida en la sección 4.

---

### Execute

Firma obligatoria:

```python
async def execute(
    self,
    context: PluginContext
) -> PluginResult:
```

---

## 7. Flujo de ejecución

### Entrada

```text
hola
```

### Router

```text
Keyword match:
hola
```

Score:

```text
+1
```

### Selección

```text
GreetingPlugin
```

### Ejecución

```text
Obtener hora local
↓
Seleccionar franja
↓
Elegir respuesta aleatoria
↓
Construir PluginResult
```

### Resultado

```python
PluginResult(
    success=True,
    speech="Buenos días, te escucho."
)
```

---

## 8. Pseudocódigo

```python
execute():

    current_hour = get_current_hour()

    if 6 <= current_hour < 12:
        responses = morning_responses

    elif 12 <= current_hour < 21:
        responses = afternoon_responses

    else:
        responses = evening_responses

    selected_response = random.choice(responses)

    return PluginResult(
        success=True,
        speech=selected_response
    )
```

---

## 9. Estructura de directorios

```text
plugins/
└── greeting/
    ├── main.py
    └── __init__.py
```

No requiere:

* config.py
* requirements.txt
* variables de entorno

---

## 10. Dependencias

Dependencias estándar de Python:

```python
datetime
random
```

No requiere librerías externas.

---

## 11. Logging

El plugin debe registrar:

### Inicio

```text
GreetingPlugin selected
```

### Franja detectada

```text
Detected greeting period: morning
```

### Respuesta elegida

```text
Selected response: Buenos días, te escucho.
```

Nivel recomendado:

```text
DEBUG
```

---

## 12. Gestión de errores

Dado que el plugin es completamente local, no se esperan errores operativos.

Ante una excepción inesperada:

```python
PluginResult(
    success=False,
    speech="Ha ocurrido un error al procesar el saludo."
)
```

---

## 13. Casos de prueba

### Caso 1

Entrada:

```text
hola
```

Resultado:

```text
success=True
```

---

### Caso 2

Entrada:

```text
buenos dias
```

Resultado:

```text
success=True
```

---

### Caso 3

Entrada:

```text
saludos
```

Resultado:

```text
success=True
```

---

### Caso 4

Entrada:

```text
hola que tiempo hace hoy
```

Resultado:

```text
GreetingPlugin obtiene score positivo.
WeatherPlugin debería ganar por score total.
```

---

### Caso 5

Entrada:

```text
texto sin saludo
```

Resultado:

```text
score=0
```

---

## 14. Criterios de aceptación

El plugin se considerará terminado cuando:

* Se cargue automáticamente mediante el Plugin Manager.
* Sea descubierto sin modificar el núcleo del Orchestrator.
* Detecte correctamente saludos comunes.
* Seleccione el saludo adecuado según la hora.
* Devuelva respuestas aleatorias.
* Devuelva siempre un PluginResult válido.
* No requiera configuración adicional.
* Funcione dentro del contenedor Docker actual.
* No introduzca dependencias externas.

---

## 15. Evoluciones futuras

Posibles mejoras para versiones posteriores:

### Personalización

```text
Hola David.
Buenos días David.
```

---

### Contexto conversacional

```text
Usuario: Hola
Asistente: Buenos días.

Usuario: ¿Qué tiempo hace?
```

---

### Detección de despedidas

Nuevo plugin:

```text
FarewellPlugin
```

Ejemplos:

```text
adiós
hasta luego
nos vemos
hasta mañana
```

---

### Saludos más naturales

Variaciones adicionales:

```text
Encantado de escucharte.
¿Qué puedo hacer por ti?
Dime.
Te escucho.
```

Manteniendo siempre el enfoque determinista y sin uso de LLM.
