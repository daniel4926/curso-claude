# Convenciones de la API

Aplica a `app/routers/` — con una excepción: `GET /health` vive directamente
en `app/main.py:10`, no en un router.

## Esquema de respuesta exacto

- Toda ruta declara `response_model` con un esquema `*Read` de `app/schemas.py`; el cuerpo de la respuesta trae exactamente esos campos, ni uno de más ni uno de menos (`docs/contrato-api.md:121-124`).
- Un campo opcional ausente se serializa como `null`, nunca se omite del cuerpo.

## Código de estado por tipo de error

- `404` — el recurso identificado en la propia URL no existe: `GET/PATCH/DELETE /projects/{id}`, `GET/PATCH/DELETE /tasks/{id}` (`app/routers/projects.py:12-16`, `app/routers/tasks.py:26-30`).
- `409` — un conflicto de negocio, no una entrada inválida: `DELETE /projects/{id}` cuando el proyecto tiene tareas asociadas (`app/routers/projects.py:61-67`).
- `422` — una referencia o un valor del cuerpo de la petición es inválido: `project_id`/`state_id` inexistente en `POST`/`PATCH /tasks`, título vacío o solo espacios ASCII, `due_at` sin zona horaria, `priority` fuera de `1`-`5` (`app/routers/tasks.py:35-36,86-89`, `app/schemas.py`).
- Nunca se usa `404` para una referencia inválida dentro del cuerpo (eso es `422`), ni `422` para el recurso identificado en la URL cuando no existe (eso es `404`).

## Colecciones

- `GET` de colección (`GET /projects`, `GET /tasks`) devuelve una lista JSON en la raíz, nunca un objeto envolvente con metadatos.
- El orden es estable entre llamadas idénticas: por `id` ascendente, incluso con filtros aplicados (`app/routers/projects.py:32`, `app/routers/tasks.py:58`).

## Un campo nuevo se agrega en tres capas

- Migración: la columna se agrega en `alembic/versions/`, nullable, sin tocar las filas existentes.
- Esquema: el campo se agrega a `Create`, `Update` y `Read` en `app/schemas.py`, con su validación declarada ahí mismo (`field_validator` para normalización, `Field(ge=..., le=...)` para rangos).
- Endpoint: el valor se pasa explícitamente al crear el recurso en `app/routers/`; un `PATCH` no necesita tocarse porque ya aplica `model_dump(exclude_unset=True)` de forma genérica.
- Las tres capas van en el mismo commit: un modelo sin su router, o un esquema sin su migración, no es un estado comprobable.
