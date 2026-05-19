# Reporte: lentitud al presionar "Actualizar" en Claro / Keepcon

Fecha de revision: 2026-05-19

## Resumen ejecutivo

El boton **Actualizar** de la pestaña Claro espera a que termine todo el proceso backend de `POST /api/v1/keepcon/refresh`. Ese proceso es sincrono: la UI queda en estado "Actualizando" hasta que el backend termina de consultar Keepcon, enriquecer perfiles, calcular sentimiento/ubicacion con IA y guardar el CSV.

La lentitud no parece estar en el render del frontend. El cuello de botella esta en el backend, principalmente por dos factores:

1. **Llamadas externas a Keepcon**, que se hacen por paginas y dos veces: por `created_at` y por `updated_at`.
2. **Analisis de sentimiento/ubicacion con OpenAI**, que se ejecuta dentro del mismo refresh para cada registro que no tenga `ai_sentiment`, en lotes secuenciales de 10.

Con los datos locales actuales, el CSV tiene **1,169 registros** y **69 registros sin `ai_sentiment`**. Con la configuracion actual (`KEEPCON_OPENAI_SYNC_CHUNK_SIZE=10` por defecto), esos 69 pendientes equivalen a hasta **7 llamadas secuenciales a OpenAI** si esos registros entran en el resultado del refresh o del backfill.

## Flujo actual del boton

Frontend:

- `frontend/src/App.jsx:161-172`
- `refreshClaro()` llama a:
  - `POST /api/v1/keepcon/refresh?days=<filtro>`
  - luego, solo cuando termina, ejecuta `loadClaro()`.

Backend:

- `backend/src/api/routers/keepcon_router.py:37-60`
- El endpoint llama directamente a `service.refresh_latest(days_filter=days)`.
- El comentario del codigo confirma que se ejecuta de forma sincrona para el boton.

Servicio:

- `backend/src/services/keepcon/service.py:90-140`
- `refresh_latest()` hace:
  1. Lee estado de sincronizacion.
  2. Carga el CSV existente.
  3. Busca contenido nuevo por `created_at`.
  4. Busca contenido actualizado por `updated_at`.
  5. Fusiona resultados.
  6. Cuenta cambios.
  7. Guarda CSV.
  8. Recien ahi responde al frontend.

## Donde se puede estar tardando

### 1. API de Keepcon

Archivo: `backend/src/services/keepcon/client.py`

- Busqueda de contenido: `requests.post(... timeout=30)` en `client.py:42-48`.
- Busqueda de perfiles: `requests.get(... timeout=20)` en `client.py:84-90`.

Cada pagina de contenido puede tardar hasta 30 segundos antes de fallar por timeout. Ademas, `refresh_latest()` puede hacer dos recorridos:

- `created_result = fetch_data_from_api(... mode="created")`
- `updated_result = fetch_data_from_api(... mode="updated")`

Eso esta en `backend/src/services/keepcon/service.py:107-110`.

Si Keepcon responde con varias paginas (`next_page_token`), el proceso las consume secuencialmente. Y si el contenido es de alto riesgo o negativo y no trae followers, puede hacer llamadas adicionales a perfiles (`get_profile`) tambien secuenciales.

### 2. Calculos de sentimiento / IA

Archivo: `backend/src/services/keepcon/service.py`

Al final de cada `fetch_data_from_api()`, despues de procesar las paginas de Keepcon, el codigo hace:

- `missing_ai = [item for item in all_results if not item.get("ai_sentiment")]`
- `ai_results = self.ai_analyzer.analyze_missing(missing_ai)`

Eso esta en `backend/src/services/keepcon/service.py:81-85`.

Archivo: `backend/src/services/keepcon/ai_analysis.py`

- Los registros pendientes se mandan a OpenAI en lotes de `openai_sync_chunk_size`.
- El valor por defecto es 10 (`backend/src/services/keepcon/config.py:14-16`).
- Cada lote se ejecuta secuencialmente.
- Cada llamada a OpenAI tiene timeout de 60 segundos (`ai_analysis.py:96-98`).

Con 69 pendientes locales, el peor caso operativo para IA seria:

- 69 registros / 10 por lote = 7 llamadas.
- Si cada llamada tarda varios segundos, el boton se queda esperando todo ese tiempo.
- Si una llamada se cuelga hasta timeout, puede sumar hasta 60 segundos por lote.

## Evidencia local encontrada

CSV revisado:

- Archivo: `backend/data/keepcon_data.csv`
- Registros: 1,169
- Registros con `ai_sentiment`: 1,100
- Registros sin `ai_sentiment`: 69

Distribucion local de `ai_sentiment`:

- negative: 453
- neutral: 264
- positive: 240
- no sentiment: 143
- blanco: 69

Estado de sincronizacion:

