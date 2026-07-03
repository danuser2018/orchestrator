# Especificación Funcional

## Fase 1 - Incorporación de frases de ejemplo y prioridad en los plugins

**Proyecto:** Nova

**Estado:** Propuesta

---

# 1. Objetivo

Modificar el contrato público de los plugins para sustituir progresivamente el modelo basado en *keywords* y expresiones regulares por un modelo declarativo basado en frases de ejemplo.

Durante esta fase **no se modificará el comportamiento del Orchestrator**.

Los nuevos atributos coexistirán con el mecanismo actual y prepararán el sistema para la futura implantación del nuevo motor de matching.

---

# 2. Motivación

El mecanismo actual de selección presenta varias limitaciones:

* Dependencia de coincidencias mediante palabras clave.
* Uso de expresiones regulares para determinar el plugin.
* Escasa tolerancia a errores de transcripción del STT.
* Dificultad para evolucionar hacia algoritmos de similitud o búsqueda semántica.

El nuevo modelo pretende desacoplar completamente la definición de un plugin del algoritmo utilizado para localizarlo.

---

# 3. Objetivos de la fase

* Incorporar frases de ejemplo a todos los plugins.
* Incorporar prioridad a todos los plugins.
* Mantener compatibilidad con el motor actual.
* No modificar el comportamiento funcional de Nova.

---

# 4. Requisitos funcionales

## RF-1. Frases de ejemplo

Cada plugin deberá publicar una colección de frases representativas que describan cómo un usuario invocaría dicha capacidad.

Las frases representan ejemplos de uso y no reglas de procesamiento.

---

## RF-2. Única acción

Cada plugin representa una única acción funcional.

Las frases de ejemplo deberán corresponder exclusivamente a dicha acción.

---

## RF-3. Diversidad

Las frases deberán representar distintas formas naturales de expresar la intención.

No deberán consistir únicamente en pequeñas variaciones de la misma frase.

---

## RF-4. Independencia

Las frases de ejemplo no contendrán información específica del algoritmo de matching.

Deberán ser válidas independientemente de que el sistema utilice:

* RapidFuzz
* Embeddings
* Búsqueda vectorial
* Algoritmos híbridos

---

## RF-5. Prioridad

Cada plugin declarará una prioridad.

Durante esta fase la prioridad no modificará el comportamiento del sistema.

Será utilizada en futuras versiones para resolver empates entre plugins con puntuaciones similares.

---

## RF-6. Compatibilidad

Los atributos actuales (`keywords` y `regex`) permanecerán operativos durante esta fase.

---

# 5. Requisitos no funcionales

## RNF-1. Compatibilidad

No deberá romperse ningún plugin existente.

---

## RNF-2. Evolución

La incorporación de frases de ejemplo deberá permitir eliminar completamente el sistema de keywords en fases posteriores.

---

## RNF-3. Independencia del algoritmo

Los plugins no deberán conocer el algoritmo utilizado para calcular similitudes.

---

## RNF-4. Legibilidad

Las frases deberán ser comprensibles para un desarrollador sin necesidad de conocer el funcionamiento interno del motor de matching.

---

## RNF-5. Mantenibilidad

La incorporación de nuevas frases no deberá requerir modificaciones en el Orchestrator.

---

# 6. Nuevo contrato conceptual

Cada plugin deberá declarar:

* Identificador
* Prioridad
* Frases de ejemplo

Conceptualmente:

Plugin

* id
* priority
* examples

---

# 7. Niveles de prioridad

Se definen los siguientes niveles de prioridad para futuras versiones.

| Nivel    | Valor |
| -------- | ----: |
| Muy alta |   100 |
| Alta     |    80 |
| Media    |    60 |
| Baja     |    40 |
| Fallback |     0 |

La prioridad únicamente se utilizará para resolver empates cuando dos plugins obtengan puntuaciones equivalentes.

Nunca sustituirá al cálculo de similitud.

---

# 8. Prioridad propuesta

| Plugin       | Prioridad |
| ------------ | --------: |
| Saludo       |       100 |
| Despedida    |       100 |
| Tiempo       |        80 |
| Identidad    |        60 |
| Capabilities |        60 |
| Fallback     |         0 |

El plugin **Fallback** continuará existiendo como un plugin convencional durante esta fase.

No dispondrá de frases de ejemplo y será tratado como un caso especial por el motor de selección en la siguiente fase.

---

# 9. Frases de ejemplo

## Plugin Saludo

* Hola.
* Buenos días.
* Buenas tardes.
* Buenas noches.
* Hola, Nova.
* Buenos días, Nova.
* ¿Hay alguien?
* ¿Estás ahí?
* ¿Me escuchas?
* Hola, ¿qué tal?

---

## Plugin Despedida

* Adiós.
* Hasta luego.
* Hasta pronto.
* Nos vemos.
* Chao.
* Me voy.
* Eso es todo.
* Ya hemos terminado.
* Gracias, hasta luego.
* Puedes irte.

---

## Plugin Tiempo

* ¿Qué tiempo hace?
* ¿Qué tiempo hará mañana?
* ¿Va a llover hoy?
* ¿Qué temperatura hay?
* ¿Cómo está el tiempo?
* Dime el pronóstico del tiempo.
* ¿Va a hacer calor hoy?
* ¿Necesito paraguas?
* ¿Qué clima hace?
* ¿Cómo estará el tiempo esta tarde?

---

## Plugin Identidad

* ¿Quién eres?
* ¿Cómo te llamas?
* ¿Qué eres?
* Cuéntame quién eres.
* Preséntate.
* Háblame de ti.
* ¿Eres una inteligencia artificial?
* ¿Para qué sirves?
* ¿Cuál es tu función?
* Dime quién eres.

---

## Plugin Capabilities

* ¿Qué puedes hacer?
* ¿En qué me puedes ayudar?
* ¿Qué funciones tienes?
* ¿Qué sabes hacer?
* Muéstrame tus capacidades.
* ¿Qué comandos conoces?
* ¿Qué cosas puedo pedirte?
* ¿Cómo puedo usarte?
* ¿Qué opciones tengo?
* Enséñame lo que puedes hacer.

---

## Plugin Fallback

No dispone de frases de ejemplo.

Su ejecución se producirá cuando el motor de selección no encuentre ningún plugin cuya puntuación supere el umbral mínimo de aceptación.

Durante esta fase continuará existiendo como un plugin convencional para mantener la compatibilidad con el diseño actual.

---

# 10. Consideraciones de diseño

* Las frases de ejemplo constituyen la descripción funcional del plugin.
* Los plugins dejan de describir cómo deben localizarse y pasan a describir cómo un usuario los invoca.
* El algoritmo de matching pasa a ser responsabilidad exclusiva del Orchestrator.
* La API pública de los plugins permanece desacoplada del algoritmo de selección.
* La incorporación de nuevas tecnologías de matching (RapidFuzz, embeddings, búsqueda vectorial o algoritmos híbridos) no requerirá modificar ningún plugin.

---

# 11. Evolución prevista

La siguiente fase del proyecto consistirá en sustituir el mecanismo de selección basado en `keywords` y expresiones regulares por un motor de matching basado en similitud.

Los plugins definidos en esta fase serán totalmente compatibles con dicha evolución y no requerirán modificaciones adicionales.
