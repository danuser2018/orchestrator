# ADR 0004: Motor de Selección de Plugins por Similitud Semántica Determinista

* **Fecha**: 2026-07-03
* **Estado**: Aceptado

## Contexto

El motor de selección de plugins heredado en el servicio `orchestrator` utilizaba palabras clave (*keywords*) y expresiones regulares (*regex*) con pesos estáticos. Aunque este enfoque es ágil y determinista, presentaba dos problemas principales:
1. Alta sensibilidad a variaciones tipográficas, errores gramaticales y fallos menores en la transcripción del Speech-to-Text (STT).
2. Dificultad para el desarrollador de plugins, quien debía prever exhaustivamente expresiones regulares complejas o listas de keywords propensas a colisiones.

Se busca una alternativa que mantenga la velocidad de respuesta local (<50 ms), no requiera infraestructura de GPU y ofrezca mayor tolerancia al lenguaje natural informal del usuario.

## Decisión

Adoptar un motor de comparación textual basado en similitud matemática determinista utilizando la librería `rapidfuzz`. 

El diseño se define por las siguientes reglas:
1. **Puntuación Ponderada:** Se combinan cuatro algoritmos de comparación de `rapidfuzz` aplicando pesos configurables (que deben sumar exactamente `1.0`):
   - `ratio` (peso por defecto: 0.20)
   - `partial_ratio` (peso por defecto: 0.30)
   - `token_sort_ratio` (peso por defecto: 0.20)
   - `token_set_ratio` (peso por defecto: 0.30)
2. **Evaluación frente a ejemplos:** Cada plugin funcional define un conjunto de frases de ejemplo (`examples`). El score de un plugin corresponde al valor máximo obtenido al comparar la petición normalizada del usuario con cada uno de sus ejemplos normalizados.
3. **Umbral de Similitud:** Se requiere superar un umbral mínimo configurable (`similarity_threshold`, por defecto `60.0`) para considerar válida la selección del plugin.
4. **Desempate por Prioridad:** Si la diferencia de puntuación entre los dos candidatos con mejores puntuaciones es menor que un umbral (`tie_breaker_threshold`, por defecto `5.0`), el empate o ambigüedad se resolverá a favor del plugin con mayor `priority`.
5. **Derivación a Fallback:** Si ningún plugin supera el umbral de similitud o si persiste un empate (mismo score y misma prioridad entre los principales candidatos), se deriva al `FallbackPlugin`.

## Consecuencias

* **Positivas**:
  - Mayor tolerancia ante errores de transcripción del STT y variaciones naturales en el habla del usuario.
  - Mayor facilidad para añadir nuevos plugins (solo requiere declarar frases de ejemplo naturales).
  - Mantiene el procesamiento en CPU local con latencias inferiores a 10 ms.
  - Absolutamente determinista y verificable mediante pruebas unitarias.
* **Negativas**:
  - Requiere afinar los pesos y los umbrales para evitar falsos positivos o resoluciones incorrectas en ambientes con muchos plugins.