- Archivo: `backend/data/keepcon_sync_state.json`
- `last_created_at_sync`: 2026-05-19T17:30:07.004827
- `last_updated_at_sync`: 2026-05-19T17:30:07.004827
- `last_successful_refresh_at`: 2026-05-19T17:30:14.628402+00:00

Ese ultimo estado sugiere que el sistema ya guarda la duracion del refresh en la respuesta (`duration_ms`), pero no hay desglose por etapa.

## Diagnostico

El problema principal no es un unico punto aislado; es que el boton ejecuta un pipeline externo completo de forma sincrona.

Mi lectura:

- Si hay pocos registros nuevos y ya tienen `ai_sentiment`, la demora probablemente venga de Keepcon: busqueda `created_at`, busqueda `updated_at`, paginacion y posibles perfiles.
- Si entran varios registros sin `ai_sentiment`, la demora probablemente venga del analisis OpenAI, porque se ejecuta en lotes secuenciales antes de responder.
- En el estado actual hay 69 pendientes de IA, asi que el calculo de sentimiento es un candidato fuerte para explicar demoras largas cuando esos pendientes son procesados.

No ejecute el refresh real porque podria modificar `backend/data/keepcon_data.csv` y el estado de sincronizacion. Este reporte se basa en lectura de codigo y datos locales existentes.

## Como confirmarlo con precision

Agregar medicion por etapas en `refresh_latest()` y `fetch_data_from_api()`:

- tiempo leyendo CSV
- tiempo Keepcon `created_at`
- paginas Keepcon `created_at`
- tiempo Keepcon `updated_at`
- paginas Keepcon `updated_at`
- cantidad de profile calls
- tiempo total de profile calls
- cantidad de registros enviados a IA
- cantidad de lotes IA
- tiempo total IA
- tiempo guardando CSV

El endpoint ya devuelve `duration_ms`, `created_pages`, `updated_pages`, `profile_calls` y `fetched_records`, pero falta separar cuanto duro cada etapa.

## Soluciones recomendadas

### Opcion 1: separar el refresh de Keepcon del analisis IA

El boton deberia:

1. Consultar Keepcon.
2. Guardar registros nuevos/actualizados.
3. Responder rapido al frontend.
4. Lanzar el analisis IA en background para los registros pendientes.

Impacto esperado:

- El boton deja de esperar OpenAI.
- La UI puede mostrar "datos actualizados; analisis IA en proceso".
- Los sentimientos aparecen cuando termine el job.

Esta es la solucion mas importante.

### Opcion 2: hacer el refresh asincrono

Cambiar `POST /refresh` para que cree un job y responda inmediatamente con un `job_id`.

Luego el frontend consulta:

- estado: pending / running / done / error
- progreso: paginas, registros, lotes IA
- duracion por etapa

Impacto esperado:

- El usuario no queda bloqueado.
- Se puede mostrar progreso real.
- Se evitan timeouts de navegador o proxy.

### Opcion 3: usar Keepcon como sentimiento inicial

Actualmente existe `keepcon_sentiment` y tambien `ai_sentiment`.

Para velocidad:

- Guardar y mostrar `keepcon_sentiment` inmediatamente.
- Calcular `ai_sentiment` despues, en background.
- Usar `ai_sentiment` solo cuando ya exista; si no, fallback a `keepcon_sentiment`.

Esto ya se hace parcialmente en filtros, pero el refresh sigue intentando calcular IA antes de terminar.

### Opcion 4: limitar IA en refresh manual

Si se quiere mantener todo sincrono, poner un limite:

- maximo 10 o 20 registros IA por click
- o solo analizar IA para registros nuevos
- o saltar IA cuando `days=1` y hay muchos pendientes acumulados

Impacto esperado:

- Menor demora maxima.
- Menos riesgo de que un backlog viejo haga lento el boton.

### Opcion 5: paralelizar con cuidado

Paralelizar algunas llamadas podria ayudar, pero no seria mi primera opcion porque aumenta riesgo de rate limits.

Candidatos:

- llamadas OpenAI por lotes con concurrencia baja, por ejemplo 2 o 3
- profile lookups con concurrencia baja

Antes de paralelizar conviene instrumentar tiempos para confirmar el cuello de botella real.

## Recomendacion final

Implementaria primero:

1. Instrumentacion por etapas para confirmar tiempos reales.
2. Cambio del boton a refresh rapido: Keepcon + guardado CSV sin esperar IA.
3. Job de IA en background para `ai_sentiment` y `ai_location`.
4. Mostrar en UI el estado "analizando sentimiento" cuando haya pendientes.

Con eso el boton dejaria de depender de la latencia acumulada de OpenAI y Keepcon, y quedaria claro en metricas si Keepcon esta lento, si hay muchas paginas, si hay muchas llamadas de perfil o si el backlog de sentimiento esta creciendo.
