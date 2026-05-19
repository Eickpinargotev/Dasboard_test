---
created: 2026-05-14T16:57:15 (UTC -05:00)
tags: []
source: https://help.keepcon.app/?epkb_post_type_1=keepcon-ticket-api
author: 
---

# Keepcon Ticket API – Keepcon

> ## Excerpt
> Última actualización04/04/2022

---
Última actualización04/04/2022

## 1\. Keepcon Integrations

### 1.1 **Objetos principales**

**Content**

El objeto “content” representa un contenido publicado en un canal o red social como Email, Twitter, Facebook, Instagram, otros. Un contenido puede componerse de un texto, información sobre el autor y atributos tales como la fecha de creación, sentimiento, clasificación, entre otros.

Cada contenido es procesado automáticamente por el motor de clasificación Keepcon. Keepcon enriquece cada contenido con las siguientes dimensiones:

-   Análisis de sentimiento
-   Etiquetas que utilizan la taxonomía creada para cada cuenta
-   Extracción de información configurada para cada cuenta. Por ejemplo: número de teléfono, número de seguro social, dirección, ID de factura, ID de cliente, etc.
-   Nube de palabras
-   Información de perfil de usuario

**User Profile**

El objeto “user profile” representa al perfil de un usuario que interactúa con una empresa en las redes sociales. Un perfil de usuario puede interactuar en diferentes redes sociales. Por ejemplo, si una persona escribe mensajes en Facebook y Twitter, tendrá dos usuarios sociales, pero ambos usuarios sociales se fusionarán en un mismo perfil de usuario.

La lógica para mergear usuarios en Perfiles de usuario se define para cada cuenta. El cliente puede solicitar a Keepcon que combine usuarios utilizando la información extraída sobre el número de teléfono, la identificación de la seguridad social, la identificación del cliente o cualquier otro atributo de su negocio.

El perfil de usuario también tiene una lista de etiquetas inteligentes que pueden representar un conjunto de intereses para esa persona, estado de ánimo, pasatiempos, etc.

**Ticket**

El objeto “ticket” representa una gestión de atención al cliente dentro de Keepcon. 

### **1.2 Autorización y Seguridad** 

Para cada solicitud, se debe agregar un parámetro access\_token = {ACCESS-TOKEN}. Puede acceder y renovar su token en la sección de configuración de la aplicación.

Debe usar HTTPS para cada solicitud.

### 1.3 **Rate Limits**

Sólo permitimos un cierto número de solicitudes por minuto, según su plan y el punto final. Nos reservamos el derecho de ajustar el límite de velocidad para puntos finales dados para proporcionar una alta calidad de servicio a todos los clientes. 

## 2\. Ticket API

Permite crear tickets en Keepcon a partir de un email inicial con datos del ticket y opcionalmente datos a incorporar en el perfil de usuario.

### 2.1 Crear Ticket

Crea un nuevo ticket a partir una interacción inicial de tipo de email con atributos de ticket y opcionalmente datos de perfil de usuario. Devuelve un ID de ticket si tiene éxito.

Los atributos del ticket son configurables en cada cuenta y dependerán de las reglas de negocio de cada cliente. Los tipos de atributos posibles son: texto libre, fecha, booleano, email, numérico, taxonomía y taxonomía jerárquica.

La interacción inicial de email es la que da inicio al ticket, a partir del cual el agente podrá seguir en contacto con el usuario respondiendo dicho email en Keepcon. 

**Importante**: La interacción inicial NO ingresa a través de ningún tópico. Esto quiere decir que  no es visible desde Monitoring y automáticamente no cuenta con ningún grupo (label)

La información del email a enviar es: email del remitente (_from\_address_ y _full\_name_), lista de destinatarios del email (campo _to_, lista de emails), asunto del email (subject) y cuerpo del email (_text_, el cual puede contener texto plano o HTML).

#### 2.1.1 Request

Invoque el servicio con un POST HTTP enviando el ticket en formato JSON en el body del request.

|**Response format**|JSON|
|---|---|
|**Content-Type**|application/json|

#### 2.1.2 Parámetros

|**Parameter**|**Required**|**Type**|**Description**|
|---|---|---|---|
|access\_token|mandatory|query string|Access token válido. Provisto por Keepcon|
|ticket|mandatory|body|Información del Ticket a crear.
En la sección _custom\_attributes_ incluir como clave-valor los atributos custom del ticket definidos en la cuenta. En la sección _starting\_interaction_ incluir la información del email inicial del ticket.
Ejemplo:
`{    "priority": 3,    "custom_attributes": {      "motivo_de_contacto": "consulta",      "tipo_de_cliente": "hogar",      "numero_factura": 1234  },    "starting_interaction": {      "content_type": "email",      "content": {        "from": {          "full_name": "Juan Perez",          "email_address": "juan.perez@gmail.com"  },        "to": [ "atencion@mail.com"],        "subject": "[URGENTE]Error de facturación",        "text": "<div>Cliente: Juan Perez<br/>Reclamo: Se facturó erróneamente la compra</div>",        "created_at": "2020-01-16T14:11:24+0000",        "attachments": [        {            "file_name": "example.txt",            "content_type": "text/plain",            "base_64_content": "VGhpcyBpcyB5b3VyIGF0dGFjaGVkIGZpbGUhISEK"          }        ]      }    }  }`|
|user\_profile|optional|body|Datos a incorporar en el perfil de usuario del email especificado en el atributo email\_address en la sección starting\_interaction. En la sección customer\_attributes como clave-valor los atributos custom de perfil configurados en la cuenta.
Ejemplo:
`{    "tags": [    "VIP",    "Consumidor Frecuente"  ],    "custom_attributes": {      "nombre": "Juan Carlos",      "apellido": "Perez",      "telefono_movil": "+54116991234",      "dni": "20123123",      "email": "juan.car@gmail.com",      "fecha_de_nacimiento": "1980-01-01",      "edad": 40    }  }`|

