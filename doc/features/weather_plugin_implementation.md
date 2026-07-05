# Adaptación del Weather Plugin para consumir Weather Service

## 1. Introducción

### 1.1 Objetivo

Modificar el `WeatherPlugin` para que obtenga la información meteorológica desde el `weather-service` en lugar de utilizar datos simulados.

Esta modificación permitirá ofrecer información meteorológica real al usuario sin alterar el contrato del plugin con el Orchestrator.

---

# 2. Alcance

## Incluido

- Consumo del endpoint del `weather-service`.
- Sustitución de los datos simulados.
- Gestión de errores de comunicación.
- Adaptación del mensaje generado por el plugin.

## No incluido

- Consulta por fecha.
- Consulta por ubicación.
- Enriquecimiento temporal.
- Cambios en el contrato del Orchestrator.
- Modificaciones del `weather-service`.

---

# 3. Requisitos funcionales

## RF-001 Consumo del Weather Service

El plugin deberá obtener la información meteorológica mediante una llamada HTTP al `weather-service`.

---

## RF-002 Uso del contrato REST

El plugin deberá consumir exclusivamente el endpoint público del servicio.

```
GET /v1/weather/current
```

No deberá depender de detalles internos de implementación.

---

## RF-003 Construcción de la respuesta

El plugin deberá construir una respuesta compatible con el Tone Guide de Nova-2 utilizando la información devuelta por el `weather-service`.

La respuesta deberá:

- Ser breve.
- Comunicar únicamente la información solicitada.
- Mantener un estilo consistente con el resto de plugins.

Como mínimo deberá incluir:

- Temperatura actual.
- Interpretación de la probabilidad de precipitación.

La probabilidad de precipitación devuelta por el `weather-service` deberá traducirse a un mensaje según la siguiente tabla:

| Probabilidad | Respuesta |
|--------------|-----------|
| 0 - 20 % | No parece que vaya a llover. |
| 21 - 40 % | Hay poca probabilidad de lluvia. |
| 41 - 60 % | Podría llover. |
| 61 - 80 % | Es probable que llueva. |
| 81 - 100 % | Es muy probable que llueva. |

Ejemplos:

> 27 grados. No parece que vaya a llover.

> 18 grados. Es probable que llueva.

---

## RF-004 Gestión de errores

Si el `weather-service` no estuviera disponible, el plugin deberá responder con un mensaje adecuado al usuario.

Ejemplo:

> En este momento no puedo consultar la información meteorológica.

---

## RF-005 Compatibilidad

La modificación no deberá alterar el contrato existente entre el plugin y el Orchestrator.

---

# 4. Requisitos no funcionales

## RNF-001 Desacoplamiento

El plugin únicamente conocerá el contrato REST del `weather-service`.

No deberá conocer el proveedor meteorológico utilizado.

---

## RNF-002 Configuración

La dirección del `weather-service` deberá obtenerse mediante configuración.

No deberá codificarse en el código fuente.

---

## RNF-003 Robustez

Los errores de comunicación deberán gestionarse sin provocar fallos en el flujo conversacional.

---

## RNF-004 Trazabilidad

Las llamadas realizadas al `weather-service` deberán registrarse mediante el sistema de logging de Nova.

---

# 5. Dependencias

Esta historia depende de:

- Weather Service implementado.
- Weather Service integrado en el ecosistema Nova.

---

# 6. Criterios de aceptación

La historia se considerará completada cuando:

- El plugin consulte correctamente el `weather-service`.
- La respuesta al usuario contenga información meteorológica real.
- La temperatura mostrada corresponda con la devuelta por el servicio.
- La probabilidad de precipitación corresponda con la devuelta por el servicio.
- Si el servicio no está disponible, el usuario reciba un mensaje de error adecuado.
- No existan cambios en el contrato del Orchestrator.