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

3. **Base de Datos (`db`)**:
   - **Tecnología**: PostgreSQL (Imagen específica solicitada).
   - **Función**: Almacenar información procesada de las APIs para control interno y evitar duplicados.
   - **Nota de Persistencia**: Los volúmenes locales se usan para el código de las aplicaciones. La base de datos es efímera según sus requerimientos (los datos siempre pueden volver a consumirse de las APIs).

4. **Entorno de Pruebas (`api_tester`)**:
   - **Tecnología**: Consola Python interactiva/Scripts.
   - **Función**: Un contenedor aislado para probar rápidamente conexiones a APIs de terceros (como la de X), validar estructuras de entrada/salida y hacer debug sin afectar el backend principal.

## Estructura de Directorios

```text
viewer_main/
├── docker-compose.yml       # Orquestador de servicios
├── README.md                # Documentación principal
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

1. Configurar las credenciales en un archivo `.env` en la raíz (basado en el actual, agregando variables de BD).
2. Levantar todo el entorno:
   ```bash
   docker-compose up --build
   ```
3. **Acceso a los servicios**:
   - **Frontend**: http://localhost:5173
   - **Backend Documentación (Swagger)**: http://localhost:8000/docs
   - **Consola de Pruebas**: Se puede ejecutar un script o entrar al bash del contenedor de pruebas:
     ```bash
     docker-compose exec api_tester bash
     ```

## Diseño de la Base de Datos
- Por el momento se diseñará una tabla central unificada (ej. `social_mentions`) para guardar registros con `platform_id` (ej. 'x', 'instagram') para evitar duplicidad de menciones o leads, según lo solicitado.
