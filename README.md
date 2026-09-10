# Curso Claude Code API

API construida con FastAPI, gestionada con [uv](https://docs.astral.sh/uv/) y Python 3.12.

## Puesta en marcha

Ejecuta estos pasos en orden, desde la raíz del repositorio:

1. Instalar las dependencias exactas del lockfile:

   ```sh
   uv sync --frozen
   ```

2. Copiar las variables de entorno de ejemplo y exportarlas en la shell actual.
   Alembic y la API leen `DATABASE_URL` del entorno del proceso, no del
   archivo `.env` directamente, así que este paso se repite en cada terminal
   nueva donde vayas a correr `alembic` o `uvicorn`:

   ```sh
   cp .env.example .env
   set -a && source .env && set +a
   ```

3. Levantar la base de datos:

   ```sh
   docker compose up -d
   ```

4. Aplicar las migraciones:

   ```sh
   uv run alembic upgrade head
   ```

5. Arrancar la API:

   ```sh
   uv run uvicorn app.main:app --reload
   ```

   Verificar en <http://127.0.0.1:8000/health> que responde `{"status": "ok"}`.

6. Probar un endpoint con [`api.http`](api.http): abrirlo con un cliente que
   entienda el formato REST Client (por ejemplo, la extensión REST Client de
   VS Code) y ejecutar sus peticiones en orden, de arriba a abajo — cada una
   se apoya en la respuesta de la anterior. El comportamiento esperado de
   cada endpoint está documentado en [`docs/contrato-api.md`](docs/contrato-api.md).

7. Al terminar, apagar la base de datos:

   ```sh
   docker compose down
   ```

## Pruebas y estilo

```sh
uv run pytest -q        # correr la suite
uv run ruff check .     # revisar el estilo
```

## Migraciones

Con `DATABASE_URL` exportado en el entorno (paso 2) y la base levantada
(paso 3):

```sh
uv run alembic upgrade head    # aplica todas las migraciones pendientes
uv run alembic downgrade base  # revierte todas las migraciones
uv run alembic downgrade -1    # revierte solo la última
```

Cada migración implementa `upgrade` y `downgrade`, y se prueba en ambos
sentidos antes de integrarse.
