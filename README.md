# Curso Claude Code API

API construida con FastAPI, gestionada con [uv](https://docs.astral.sh/uv/) y Python 3.12.

## Recorrido

1. Instalar las dependencias exactas del lockfile:

   ```sh
   uv sync --frozen
   ```

2. Ejecutar las pruebas:

   ```sh
   uv run pytest -q
   ```

3. Revisar el estilo con Ruff:

   ```sh
   uv run ruff check .
   ```

4. Levantar la base de datos:

   ```sh
   docker compose up -d
   ```

5. Arrancar la API con Uvicorn:

   ```sh
   uv run uvicorn app.main:app --reload
   ```

   Verificar en <http://127.0.0.1:8000/health> que responde `{"status": "ok"}`.

6. Al terminar, apagar la base de datos:

   ```sh
   docker compose down
   ```

## Configuración

`compose.yaml` funciona con valores locales por defecto sin necesitar un `.env`.
Para personalizarlos, copia `.env.example` a `.env` y ajusta los valores.