#### 2.1.3 Respuesta

|**Status code**|**Response body**|**Description**|
|---|---|---|
|200|{“id”: “ABC123456”}|El ticket se creó correctamente. Devuelve el ID del ticket en Keepcon.|
|400|{“error”: “Invalid format…”}|Request invalido. Alguno de los valores especificados es incorrecto. Devuelve una descripción del error.|

## 3\. Creación de Ticket

En dicha sección se detalla cómo crear un ticket en Keepcon vía API REST. También se incluye la definición de los campos custom de los tickets y de los perfiles de usuarios.

### 3.1 Campos custom del Ticket

Todos los campos custom son opcionales. Los atributos del ticket son configurables en cada cuenta y dependerán de las reglas de negocio de cada cliente.

Para enviar datos de un campo debe incluirse en el Request, en el caso que no se quiera enviarlo no incluirlo en el request o en su defecto enviarlo con valor _null_.

A continuación se muestra un ejemplo de los campos del ticket, los cuales deberán ser enviados en la sección _custom\_attributes_ del ticket. 

Ejemplo:

|**Código de campo**|**Tipo dato JSON**|**Ejemplo**|**Observaciones**|
|---|---|---|---|
|motivo\_de\_contacto|String|“Consulta”|
|es\_cliente|Boolean|true|Boolean formato JSON|
|fecha\_creacion\_caso|String|“2019-12-09T09:30:05-03:00”|Formato ISO 8601|
|monto|Number|100.54|Formato JSON. De ser necesario, se utiliza “.” como separador de decimales, sin separador de miles|
|numero\_factura|Number|123456|Formato JSON|
|segmento\_cliente|String|“Empresas”|Formato JSON|
|tipologia\_del\_caso|String|“1\_1\_1”|Ejemplo formato de tres niveles donde esperamos recibir:
código nivel 1, código nivel 2, código nivel 3, concatenados por guión bajo (\_). 
Ejemplo: para “Reclamo, Problemas de Señal, Mobile” deberán enviar el código específico, en este caso sería: “1\_1\_1”|

### 3.2 Campos custom de perfil de usuario

Todos los campos custom son opcionales. Los atributos del ticket son configurables en cada cuenta y dependerán de las reglas de negocio de cada cliente.

Para enviar datos de un campo debe incluirse en el Request, en el caso que no se quiera enviarlo no incluirlo en el request o en su defecto enviarlo con valor _null_.

A continuación se muestra un ejemplo de los campos del perfil de usuario, los cuales deberán ser enviados en la sección _custom\_attributes_ del _user\_profile_. 

Ejemplo:

|**Código de campo**|**Tipo dato JSON**|**Ejemplo**|**Observaciones**|
|---|---|---|---|
|nombre|String|“Juan Carlos”|
|apellido|String|“Perez”|
|email|String|“juan.car@gmail.com”|
|telefono\_movil|String|“+541112345678”|
|telefono\_alternativo|String|“+541112345678”|
|fecha\_de\_nacimiento|String|“1980-01-01”|Formato ISO 8601|
|edad|Number|40|Formato JSON|

### **3.3 Ejemplo de request de creación de ticket**

`url -i -X POST \   -H "Content-Type:application/json" \     -d \'{  "ticket": {"priority": 3,    "starting_interaction": { "content_type": "email", "content": {"from": {"nombre_apellido": "Juan Perez", "email_address": "juan.perez@gmail.com"}, "to": ["atencion@mail.com"], "subject": "[URGENTE] Error de facturación", "text": "<div>Cliente: Juan Perez<br/>Reclamo: Se facturó erróneamente la compra</div>", "created_at": "2020-01-16T14:11:24+0000", "attachments": [{"file_name": "example.txt", "content_type": "text/plain", "base_64_content": "VGhpcyBpcyB5b3VyIGF0dGFjaGVkIGZpbGUhISEK"}]}}, "custom_attributes": {"motivo_de_contacto": "Consulta", "es_cliente": true, "fecha_creacion_caso": "2019-12-09T00:00:00-03:00", "monto": 100.54, "numero_factura": 123456, "segmento_cliente": "Empresas", "tipologia_del_caso": "1_1_1" }}, "user_profile": { "tags": [], "custom_attributes": {"nombre": "Juan Carlos", "apellido": "Perez", "email": "juan.car@gmail.com", "telefono_movil": "+541162991234", "telefono_alternativo": "+541112345678", "fecha_de_nacimiento": "1980-01-01", "edad": 40}  }}'\`

Ante cualquier duda consultar al responsable asignado a su cuenta.

___

¿Te gustó este artículo?
