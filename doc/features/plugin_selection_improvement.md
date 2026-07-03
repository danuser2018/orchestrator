# Especificación Funcional

## Fase 2 - Nuevo motor de selección de plugins basado en similitud

**Proyecto:** Nova

**Estado:** Propuesta

---

# 1. Objetivo

Sustituir el mecanismo actual de selección de plugins basado en `keywords` y expresiones regulares por un motor de matching basado en similitud textual.

El nuevo motor utilizará las frases de ejemplo publicadas por los plugins para determinar la capacidad que mejor representa la intención del usuario.

La implementación inicial utilizará RapidFuzz como motor de cálculo de similitud, manteniendo una arquitectura desacoplada que permita sustituir el algoritmo en futuras versiones.

---

# 2. Motivación

El sistema actual presenta las siguientes limitaciones:

* Dependencia de coincidencias exactas.
* Baja tolerancia a errores de transcripción del STT.
* Baja tolerancia a variaciones lingüísticas.
* Acoplamiento entre los plugins y el algoritmo de selección.

El nuevo diseño persigue:

* mejorar la robustez del reconocimiento de intenciones;
* simplificar el desarrollo de plugins;
* preparar Nova para futuras implementaciones mediante embeddings o búsqueda vectorial.

---

# 3. Objetivos

* Eliminar la selección mediante keywords.
* Eliminar las expresiones regulares utilizadas para seleccionar plugins.
* Seleccionar plugins mediante similitud con frases de ejemplo.
* Resolver empates mediante prioridad.
* Mantener el plugin Fallback como mecanismo de última instancia.

---

# 4. Arquitectura

El proceso de selección estará compuesto por los siguientes elementos:

## Plugin Matcher

Responsable de:

* obtener todos los plugins registrados;
* recuperar las frases de ejemplo;
* solicitar el cálculo de similitud;
* calcular el score de cada plugin;
* generar un ranking;
* aplicar el umbral mínimo;
* resolver empates;
* devolver el plugin seleccionado.

---

## Similarity Engine

Responsable de calcular la similitud entre:

* texto recibido
* frase de ejemplo

Interfaz conceptual:

score(texto_usuario, frase_ejemplo) → [0..100]

La primera implementación utilizará RapidFuzz.

El Plugin Matcher no conocerá el algoritmo utilizado.

---

# 4.1 Arquitectura interna del motor de selección

Con el fin de desacoplar el algoritmo de cálculo de similitud del proceso de selección de plugins, el nuevo motor estará compuesto por los siguientes componentes.

## Plugin Matcher

Responsable de coordinar el proceso completo de selección.

Sus responsabilidades serán:

* obtener los plugins registrados;
* recuperar las frases de ejemplo de cada plugin;
* solicitar el cálculo de similitud al Similarity Engine;
* calcular el score de cada plugin;
* construir el ranking de resultados;
* aplicar el umbral mínimo;
* resolver empates mediante prioridad;
* devolver el resultado final al Orchestrator.

El Plugin Matcher no conocerá el algoritmo utilizado para calcular la similitud.

---

## Similarity Engine

Componente responsable de calcular el grado de similitud entre un texto de entrada y una frase de ejemplo.

Su interfaz conceptual será:

```
score(texto_usuario, frase_ejemplo) → [0..100]
```

El resultado será un valor numérico comprendido entre 0 y 100, donde:

* 0 representa ausencia de similitud.
* 100 representa coincidencia máxima.

El Plugin Matcher dependerá exclusivamente de esta interfaz.

---

## RapidFuzzSimilarityEngine

La primera implementación del Similarity Engine utilizará la librería RapidFuzz.

Internamente combinará distintos algoritmos de similitud para obtener una puntuación única.

La estrategia de combinación y los pesos utilizados serán configurables y no formarán parte del contrato público de la interfaz.

---

## Futuras implementaciones

La arquitectura deberá permitir incorporar nuevas implementaciones del Similarity Engine sin modificar el Plugin Matcher ni los plugins.

Ejemplos:

* RapidFuzzSimilarityEngine
* EmbeddingSimilarityEngine
* HybridSimilarityEngine
* AISimilarityEngine

Todas las implementaciones deberán respetar exactamente la misma interfaz pública.

---

## Relaciones entre componentes

```
                Orchestrator
                      │
                      ▼
              Plugin Matcher
                      │
      ┌───────────────┴───────────────┐
      │                               │
      ▼                               ▼
Plugin Registry              Similarity Engine
      │                               ▲
      ▼                               │
 Plugins                    RapidFuzzSimilarityEngine
                                     │
                          (implementaciones futuras)
```

---

## Beneficios arquitectónicos

Esta separación proporciona las siguientes ventajas:

* desacoplamiento entre plugins y algoritmo de selección;
* posibilidad de sustituir RapidFuzz sin modificar el resto del sistema;
* facilidad para realizar pruebas comparativas entre distintos motores de similitud;
* simplificación del mantenimiento;
* preparación para futuras implementaciones basadas en embeddings o búsqueda vectorial;
* cumplimiento del principio de responsabilidad única, separando la coordinación del proceso (Plugin Matcher) del cálculo de similitud (Similarity Engine).


