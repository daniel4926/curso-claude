# Plan: conexión a PostgreSQL

Planificación acordada para conectar la API a PostgreSQL en incrementos.
Fuentes: `docs/contrato-api.md` (secciones Salud y Estados),
`docs/decisiones-ingenieria.md`, `CLAUDE.md`.

Fuera de alcance: proyectos, tareas, filtros, `due_at`, skills, hooks y CI.

Cada incremento se confirma solo, con su propia comprobación. No se encadena
el siguiente sin aprobación explícita.

## Qué existe hoy

- `app/main.py:1-8` — FastAPI con un único endpoint, `GET /health`, que ya
  cumple el contrato (`docs/contrato-api.md:44-54`) devolviendo
  `{"status": "ok"}` sin tocar ninguna base de datos.
- No hay ninguna dependencia de persistencia: `pyproject.toml` y `uv.lock` no
  incluyen SQLAlchemy, driver de Postgres ni Alembic.
- `compose.yaml` ya levanta Postgres 18 con credenciales tomadas de
  variables de entorno (por defecto o de `.env`).
- `docs/contrato-api.md:56-80` fija el catálogo de Estados (`PENDIENTE`,
  `EN_CURSO`, `BLOQUEADA`, `HECHA`), sin endpoints propios salvo
  `GET /states`, y exige que el seed viva en una migración idempotente, no en
  un script de Docker.
- `tests/test_health.py` es la única prueba existente, corre en memoria (sin
  Postgres) y pasa; `uv run ruff check .` está limpio.
- `docs/decisiones-ingenieria.md:11-18` fija: pruebas de persistencia contra
  PostgreSQL real (no SQLite), esquema vía migraciones de Alembic sin
  efectos al importar módulos, y cada migración probada en `upgrade` y
  `downgrade` antes de integrarse.

El motor (Postgres) está decidido, pero el driver/ORM y la herramienta de
migraciones no estaban elegidos en código antes de este plan.

## Secuencia de incrementos

### 1. Dependencias de persistencia

Agregar SQLAlchemy (async) + `asyncpg` como driver de la app, y Alembic para
migraciones. Solo `pyproject.toml`/`uv.lock`, sin tocar `app/`.

Comprobación: `uv sync --frozen` resuelve limpio; `uv run pytest -q` y
`uv run ruff check .` siguen en verde.

### 2. Configuración de conexión

`app/db.py` (o similar) con el engine/sesión async, leyendo host/usuario/db/
puerto de variables de entorno con los mismos nombres que `.env.example`
(sin abrir `.env`). Todavía sin endpoints nuevos.

Comprobación: con `docker compose up -d`, un test o script mínimo hace
`SELECT 1` contra la base real y confirma la conexión.

### 3. Infraestructura de Alembic

`alembic init`, `env.py` apuntando a la configuración del paso 2, primera
revisión vacía (sin tablas todavía).

Comprobación: `alembic upgrade head` contra Postgres limpio funciona, y
`alembic downgrade base` revierte sin dejar rastro.

### 4. Migración del catálogo de Estados

Tabla `states` + seed idempotente de los cuatro códigos fijos
(`docs/contrato-api.md:58`).

Comprobación: test nuevo, que primero falla por ausencia de la capacidad,
verificando que el catálogo existe tras `upgrade`, que migrar dos veces no
duplica filas, y que `downgrade` limpia — todo contra Postgres real.

### 5. Endpoint `GET /states`

Lee el catálogo desde la base y responde con el orden exacto del contrato
(campo de orden, `id` como desempate) y el esquema exacto `{"id", "code"}`
(`docs/contrato-api.md:63-65,121-129`).

Comprobación: test de integración de `GET /states` contra Postgres,
verificando orden estable entre llamadas y que no haya campos de más ni de
menos.

`GET /health` no requiere cambios: el contrato no exige que verifique la
base, así que queda fuera de estos incrementos salvo decisión explícita en
contrario.

## Decisión abierta

Stack propuesto por defecto: SQLAlchemy async + `asyncpg` + Alembic, ya que
no estaba fijado en ningún documento del repo. Queda sujeto a confirmación
antes de arrancar el incremento 1.
