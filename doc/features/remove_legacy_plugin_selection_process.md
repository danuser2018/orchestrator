# Especificación Funcional

## Fase 3 - Eliminación del mecanismo legado de selección de plugins

**Proyecto:** Nova

**Estado:** Propuesta

---

# 1. Objetivo

Eliminar completamente el mecanismo legado de selección de plugins basado en `keywords` y expresiones regulares, consolidando el nuevo modelo de selección basado en frases de ejemplo.

Al finalizar esta fase, el sistema utilizará exclusivamente el motor de matching introducido en la Fase 2.

---

# 2. Motivación

Tras la implantación del nuevo motor de selección, el sistema mantiene dos mecanismos de selección:

* mecanismo legado (keywords y regex);
* mecanismo basado en similitud.

Mantener ambos mecanismos incrementa la complejidad del sistema, dificulta el mantenimiento y puede provocar inconsistencias.

Esta fase elimina dicha deuda técnica.

---

# 3. Objetivos

* Eliminar completamente el sistema basado en `keywords`.
* Eliminar las expresiones regulares utilizadas para seleccionar plugins.
* Simplificar el contrato público de los plugins.
* Eliminar código legado del Orchestrator.
* Consolidar el nuevo modelo de matching como único mecanismo oficial de selección.

---

# 4. Requisitos funcionales

## RF-1. Eliminación de keywords

Todos los plugins deberán eliminar la propiedad `keywords`.

Ningún componente del sistema podrá depender de dicha información.

---

## RF-2. Eliminación de expresiones regulares de selección

Todas las expresiones regulares utilizadas exclusivamente para determinar el plugin deberán eliminarse.

Las expresiones regulares destinadas a la extracción o validación de parámetros podrán mantenerse cuando resulten necesarias para la lógica del propio plugin.

---

## RF-3. Simplificación del contrato de los plugins

El contrato conceptual de un plugin quedará reducido a:

* identificador;
* prioridad;
* frases de ejemplo;
* lógica de ejecución.

No deberán existir mecanismos alternativos para describir cómo localizar un plugin.

---

## RF-4. Actualización del Orchestrator

El Orchestrator utilizará exclusivamente el `PluginMatcher` para determinar el plugin a ejecutar.

No deberá conservar lógica relacionada con `keywords` o expresiones regulares de selección.

---

## RF-5. Compatibilidad funcional

El comportamiento observable de Nova deberá mantenerse.

La eliminación del mecanismo legado no deberá modificar las capacidades disponibles ni la experiencia de usuario.

---

## RF-6. Plugin Fallback

El plugin Fallback continuará existiendo como mecanismo de resolución cuando el `PluginMatcher` devuelva `NoMatch`.

No participará en el cálculo de similitud.

---

## RF-7. Actualización de la documentación

Toda la documentación para el desarrollo de nuevos plugins deberá reflejar exclusivamente el nuevo contrato basado en:

* prioridad;
* frases de ejemplo.

No deberán existir referencias al uso de `keywords` o expresiones regulares para la selección.

---

## RF-8. Actualización de pruebas

Los tests deberán adaptarse para validar exclusivamente el nuevo mecanismo de selección.

No deberán existir pruebas asociadas al sistema legado.

---

# 5. Requisitos no funcionales

## RNF-1. Reducción de complejidad

La eliminación del mecanismo legado deberá reducir la complejidad del código y evitar la coexistencia de múltiples estrategias de selección.

---

## RNF-2. Mantenibilidad

El desarrollo de nuevos plugins deberá requerir únicamente la definición de:

* prioridad;
* frases de ejemplo;
* implementación de la acción.

---

## RNF-3. Coherencia arquitectónica

Todos los plugins deberán utilizar el mismo mecanismo de publicación de capacidades.

No deberán existir excepciones al modelo.

---

## RNF-4. Responsabilidad única

La responsabilidad de localizar un plugin corresponderá exclusivamente al `PluginMatcher`.

Los plugins únicamente describirán cómo un usuario invoca su capacidad.

---

## RNF-5. Extensibilidad

La eliminación del sistema legado no deberá dificultar la futura sustitución del `SimilarityEngine` por otras implementaciones.

---

## RNF-6. Legibilidad

La API pública de los plugins deberá ser más sencilla y fácil de comprender que la versión anterior.

---

## RNF-7. Ausencia de código muerto

No deberán permanecer clases, métodos, configuraciones o dependencias relacionadas con el mecanismo legado de selección.

---

# 6. Contrato conceptual resultante

Al finalizar esta fase, el contrato conceptual de un plugin será:

Plugin

* id
* priority
* examples
* execute(...)

Todos los plugins deberán ajustarse a este contrato.

---

# 7. Criterios de aceptación

La fase se considerará completada cuando se cumplan las siguientes condiciones:

* Ningún plugin declare `keywords`.
* Ningún plugin utilice expresiones regulares para su selección.
* El Orchestrator utilice exclusivamente el `PluginMatcher`.
* Todas las pruebas automáticas sean satisfactorias.
* Toda la documentación refleje el nuevo modelo.
* No exista código legado relacionado con el mecanismo anterior.

---

# 8. Beneficios esperados

La finalización de esta fase proporcionará:

* una arquitectura más simple y coherente;
* una única estrategia de selección de plugins;
* una API más limpia para el desarrollo de nuevas capacidades;
* una reducción de la deuda técnica;
* una mejor preparación para futuras evoluciones del motor de similitud sin necesidad de modificar los plugins.
