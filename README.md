# Monitoreo Estratégico Social Dashboard - Arquitectura Modular

Este proyecto ha sido refactorizado para utilizar una arquitectura de microservicios limpia y escalable. Todo el entorno está contenedorizado, evitando un enfoque monolítico.

## Arquitectura del Proyecto

El entorno está orquestado con `docker-compose` y cuenta con los siguientes servicios:

1. **Frontend (`frontend`)**:
   - **Tecnología**: Vite + React (Ligero, rápido, y moderno).
   - **Función**: Interfaz de usuario para visualizar el dashboard de menciones, crisis y oportunidades.

2. **Backend API (`backend`)**:
   - **Tecnología**: Python 3.11 + FastAPI.
   - **Arquitectura**: Clean Architecture y Domain-Driven Design (DDD). Separación clara entre enrutadores (API), lógica de negocio (Servicios) y acceso a datos (Modelos/Repositorios).
   - **Modularidad**: Diseñado para soportar múltiples fuentes (X, Instagram, Facebook). Por ahora, el módulo de `X` (Twitter) es el foco.

3. **Almacenamiento local**:
   - **Tecnología**: Archivos locales generados por el backend.
   - **Función**: Guardar datos procesados y estado de sincronización durante el uso local.
   - **Nota de seguridad**: La carpeta `backend/data/` está ignorada por git porque puede contener información generada por APIs externas.

4. **Entorno de Pruebas (`api_tester`)**:
   - **Tecnología**: Consola Python interactiva/Scripts.
   - **Función**: Un contenedor aislado para probar rápidamente conexiones a APIs de terceros (como la de X), validar estructuras de entrada/salida y hacer debug sin afectar el backend principal.

## Estructura de Directorios

```text
viewer_main/
├── docker-compose.yml       # Orquestador de servicios
├── README.md                # Documentación principal
├── .env.example             # Plantilla de variables de entorno sin secretos
├── docs/                    # Documentación detallada
│   └── keepcon/             # Documentación de Keepcon API
├── backend/                 # API FastAPI (Python)
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── src/                 # Estructura modular (core, api, services)
│   │   └── services/keepcon/ # Módulo Keepcon modularizado
│   └── tests/               # Pruebas automatizadas y scripts de validación
├── frontend/                # Aplicación Web (Dashboard)
└── api_tester/              # Herramientas de diagnóstico de API
```

## Instrucciones de Despliegue

1. Crear el archivo local de variables de entorno:
   ```bash
   cp .env.example .env
   ```
2. Completar `.env` con las credenciales reales:
   ```env
   KEEPCON_TOKEN=
   KEEPCON_ACCOUNT_NUMBER=
   SCRAPEBADGER_API=
   OPENAI_API=
   ```
3. Levantar todo el entorno:
   ```bash
   docker-compose up --build
   ```
4. **Acceso a los servicios**:
   - **Frontend**: http://localhost:5173
   - **Backend Documentación (Swagger)**: http://localhost:8000/docs
   - **Consola de Pruebas**: Se puede ejecutar un script o entrar al bash del contenedor de pruebas:
     ```bash
     docker-compose exec api_tester bash
     ```

## Variables de Entorno

Las variables principales están documentadas en `.env.example`:

- `KEEPCON_TOKEN`: token de acceso a Keepcon.
- `KEEPCON_ACCOUNT_NUMBER`: número de cuenta de Keepcon.
- `SCRAPEBADGER_API`: API key de Scrapebadger.
- `OPENAI_API`: API key de OpenAI para análisis con IA.
- `REFRESH_INTERVAL_SECONDS`: intervalo de actualización del módulo Keepcon.
- `SCRAPEBADGER_REFRESH_INTERVAL_SECONDS`: intervalo de actualización del módulo Scrapebadger.

`docker-compose.yml` requiere `KEEPCON_TOKEN` y `KEEPCON_ACCOUNT_NUMBER`. Si no están definidos en `.env`, el backend no iniciará para evitar ejecutar el proyecto con credenciales incompletas o valores de prueba.

## Seguridad Antes de Subir a GitHub

Este proyecto incluye un `.gitignore` preparado para no subir credenciales ni archivos generados. En particular, quedan fuera del repo:

- `.env` y variantes locales de entorno.
- `node_modules/`.
- `frontend/dist/`.
- `__pycache__/` y archivos `.pyc`.
- `backend/data/`.
- `backend/tests/keepcon_debug/`.
- certificados, llaves privadas y carpetas de credenciales.

Antes de publicar, verifica el estado con:

```bash
git status --ignored --short
```

`.env` debe aparecer como ignorado. Solo debe subirse `.env.example`, que no contiene claves reales.

Si una clave real fue escrita por error en un archivo local, rota o revoca esa credencial en el proveedor correspondiente antes de publicar el repositorio.
