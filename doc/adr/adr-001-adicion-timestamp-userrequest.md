# ADR 0001: Adición de campo timestamp opcional en UserRequest

* **Fecha**: 2026-06-29
* **Estado**: Aceptado

## Contexto

La especificación técnica del proyecto (`README.md`, Sección 9 - Modelo de datos) define que el modelo de datos `UserRequest` (la estructura recibida por el endpoint `POST /api/v1/execute`) debe contener los campos `text` (str) y `timestamp` (float). 

Sin embargo, en la implementación del código (`core/models.py`), el campo `timestamp` estaba ausente, lo que representaba una discrepancia entre el diseño documentado y el código.

## Decisión

Añadir el campo `timestamp` al modelo `UserRequest` utilizando la definición `timestamp: Optional[float] = None` de la librería `pydantic`.

Al definir este campo como opcional y asignarle un valor predeterminado de `None`, garantizamos que la API del Orchestrator mantenga una compatibilidad absoluta con clientes antiguos que no envíen el campo `timestamp` en sus peticiones JSON.

## Consecuencias

* **Positivas**:
  - Se resuelve la discrepancia técnica existente con la documentación (`README.md`).
  - Habilita la capacidad futura de calcular y registrar la latencia extremo a extremo (*end-to-end*) comparando el tiempo del sistema del cliente con el de procesamiento del Orchestrator.
* **Neutras**:
  - No requiere cambios en la infraestructura de pruebas ni en los llamadores del servicio actuales debido a que el campo es opcional.