---

# 5. Requisitos funcionales

## RF-1. Obtención de plugins

El Plugin Matcher deberá recuperar todos los plugins registrados, excepto el plugin Fallback.

---

## RF-2. Comparación

Cada frase de ejemplo deberá compararse con el texto recibido.

---

## RF-3. Cálculo de similitud

La implementación inicial utilizará RapidFuzz.

Para cada frase deberán calcularse los siguientes índices:

* ratio
* partial_ratio
* token_sort_ratio
* token_set_ratio

---

## RF-4. Score de la frase

El Similarity Engine combinará los distintos índices de RapidFuzz para obtener un único score comprendido entre 0 y 100.

La función de combinación y sus pesos serán configurables para permitir ajustes posteriores sin modificar la arquitectura.

---

## RF-5. Score del plugin

El score de un plugin será el mayor score obtenido entre todas sus frases de ejemplo.

Asimismo deberá almacenarse la frase responsable del mejor resultado.

---

## RF-6. Ranking

El Plugin Matcher generará un ranking ordenado de mayor a menor score.

Cada entrada contendrá:

* plugin
* score
* prioridad
* frase de ejemplo ganadora

---

## RF-7. Umbral mínimo

Deberá existir un umbral configurable.

Si ningún plugin supera dicho umbral, el Plugin Matcher devolverá `NoMatch`.

---

## RF-8. Desempate

Si dos plugins obtienen puntuaciones cuya diferencia sea inferior al umbral de desempate:

1. comparar prioridad;
2. seleccionar el plugin con mayor prioridad;
3. si persiste el empate, devolver `NoMatch`.

La prioridad nunca sustituirá al score de similitud.

Únicamente resolverá situaciones ambiguas.

---

## RF-9. Fallback

Si el resultado del Plugin Matcher es `NoMatch`, el Orchestrator ejecutará el plugin Fallback.

El plugin Fallback no participará en el proceso de comparación.

---

## RF-10. Registro

El motor deberá registrar, al menos en modo diagnóstico:

* texto recibido;
* ranking obtenido;
* plugin seleccionado;
* score;
* prioridad aplicada (si procede);
* frase de ejemplo responsable de la selección.

---

# 6. Algoritmo

## Paso 1

Obtener el texto recibido.

---

## Paso 2

Recuperar todos los plugins registrados excepto Fallback.

---

## Paso 3

Para cada plugin.

Para cada frase de ejemplo.

Calcular el score mediante el Similarity Engine.

---

## Paso 4

Conservar únicamente la mejor puntuación obtenida por dicho plugin.

Guardar también la frase responsable.

---

## Paso 5

Ordenar los plugins por score descendente.

---

## Paso 6

Si el mejor score es inferior al umbral configurado:

Resultado = NoMatch.

---

## Paso 7

Si el segundo plugin posee una puntuación suficientemente próxima al primero (según el umbral de desempate):

Comparar prioridades.

Seleccionar el plugin con mayor prioridad.

Si continúan empatados:

Resultado = NoMatch.

---

## Paso 8

El Orchestrator ejecutará:

* plugin ganador, o
* plugin Fallback.

---

# 7. Complejidad

Si:

P = número de plugins

E = número de frases de ejemplo por plugin

El número de comparaciones será:

P × E

Ejemplo:

100 plugins

15 frases

Resultado:

1.500 comparaciones.

RapidFuzz permite ejecutar este volumen de comparaciones en CPU con una latencia de pocos milisegundos.

---

# 8. Requisitos no funcionales

## RNF-1. Independencia del canal

El motor deberá funcionar de igual forma para cualquier canal de entrada:

* Voz
* Telegram
* API
* Web
* Futuros canales

---

## RNF-2. Independencia del algoritmo

El Plugin Matcher no dependerá de RapidFuzz.

Toda la lógica de similitud estará encapsulada en el Similarity Engine.

---

## RNF-3. Baja latencia

La selección deberá completarse en pocos milisegundos incluso con cientos de plugins registrados.

---

## RNF-4. Escalabilidad

La incorporación de nuevos plugins únicamente incrementará el número de frases comparadas.

No requerirá modificaciones en el algoritmo.

---

## RNF-5. Extensibilidad

El Similarity Engine deberá poder sustituirse por:

* Embeddings
* Búsqueda vectorial
* Algoritmos híbridos
* Clasificadores de IA

Sin modificar los plugins ni el Plugin Matcher.

---

## RNF-6. Compatibilidad

La sustitución del motor no modificará la interfaz pública de los plugins.

---

## RNF-7. Observabilidad

El sistema deberá proporcionar información suficiente para analizar decisiones de matching y ajustar umbrales o pesos del algoritmo.

---

# 9. Evolución futura

Se prevé la incorporación de nuevas implementaciones del Similarity Engine sin modificar el contrato de los plugins.

La arquitectura permitirá evolucionar desde RapidFuzz hacia motores basados en similitud semántica manteniendo intacta la API pública del ecosistema de plugins.

