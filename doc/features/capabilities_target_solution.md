# Feature: Centralización del destinatario de correo en Identity Service

## Objetivo

Modificar la arquitectura de la capability **"Qué sabes hacer"** para que la dirección de correo del usuario deje de ser responsabilidad del Orchestrator y pase a ser gestionada exclusivamente por Identity Service.

El objetivo es reforzar la separación de responsabilidades y garantizar que únicamente pueda enviarse correo al destinatario configurado en el sistema.

No se modifica el comportamiento observable por el usuario.

---

# Requisitos funcionales

## RF-1. Obtención del destinatario

Mail Watchdog deberá obtener la dirección de correo del usuario consultando Identity Service mediante su API.

La dirección de correo dejará de ser proporcionada por el Orchestrator.

---

## RF-2. Nuevo contrato con Mail Watchdog

El contrato de invocación de Mail Watchdog dejará de incluir el campo correspondiente al destinatario del correo.

El contrato deberá contener únicamente la información necesaria para generar el mensaje (asunto, contenido, adjuntos u otros datos funcionales).

---

## RF-3. Eliminación de la responsabilidad del Orchestrator

El Orchestrator no deberá conocer la dirección de correo del usuario.

En consecuencia:

* no cargará el correo desde variables de entorno;
* no realizará llamadas a Identity Service para obtenerlo;
* no lo incluirá en solicitudes dirigidas a Mail Watchdog.

---

## RF-4. Envío del correo

Mail Watchdog utilizará exclusivamente la dirección obtenida desde Identity Service como destinatario del mensaje.

No deberá existir ningún mecanismo para indicar un destinatario alternativo mediante el contrato de la API.

---

## RF-5. Compatibilidad funcional

La capability "Qué sabes hacer" deberá mantener exactamente el mismo comportamiento observable:

* Nova continuará informando por voz del número de capabilities disponibles.
* Nova continuará enviando un correo con el detalle completo de dichas capabilities.

No deberán producirse cambios en el contenido del correo ni en la experiencia del usuario.

---

# Requisitos no funcionales

## RNF-1. Fuente única de verdad

Identity Service será la única fuente autorizada para la obtención del correo electrónico del usuario.

Ningún otro servicio deberá mantener una copia persistente de dicha información.

---

## RNF-2. Encapsulación

La responsabilidad de decidir el destinatario del correo recaerá exclusivamente en Mail Watchdog.

Los servicios consumidores únicamente solicitarán el envío del mensaje.

---

## RNF-3. Seguridad

La arquitectura deberá impedir el envío de correos a destinatarios arbitrarios mediante la API de Mail Watchdog.

El destinatario utilizado será siempre el configurado en Identity Service.

---

## RNF-4. Separación de responsabilidades

Cada servicio mantendrá una responsabilidad claramente definida:

* Identity Service gestiona la identidad del usuario y su dirección de correo.
* Mail Watchdog gestiona el envío de correo y determina el destinatario consultando Identity Service.
* Orchestrator únicamente coordina el flujo funcional.

---

## RNF-5. Simplificación del contrato

La API de Mail Watchdog deberá eliminar toda información redundante relacionada con el destinatario del mensaje.

El contrato deberá reflejar únicamente la intención de enviar un correo, sin exponer detalles de direccionamiento.

---

## RNF-6. Eliminación de código obsoleto

Deberá eliminarse todo el código relacionado con la obtención, almacenamiento o propagación del correo electrónico del usuario dentro del Orchestrator.

No deberán permanecer variables de entorno, configuraciones, clases, contratos o lógica asociada que hayan dejado de utilizarse.

---

## RNF-7. Compatibilidad

El cambio deberá ser completamente transparente para el usuario.

No se modificará la interfaz de voz, el contenido del correo ni el comportamiento funcional de la capability.

El impacto del cambio deberá limitarse exclusivamente a la arquitectura interna de los servicios.
