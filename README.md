# Vambe Dashboard — Categorización Automática y Visualización de Métricas de Clientes

Aplicación full-stack que procesa transcripciones de reuniones de ventas, las categoriza automáticamente con un LLM (Gemma 4) y muestra métricas en un dashboard interactivo.

---

## Instrucciones para ejecutar la aplicación

### Prerrequisitos

- [Docker](https://www.docker.com/get-started) y Docker Compose instalados
- Una API key de un LLM compatible con OpenAI (Gemma 4, OpenAI, etc.)

### Pasos

1. **Clonar el repositorio**

   ```bash
   git clone https://github.com/jcarrascoa7/vambe-technical-test.git
   cd vambe-technical-test
   ```

2. **Configurar variables de entorno**

   Copiar el archivo de ejemplo y configurar la API key del LLM:

   ```bash
   cp .env.example .env
   ```

   Editar `.env` y completar:

   | Variable | Descripción | Ejemplo |
   |---|---|---|
   | `DATABASE_URL` | Cadena de conexión a PostgreSQL | `postgresql://postgres:postgres@db:5432/vambe` |
   | `POSTGRES_USER` | Usuario de PostgreSQL | `postgres` |
   | `POSTGRES_PASSWORD` | Contraseña de PostgreSQL | `postgres` |
   | `POSTGRES_DB` | Nombre de la base de datos | `vambe` |
   | `LLM_API_KEY` | API key del LLM compatible con OpenAI | `tu_api_key_aquí` |
   | `LLM_API_URL` | URL base de la API del LLM | `https://token-plan-sgp.xiaomimimo.com/v1` |
   | `LLM_MODEL` | Nombre del modelo LLM | `mimo-v2.5-pro` |
   | `MAX_RECORDS_TO_CATEGORIZE` | Máximo de registros a categorizar | `1000` |

3. **Iniciar la aplicación**

   ```bash
   docker compose up --build
   ```

   - **Puerto de la aplicación**: `http://localhost:8000`
   - **Puerto de PostgreSQL**: `5432`

4. **Primer arranque**

   En el primer inicio, el sistema ejecuta automáticamente:
   - **ETL**: Lee el CSV, limpia los datos y los carga en PostgreSQL (~30 segundos)
   - **Categorización**: Procesa los registros en lotes de 50 usando el LLM (~30-40 minutos para 1000 registros)

   El dashboard es accesible desde el inicio y muestra métricas parciales mientras la categorización corre en segundo plano. Una barra de progreso indica el avance.

5. **Reiniciar sin perder datos**

   Los datos se persisten en un volumen de Docker. Para reiniciar sin perder datos:

   ```bash
   docker compose down
   docker compose up
   ```

   Para limpiar completamente y empezar de cero:

   ```bash
   docker compose down -v
   docker compose up --build
   ```

---

## Documentación básica

### Arquitectura del sistema

El sistema consta de dos contenedores orquestados por Docker Compose:

```
┌─────────────────────────────────────────────────────────┐
│                    App Container                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │   FastAPI     │  │   ETL        │  │ Categorizer  │  │
│  │   (API +      │  │   (pandas)   │  │ (prompts +   │  │
│  │   Static)     │  │              │  │  validation) │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
│         │                 │                 │           │
│         └─────────────────┼─────────────────┘           │
│                           │                             │
│                    React Frontend                        │
│                    (static build)                        │
└───────────────────────────┬─────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    │  PostgreSQL   │
                    │  (Docker)     │
                    └───────────────┘
                            │
                    ┌───────┴───────┐
                    │  Gemma 4 API  │
                    │  (externo)    │
                    └───────────────┘
```

**Backend (FastAPI)**: Sirve la API REST y los archivos estáticos del frontend. Incluye la lógica de startup que ejecuta ETL y categorización automáticamente.

**ETL (pandas)**: Lee el CSV de 10,000 registros, limpia datos (fechas, nulos, duplicados) y carga en PostgreSQL.

**Categorizador**: Usa prompts estructurados con few-shot examples para que el LLM clasifique cada transcripción en 10 dimensiones. Valida las respuestas contra listas predefinidas y mapea categorías inválidas a "Otros".

**Frontend (React + Vite + Chart.js + Tailwind)**: Dashboard interactivo con filtros, KPIs, gráficos y tabla de clientes.

**PostgreSQL**: Base de datos relacional que almacena todos los registros con sus categorías.

### Funcionalidades

- **ETL**: Limpieza automática de CSV con pandas, carga idempotente en PostgreSQL
- **Categorización**: Clasificación automática de transcripciones en 10 dimensiones usando LLM
- **Dashboard**: Visualización interactiva con filtros combinables, KPIs, gráficos y tabla paginada
- **Métricas**: 12 endpoints de métricas con agregaciones sobre datos categorizados
- **Filtros**: Búsqueda por texto y filtros por dimensión, combinables con lógica AND

### Stack utilizado

| Componente | Tecnología | Justificación |
|---|---|---|
| Backend | FastAPI (Python) | Async nativo, documentación OpenAPI automática, un solo lenguaje para backend y ETL |
| ETL | Python + pandas | Limpieza de datos robusta, manejo de CSVs grandes |
| Categorización | httpx async + LLM API | Llamadas HTTP directas sin dependencias de SDK, concurrencia para lotes |
| Base de datos | PostgreSQL | Consultas complejas para filtros y agregaciones, soporte para producción |
| Frontend | React + Vite + Chart.js + Tailwind | UI moderna y responsiva, builds rápidos, gráficos interactivos |
| Contenedores | Docker Compose | Un solo comando levanta todo el stack |
| CI/CD | GitHub Actions | Linting, tests y build automatizados en cada push |

### Configuración de la API key del LLM

El sistema usa un LLM compatible con la API de OpenAI. Para configurarlo:

1. Obtener una API key de un proveedor compatible (Gemma 4 via Google AI Studio, OpenAI, etc.)
2. Editar `.env` y establecer:
   - `LLM_API_KEY`: Tu API key
   - `LLM_API_URL`: URL base de la API (ej: `https://token-plan-sgp.xiaomimimo.com/v1`)
   - `LLM_MODEL`: Nombre del modelo (ej: `mimo-v2.5-pro`)
3. El sistema usa la API con `temperature=0` para respuestas deterministas

Si la API key no está configurada, la aplicación inicia pero la categorización falla silenciosamente.

---

## Decisiones clave

### Dimensiones descartadas del análisis

| Dimensión | Razón de descarte |
|---|---|
| **Tipo de objeción dominante** | Las transcripciones son reuniones de discovery, no conversaciones de objeción. La detección por regex dio 1.1% de falsos positivos |
| **B2B vs B2C** | Se superpone con "Sector" y "Tamaño". Aporta poco valor incremental y aumenta la carga de clasificación |
| **Horarios de disponibilidad** | Mencionado en muy pocas transcripciones explícitamente. Se puede inferir parcialmente del sector |

### Técnicas para garantizar consistencia de respuestas del LLM

1. **Prompts estructurados con schema JSON**: Cada prompt incluye el schema exacto de la respuesta esperada, reduciendo ambigüedad
2. **Few-shot examples**: Ejemplos concretos de transcripciones y sus categorías correctas para guiar al modelo
3. **Validación post-respuesta**: Todas las categorías devueltas se validan contra listas predefinidas. Categorías inválidas se mapean a "Otros"
4. **Temperature 0**: Respuestas deterministas para el mismo input
5. **Reintentos automáticos**: El cliente HTTP reintenta en caso de timeout o respuesta malformada
6. **Lotes con checkpoint**: Procesamiento en lotes de 50 con persistencia intermedia. Si falla un lote, los anteriores ya están guardados

### Por qué se eligió el stack

- **Python en todo el backend**: pandas ya requiere Python para el ETL. Usar el mismo lenguaje para API, ETL y categorización simplifica el desarrollo y despliegue
- **FastAPI sobre Flask/Django**: Async nativo para llamadas concurrentes al LLM. Documentación OpenAPI automática. Más liviando que Django para este tamaño de proyecto
- **PostgreSQL sobre SQLite**: Consultas complejas con filtros combinados y agregaciones. SQLite no soportaría patrones de producción
- **React + Vite sobre Next.js/otros**: Builds rápidos, ecosistema maduro, suficiente para un dashboard sin SSR
- **Chart.js sobre D3/otros**: Más simple de usar para gráficos estándar, buena documentación, suficiente para las visualizaciones requeridas
- **Docker Compose**: Un solo comando levanta backend, frontend y base de datos. Elimina "works on my machine"

---

## Enlaces

- **Repositorio**: [https://github.com/jcarrascoa7/vambe-technical-test.git](https://github.com/jcarrascoa7/vambe-technical-test.git)
- **App desplegada**: [https://vambe-dashboard.onrender.com](https://vambe-dashboard.onrender.com)

---

## Ejecución de tests

```bash
# Dentro del contenedor
docker compose exec app pytest backend/tests/ -v

# Tests específicos
docker compose exec app pytest backend/tests/test_etl.py -v
docker compose exec app pytest backend/tests/test_categorizer.py -v
docker compose exec app pytest backend/tests/test_api_clients.py -v
docker compose exec app pytest backend/tests/test_api_metrics.py -v
```

---

## Licencia

Proyecto técnico para evaluación de Vambe.