# Anexo A. Implementación de referencia mediante RapidFuzz

## A.1 Objetivo

Este anexo describe una posible implementación del `SimilarityEngine` utilizando la librería RapidFuzz.

Su contenido es meramente informativo y no forma parte del contrato funcional del sistema.

El objetivo es proporcionar una implementación de referencia que pueda sustituirse en el futuro sin modificar el resto de la arquitectura.

---

# A.2 Funcionamiento general

El `RapidFuzzSimilarityEngine` recibe:

* el texto introducido por el usuario;
* una frase de ejemplo publicada por un plugin.

Como resultado devuelve un valor comprendido entre **0 y 100**, donde:

* **0** representa ausencia de similitud.
* **100** representa una coincidencia prácticamente exacta.

Este cálculo se realiza utilizando varios algoritmos de RapidFuzz, cada uno especializado en un tipo diferente de comparación.

---

# A.3 Algoritmos utilizados

La implementación de referencia utilizará los siguientes algoritmos.

## ratio

Calcula la similitud global entre ambas cadenas.

Adecuado para frases muy parecidas.

Ejemplo:

Texto usuario:

> ¿Qué tiempo hace?

Frase ejemplo:

> ¿Qué tiempo hace?

Resultado esperado:

100

---

## partial_ratio

Busca la mejor coincidencia parcial.

Resulta especialmente útil cuando el usuario añade información adicional.

Ejemplo:

Usuario:

> Hola Nova, ¿qué tiempo hace hoy?

Ejemplo:

> ¿Qué tiempo hace?

Este algoritmo seguirá proporcionando una puntuación elevada.

---

## token_sort_ratio

Ordena previamente las palabras antes de compararlas.

Permite detectar frases con las mismas palabras en distinto orden.

Ejemplo:

Usuario:

> Hace qué tiempo

Ejemplo:

> Qué tiempo hace

---

## token_set_ratio

Compara los conjuntos de palabras ignorando repeticiones.

Es especialmente útil cuando aparecen palabras adicionales o irrelevantes.

Ejemplo:

Usuario:

> Hola Nova, por favor dime qué tiempo hace hoy

Ejemplo:

> Qué tiempo hace

---

# A.4 Cálculo del score

Cada algoritmo produce un valor entre 0 y 100.

La implementación combinará dichos valores mediante una función configurable.

Una posible implementación inicial podría ser:

Score =
0,20 × ratio +
0,30 × partial_ratio +
0,20 × token_sort_ratio +
0,30 × token_set_ratio

Los pesos anteriores constituyen únicamente un ejemplo.

La implementación podrá modificarlos tras realizar pruebas de rendimiento y precisión.

---

# A.5 Cálculo del score de un plugin

Para cada plugin:

1. recorrer todas las frases de ejemplo;
2. calcular el score de cada frase;
3. conservar únicamente la mayor puntuación obtenida.

Ejemplo:

Plugin Tiempo

| Frase de ejemplo      | Score |
| --------------------- | ----: |
| ¿Qué tiempo hace?     |    97 |
| ¿Va a llover?         |    61 |
| ¿Qué temperatura hay? |    48 |

Resultado del plugin:

Score = 97

Frase seleccionada = "¿Qué tiempo hace?"

---

# A.6 Construcción del ranking

Una vez evaluados todos los plugins, el Plugin Matcher generará un ranking ordenado de mayor a menor puntuación.

Ejemplo:

| Plugin    | Score |
| --------- | ----: |
| Tiempo    |    97 |
| Música    |    34 |
| Identidad |    18 |

Este ranking será utilizado posteriormente por el Match Resolver para aplicar el umbral mínimo y resolver posibles empates.

---

# A.7 Complejidad

Si:

* P = número de plugins.
* E = número de frases de ejemplo por plugin.

El número de comparaciones será:

P × E

Ejemplo:

100 plugins

15 frases

Total:

1.500 comparaciones

RapidFuzz está optimizado para este tipo de operaciones y permite realizar este volumen de comparaciones con una latencia de pocos milisegundos en CPU, sin necesidad de aceleración mediante GPU.

---

# A.8 Evolución

La arquitectura propuesta permite sustituir completamente esta implementación sin modificar:

* los plugins;
* el Plugin Matcher;
* el Orchestrator.

Implementaciones futuras podrían utilizar:

* búsqueda mediante embeddings;
* búsqueda vectorial;
* algoritmos híbridos;
* modelos de clasificación basados en IA.

Todas ellas deberán respetar la interfaz definida por `SimilarityEngine`.

---

# A.9 Ventajas de esta implementación

La implementación basada en RapidFuzz proporciona las siguientes ventajas:

* ejecución completamente local;
* ausencia de dependencias con servicios externos;
* baja latencia;
* consumo reducido de memoria y CPU;
* tolerancia a pequeñas variaciones lingüísticas;
* mejora de la robustez frente a errores habituales del reconocimiento de voz (STT);
* facilidad para evolucionar hacia motores de similitud más avanzados manteniendo intacta la arquitectura del sistema.
