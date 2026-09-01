# Mapa de Onboarding

Este documento resume, con cita de archivo y línea, lo que se puede verificar
hoy en el repositorio. Separa hechos (evidencia directa en el código), de
inferencias (deducciones razonables sin confirmación explícita) y de
desconocidos (decisiones aún no tomadas o huecos detectados).

## 1. Fuente de verdad del comportamiento

**Hecho:** [`docs/contrato-api.md:3`](contrato-api.md) lo dice explícitamente:
*"Este documento fija comportamiento observable."* Las tablas del documento
"son lo que afirman los tests, y lo que la sesión 10 compara al revisar. No
los cambies sin cambiar antes este documento" (`docs/contrato-api.md:11-13`).

Ahí quedan fijados: catálogo de estados (`docs/contrato-api.md:58`), reglas de
normalización de `title` (`docs/contrato-api.md:20-31`), orden estable de
listados (`docs/contrato-api.md:33-42`) y los esquemas de respuesta exactos
(`docs/contrato-api.md:121-150`).

**Inferencia:** existió una copia en la raíz (`contrato-api.md`) según el
historial (commit `2b3d595`), pero no está en `git ls-files` actual — solo
vive la copia en `docs/`. No es un archivo activo.

## 2. Comandos exactos

Todos documentados en `README.md`:

| Acción | Comando | Línea |
|---|---|---|
| Instalar | `uv sync --frozen` | `README.md:10` |
| Probar | `uv run pytest -q` | `README.md:16` |
| Revisar estilo | `uv run ruff check .` | `README.md:22` |
| Levantar DB | `docker compose up -d` | `README.md:28` |
| Ejecutar API | `uv run uvicorn app.main:app --reload` | `README.md:34` |
| Detener DB | `docker compose down` | `README.md:42` |

**Desconocido:** no hay comando documentado para detener Uvicorn (se asume
`Ctrl+C`, pero no está escrito en ningún archivo).

## 3. Motor para futuros tests de persistencia

**Hecho:** `compose.yaml:3` fija `postgres:18-alpine` como base de datos.

**Desconocido (importante):** en `pyproject.toml:6-17` y en todo `uv.lock` no
hay ninguna librería de acceso a datos: ni `sqlalchemy`, ni
`asyncpg`/`psycopg`, ni `alembic`. Solo están `fastapi`, `uvicorn`, y en dev
`httpx`, `pytest`, `pytest-asyncio`, `ruff`. `app/main.py` no importa nada de
persistencia — hoy solo expone `/health` (`app/main.py:6-8`).

Es decir: el motor de base de datos (Postgres) está decidido, pero el
driver/ORM Python y la herramienta de migraciones para los tests de
persistencia todavía no están elegidos en el código. El contrato solo dice
"la migración" en abstracto (`docs/contrato-api.md:73`,
`docs/contrato-api.md:163`), sin nombrar herramienta.

## 4. Límites sobre archivos con secretos

**Hecho:** `.gitignore:1` ignora `.env`. `.env.example:1-2` trae el
comentario *"Copia este archivo a .env y ajusta los valores... Valores
locales ficticios; no usar en ningún entorno compartido."* Existe un `.env`
local no versionado — su contenido no se debe leer ni exponer fuera de la
máquina local.

**Hecho:** el contrato también pone un límite a nivel de API:
`docs/contrato-api.md:54` — `/health` *"No expone credenciales ni detalles
internos."*

## 5. Lo que no se puede establecer con evidencia

- **Driver/ORM y herramienta de migraciones** (ver punto 3) — no están en
  `pyproject.toml` ni `uv.lock`.
- **`docs/contrato-api.md:79`** enlaza a `../docs/glosario.md#idempotente`,
  pero ese archivo no existe en el repo (`docs/` solo tiene
  `contrato-api.md`) — enlace roto.
- **Archivo `d` en la raíz**: tracked, vacío, agregado en el commit inicial
  (`2d3cd81`) junto con el resto del scaffold. No hay pista de su propósito —
  probablemente accidental (p. ej. de copiar/pegar `docker compose up -d`).
- **Convenciones de commits/PR, CI**: no hay `.github/`, ni `CLAUDE.md`, ni
  configuración de pre-commit en el repo — cualquier flujo de CI/revisión
  automatizada aún no está definido en código.
