# Keepcon API - Pruebas y Documentación

Esta documentación detalla cómo realizar pruebas y consumir la API de Búsqueda (CEM Search API) de Keepcon, específicamente para obtener las últimas interacciones de Twitter (ahora X). Esta información servirá como base para la futura integración en el dashboard.

## 1. Configuración del Entorno de Pruebas

Para realizar las pruebas, se creó un entorno virtual de Python y se instalaron las dependencias necesarias:

```bash
# Crear entorno virtual en la carpeta pruebas
python3 -m venv pruebas/venv
source pruebas/venv/bin/activate

# Instalar dependencias
pip install requests python-dotenv
```

Se utilizó un script `test_keepcon_twitter.py` para ejecutar las peticiones HTTP.

## 2. Autenticación y Credenciales

Las credenciales necesarias se encuentran en el archivo `.env` en la raíz del proyecto:
- `token`: Token de acceso (`access_token`).
- `account_number`: Número de cuenta asignado en Keepcon (ej. `689`).

**Consideración:** El archivo `.env` actualmente tiene las variables separadas por dos puntos (`:`). En implementaciones estándar se recomienda usar `=` (ej. `token=123...`). Para la prueba, el script fue adaptado para leer el formato con `:`.

## 3. Endpoint Principal (Búsqueda de Contenido)

Para buscar contenido (menciones, mensajes, tweets, etc.), se utiliza el siguiente endpoint:

**Método HTTP:** `POST`
**URL:** `https://api.keepcon.com/accounts/{account_number}/content/search?access_token={token}`

### Payload (Cuerpo de la Petición)

El cuerpo de la petición debe enviarse en formato JSON (`Content-Type: application/json`). Para traer la información de Twitter en un rango de fechas, la estructura es:

```json
{
  "sources": [
    "twitter"
  ],
  "created_at_from": "2026-04-13T09:14:35",
  "created_at_to": "2026-05-13T09:14:35"
}
```

*Nota: Keepcon requiere que se especifique un rango de fechas o retornará un error HTTP 400 (`{"error":"Invalid dates filter"}`). Se utilizaron filtros de 30 días en formato ISO 8601.*

## 4. Respuesta de la API (Información Recibida)

Si la solicitud es exitosa, la API responde con un código HTTP 200 y un JSON que contiene un listado de elementos (`items`). Cada elemento representa una interacción y tiene la siguiente estructura clave:

```json
{
  "id": "MjA1NDM1OTI3Njk5OT...",
  "source": "twitter",
  "content_type": "direct-message", // Puede ser tweet, retweet, direct-message, etc.
  "content": {
    "id": "2054359276999639550",
    "text": "Gracias por la espera, David...",
    "url": null,
    "createdat": "2026-05-13T00:33:14+00:00",
    "user": {
      "id": "248877722",
      "username": "ClaroEcua",
      "name": "Claro Ecuador",
      "followers": 462662
    },
    "own_content": "true",
    "is_reply": false
  },
  "topics": [
    "ClaroEcuadorTW"
  ],
  "groups": [
    "Claro Ecuador"
  ],
  "tags": [],
  "sentiment": "no sentiment", // Ej. "neutral", "positive", "negative"
  "review_status": "NOT_REVIEWED",
  "updated_at": "2026-05-13T00:33:16+00:00"
}
```

### Atributos Relevantes para el Dashboard:

- `source`: Red social de origen (siempre será "twitter" para este caso).
- `content.text`: El mensaje o tweet en sí.
- `content.user.username` / `content.user.name`: Datos del usuario que interactuó.
- `sentiment`: Análisis de sentimiento automático asignado por Keepcon (útil para métricas del dashboard).
- `tags`: Etiquetas inteligentes asignadas a la interacción.
- `content_type`: Para diferenciar si es un tweet público o un mensaje directo (`direct-message`, `tweet`, `reply`, etc.).

## 5. Siguientes Pasos

Esta estructura de respuesta ya está lista para ser consumida y modelada dentro del código principal del Dashboard. Las funciones que consuman esta API deberán:
1. Generar dinámicamente las fechas `created_at_from` y `created_at_to`.
2. Parsear el resultado (la lista dentro del JSON devuelto).
3. Utilizar los campos de texto, sentimiento y nombre de usuario para construir los paneles del Dashboard.

## 6. Estadísticas Reales (Últimos 4 días)

Para dimensionar el volumen de datos que procesará el dashboard, se realizó una extracción masiva de los últimos 4 días en Facebook, Twitter e Instagram. El resultado arrojó un total de **4,818 interacciones**. 

La gran mayoría de estas interacciones son mensajes directos/privados (los cuales ya están excluidos en el script del dashboard). El desglose exacto de tipos de contenido y redes fue el siguiente:

**Conteo por Red Social (`source`):**
- Facebook: 2,701
- Twitter: 1,572
- Instagram: 546

**Desglose Detallado por Tipo de Contenido y Sentimiento:**

- **`fb-message` (Privado) - Total: 2,439**
  - `no sentiment`: 1,567
  - `neutral`: 650
  - `negative`: 200
  - `positive`: 22

- **`direct-message` (Privado, Twitter) - Total: 1,360**
  - `no sentiment`: 867
  - `neutral`: 295
  - `negative`: 188
  - `positive`: 10

- **`ig-message` (Privado, Instagram) - Total: 446**
  - `no sentiment`: 266
  - `neutral`: 117
  - `negative`: 55
  - `positive`: 8

- **`fb-comment` (Público) - Total: 203**
  - `no sentiment`: 92
  - `negative`: 62
  - `neutral`: 42
  - `positive`: 7

- **`tweet` (Público) - Total: 187**
  - `no sentiment`: 108
  - `negative`: 69
  - `neutral`: 7
  - `positive`: 3

- **`ig-comment` (Público) - Total: 89**
  - `positive`: 37
  - `no sentiment`: 23
  - `negative`: 17
  - `neutral`: 12

- **`fb-post` (Público) - Total: 61**
  - `no sentiment`: 61

- **`retweet` (Público) - Total: 21**
  - `no sentiment`: 12
  - `negative`: 5
  - `positive`: 4

- **`ig-video` (Público) - Total: 5**
  - `neutral`: 3
  - `no sentiment`: 2

- **`ig-story` (Público) - Total: 5**
  - `no sentiment`: 5

- **`quote` (Público) - Total: 5**
  - `negative`: 2
  - `neutral`: 2
  - `no sentiment`: 1

- **`ig-image` (Público) - Total: 1**
  - `neutral`: 1

*Como se puede observar, al filtrar los mensajes privados (`fb-message`, `direct-message`, `ig-message`), reducimos drásticamente el volumen de datos que el dashboard tiene que procesar, quedándonos solo con las interacciones públicas (~577 interacciones públicas en 4 días).*
