# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos

Gestionado con [uv](https://docs.astral.sh/uv/), Python 3.12 exacto (`requires-python = "==3.12.*"`).

```sh
uv sync --frozen                          # instalar dependencias exactas del lockfile
uv run pytest -q                          # correr toda la suite
uv run pytest tests/test_health.py -q     # correr un solo archivo de test
uv run pytest tests/test_health.py::test_health_returns_ok -q  # correr un solo test
uv run ruff check .                       # lint
docker compose up -d                      # levantar Postgres (necesario antes de correr la API si hay endpoints con persistencia)
uv run uvicorn app.main:app --reload      # arrancar la API (http://127.0.0.1:8000)
docker compose down                       # apagar Postgres
```

Ruff está configurado con `select = ["E", "F", "I", "UP"]` y `line-length = 100` (`pyproject.toml`).

## Arquitectura

Este es el scaffold inicial de una API de gestión de tareas (TaskFlow), construida con FastAPI. Hoy en día `app/main.py` solo expone `GET /health`; el resto de la API (proyectos, tareas, estados) todavía no está implementado, pero su comportamiento observable ya está **fijado por contrato** en `docs/contrato-api.md` — léelo antes de implementar o modificar cualquier endpoint, porque define exactamente lo que los tests van a verificar.

Puntos del contrato que no son obvios desde el código y que hay que respetar al implementar:

- **Estados es un catálogo cerrado** (`PENDIENTE`, `EN_CURSO`, `BLOQUEADA`, `HECHA`) sin endpoints de creación/borrado. Debe poblarse vía **migración** (se ejecuta en cada `upgrade`, no solo al crear el volumen de Docker) y de forma **idempotente**.
- **Normalización de `title`**: se recorta espacio en los extremos y se rechaza con `422` si no queda ningún carácter visible tras la normalización — la validación es por categoría Unicode (`Cc`, `Cf`, `Zl`, `Zp`, `Zs`), no basta un `strip()` simple (hay invisibles como `U+200B` que lo atraviesan).
- **Orden estable entre llamadas idénticas** es obligatorio en toda colección: `GET /states` por campo de orden del catálogo + `id` como desempate; `GET /projects` y `GET /tasks` por `id` ascendente (incluso con filtros).
- **Borrado de proyecto con tareas** devuelve `409`, nunca cascada implícita. Una referencia a proyecto o estado inexistente al crear una tarea no se crea implícitamente.
- **`due_at`** (tareas v2) es opcional, requiere zona horaria explícita (`422` si no la tiene — nunca se asume una), se normaliza y serializa siempre en UTC con sufijo `Z` y sin microsegundos (`2026-03-01T09:00:00Z`, nunca `+00:00`). `GET /tasks?overdue=true` filtra por `due_at` pasado y estado distinto de `HECHA`; una tarea sin fecha nunca está vencida.
- **Esquemas de respuesta son exactos**: campos declarados, ni uno de más. Un campo opcional ausente se serializa como `null`, nunca se omite. Las colecciones devuelven una lista JSON en la raíz, no un objeto con metadatos envolvente.
- **Forma de error estable**: `{"detail": "<mensaje>"}`; para `422` se admite además la forma que genere el framework siempre que la clave de primer nivel siga siendo `detail`.
- El motor de persistencia decidido es **Postgres** (`compose.yaml`, imagen `postgres:18-alpine`), pero a la fecha de este archivo **aún no hay driver/ORM ni herramienta de migraciones** en `pyproject.toml`/`uv.lock` — es una decisión pendiente, no asumas SQLAlchemy/Alembic u otra alternativa sin confirmarlo.

`docs/onboarding.md` mantiene un mapa más detallado de hechos vs. inferencias vs. desconocidos sobre el estado del repo, con cita de archivo y línea — consúltalo si necesitas verificar algo con evidencia antes de asumirlo.
