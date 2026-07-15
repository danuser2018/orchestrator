# Especificación de Refactorización
# Consolidación del modelo ExecutionPlan y eliminación del endpoint legado

**Estado:** Propuesto

**Tipo:** Refactorización interna

**Impacto:** Orchestrator

---

# 1. Introducción

La refactorización introducida en ADR-014 separó el proceso de resolución de intención del proceso de ejecución mediante dos componentes independientes y un nuevo contrato interno (`ExecutionPlan`).

Durante una fase de transición se mantuvo el endpoint legado `POST /api/v1/execute` para garantizar la compatibilidad con los consumidores existentes.

Tras la migración de `Interaction Manager` al nuevo flujo basado en planificación, dicho endpoint ha dejado de tener consumidores.

Esta iteración completa definitivamente la transición iniciada en ADR-014 eliminando la capa de compatibilidad y alineando completamente la implementación con la arquitectura objetivo.

---

# 2. Objetivos

## Objetivos

- Eliminar el endpoint legado `/api/v1/execute`.
- Eliminar el código de compatibilidad asociado.
- Simplificar la API pública del Orchestrator.
- Consolidar el modelo basado en `ExecutionPlan`.
- Alinear la nomenclatura de los componentes con sus responsabilidades actuales.
- Reducir la deuda técnica generada durante la migración.

## Objetivos no incluidos

- No modificar el algoritmo de resolución.
- No modificar el contrato `ExecutionPlan`.
- No modificar los plugins existentes.
- No introducir nuevas capacidades funcionales.

---

# 3. Situación actual

Actualmente el Orchestrator expone tres endpoints.

```
POST /api/v1/resolve

POST /api/v1/execute-plan

POST /api/v1/execute
```

Los dos primeros constituyen la arquitectura objetivo.

El tercero únicamente existe por motivos de compatibilidad.

Asimismo, los componentes internos mantienen todavía una nomenclatura heredada de la arquitectura anterior.

```
IntentResolver

PluginExecutor
```

Aunque funcionalmente correctos, estos nombres ya no representan con precisión la responsabilidad real de cada componente.

---

# 4. Arquitectura objetivo

Una vez completada esta iteración, la arquitectura quedará formada por dos componentes claramente diferenciados.

```text
                 +-----------------------+
                 | Interaction Manager   |
                 +-----------+-----------+
                             |
                     POST /resolve
                             |
                             ▼
                 +-----------------------+
                 | ExecutionPlanner      |
                 +-----------+-----------+
                             |
                     ExecutionPlan
                             |
                     POST /execute-plan
                             |
                             ▼
                 +-----------------------+
                 | PlanExecutor          |
                 +-----------+-----------+
                             |
                             ▼
                         Plugins
                             |
                             ▼
                    AssistantResponse
```

El `ExecutionPlan` pasa a convertirse en el contrato interno central del Orchestrator.

---

# 5. Cambios funcionales

## Eliminación del endpoint legado

Se eliminará completamente:

```
POST /api/v1/execute
```

No deberá mantenerse ningún alias ni código de compatibilidad.

---

## Eliminación del flujo puente

Se eliminará toda la lógica equivalente a:

```
resolve()

↓

execute-plan()
```

El flujo quedará explícitamente dividido entre planificación y ejecución.

---

## Simplificación de la API

La API pública del Orchestrator quedará reducida a:

```
POST /api/v1/resolve

POST /api/v1/execute-plan
```

---

# 6. Cambios de nomenclatura

Como parte de esta iteración se actualizará la nomenclatura de los componentes internos para alinearla con el modelo arquitectónico.

## 6.1 IntentResolver → ExecutionPlanner

La clase:

```
IntentResolver
```

pasará a denominarse:

```
ExecutionPlanner
```

### Justificación

Actualmente el componente no se limita a resolver una intención.

Su responsabilidad consiste en construir un `ExecutionPlan`.

El nuevo nombre representa mejor dicha responsabilidad y permite incorporar en el futuro nuevas etapas de planificación como:

- resolución de parámetros;
- inferencia de canales;
- enriquecimiento mediante contexto;
- validaciones de seguridad;
- generación de planes con múltiples acciones.

---

## 6.2 PluginExecutor → PlanExecutor

La clase:

```
PluginExecutor
```

pasará a denominarse:

```
PlanExecutor
```

### Justificación

El componente no ejecuta directamente plugins.

Consume un `ExecutionPlan` y ejecuta secuencialmente cada uno de sus pasos.

El nuevo nombre refleja con precisión su responsabilidad y mantiene la simetría con `ExecutionPlanner`.

---

## 6.3 Actualización de referencias

Deberán actualizarse todas las referencias presentes en:

- código fuente;
- pruebas unitarias;
- pruebas de integración;
- documentación técnica;
- ADR-014;
- architecture.md;
- services.md;
- CHANGELOG;
- skills del repositorio `home-assistant`.

No deberán permanecer referencias a la nomenclatura anterior, salvo aquellas destinadas a documentar la evolución histórica del proyecto.

---

# 7. Compatibilidad

Esta refactorización rompe la compatibilidad con clientes que consuman el endpoint legado.

Se considera aceptable porque:

- `Interaction Manager` ya utiliza exclusivamente `/resolve` y `/execute-plan`.
- No existen consumidores adicionales identificados.
- La migración al nuevo modelo ha finalizado.

---

# 8. Requisitos funcionales

## RF-001

Eliminar completamente el endpoint:

```
POST /api/v1/execute
```

---

## RF-002

La API pública deberá exponer únicamente:

```
POST /api/v1/resolve

POST /api/v1/execute-plan
```

---

## RF-003

Renombrar la clase:

```
IntentResolver
```

por:

```
ExecutionPlanner
```

---

## RF-004

Renombrar la clase:

```
PluginExecutor
```

por:

```
PlanExecutor
```

---

## RF-005

Actualizar todas las referencias internas y documentación.

---

## RF-006

Eliminar cualquier código de compatibilidad asociado al endpoint legado.

---

## RF-007

Mantener exactamente el mismo comportamiento funcional del sistema.

---

# 9. Requisitos no funcionales

## RNF-001

La refactorización no deberá modificar el comportamiento observable por el usuario.

---

## RNF-002

No deberá permanecer código muerto asociado al endpoint eliminado.

---

## RNF-003

La cobertura de pruebas deberá mantenerse.

---

## RNF-004

La documentación deberá quedar completamente alineada con la nueva arquitectura.

---

## RNF-005

La nomenclatura del código deberá reflejar fielmente las responsabilidades de cada componente.

---

## RNF-006

El `ExecutionPlan` continuará siendo el único contrato compartido entre planificación y ejecución.

---

# 10. Plan de implementación

## Paso 1

Eliminar el endpoint:

```
POST /api/v1/execute
```

---

## Paso 2

Eliminar el código de compatibilidad asociado.

---

## Paso 3

Renombrar:

```
IntentResolver
```

↓

```
ExecutionPlanner
```

---

## Paso 4

Renombrar:

```
PluginExecutor
```

↓

```
PlanExecutor
```

---

## Paso 5

Actualizar todas las referencias en:

- código;
- pruebas;
- documentación;
- skills;
- ADR-014;
- CHANGELOG.

---

## Paso 6

Eliminar las pruebas específicas del endpoint legado.

---

## Paso 7

Ejecutar la batería completa de pruebas unitarias e integración.

---

# 11. Documentación afectada

Deberán actualizarse los siguientes documentos:

- `docs/architecture.md`
- `docs/services.md`
- `docs/adr/adr-014-refactorizacion-orquestador.md`
- `CHANGELOG.md` (orchestrator)
- `CHANGELOG.md` (home-assistant)
- Skills:
  - `api-contracts`
  - `service-responsibilities`

---

# 12. Criterios de aceptación

La iteración se considerará completada cuando:

- El endpoint `POST /api/v1/execute` haya sido eliminado.
- La API exponga únicamente `/resolve` y `/execute-plan`.
- La clase `IntentResolver` haya sido renombrada a `ExecutionPlanner`.
- La clase `PluginExecutor` haya sido renombrada a `PlanExecutor`.
- No existan referencias a la nomenclatura anterior en el código ni en la documentación.
- No permanezca código de compatibilidad.
- Toda la batería de pruebas pase correctamente.
- El comportamiento funcional permanezca inalterado.

---

# 13. Resultado esperado

Con esta refactorización se completa definitivamente la transición iniciada en ADR-014.

El Orchestrator adopta de forma definitiva un modelo basado en planificación y ejecución, en el que el `ExecutionPlan` constituye el contrato central de la plataforma.

La arquitectura resultante queda definida por los siguientes componentes:

```text
Texto
   │
   ▼
ExecutionPlanner
   │
   ▼
ExecutionPlan
   │
   ▼
PlanExecutor
   │
   ▼
AssistantResponse
```

A partir de este punto, el pipeline queda preparado para incorporar nuevas fases de planificación (Parameter Resolver, Channel Resolver, Security Manager, Context Service o transformadores del `ExecutionPlan`) sin necesidad de realizar nuevas refactorizaciones estructurales.

Esta iteración representa el cierre de la transición desde el modelo monolítico original hacia una arquitectura basada en un contrato explícito de planificación y ejecución, simplificando el código, reduciendo la deuda técnica y estableciendo una base sólida para la evolución futura de NOVA-2.