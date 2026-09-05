# Plan: Proyectos y Tareas v1

Plan de incrementos para implementar la sección **Proyectos** del contrato y,
como dependencia obligatoria de su regla de borrado, la sección **Tareas v1**
(sin `due_at`). Cada incremento es un commit; al terminar uno se para y se
espera aprobación antes de seguir con el siguiente.

## Fuentes

- `docs/contrato-api.md` (secciones Convenciones, Proyectos, Tareas v1,
  Esquemas de Respuesta, Matriz Mínima de Tests).
- `docs/decisiones-ingenieria.md`.
- `CLAUDE.md`.
- `README.md`.
- `docs/onboarding.md` (con reservas: describe un estado del repo anterior a
  la persistencia; se contrastó contra el código actual antes de usarlo, ver
  más abajo).
- Código actual: `app/models.py`, `app/db.py`, `app/main.py`,
  `app/seed_states.py`, `alembic/env.py`, `alembic/versions/*`,
  `tests/test_states_migration.py`.
- `docs/plan-persistencia.md`, como referencia de formato y de la decisión ya
  tomada de driver/capa de acceso (SQLAlchemy async + asyncpg).

## Fuera de alcance

- `due_at` y todo lo de Tareas v2 (`overdue`, recordatorios, scheduler, zona
  preferida del usuario).
- Implementar `GET /states`: la sección Estados del contrato ya está migrada
  en el código (`app/models.py:7-12`, `alembic/versions/00cbe98f3c48_*.py`)
  pero el endpoint no existe todavía (no hay ninguna ruta `/states` en
  `app/main.py`). Es un hueco anterior a este plan y no forma parte de
  Proyectos ni de Tareas v1; los tests de este plan que necesitan un
  `state_id` válido lo obtienen consultando la tabla `states` directamente
  con SQLAlchemy, igual que hace `tests/test_states_migration.py`.
- Detección de caracteres invisibles Unicode en `title` (categorías `Cc`,
  `Cf`, `Zl`, `Zp`, `Zs`). El propio contrato marca esto como una regresión
  que se trabaja explícitamente en la sesión 7, con un título "que parece
  válido y no lo es" (`docs/contrato-api.md:30-31` y `:157`). Este plan
  implementa solo el recorte de espacio y el rechazo de vacío tras el
  recorte (cadena vacía o solo espacios ASCII).
- Autenticación, autorización y cualquier control de acceso: el contrato no
  los menciona.
- Skills, hooks y verificación automatizada del repositorio.
- Corregir el archivo `d` vacío en la raíz ni el enlace roto a
  `docs/glosario.md` (`docs/contrato-api.md:79`): son huecos preexistentes
  sin relación con Proyectos ni Tareas v1.

## Estado del repositorio al planificar

- `app/main.py:1-8`: la única ruta es `GET /health`. No hay routers, no hay
  dependencia de sesión de base de datos para requests, no hay esquemas
  Pydantic en el repo.
- `app/models.py:1-12`: solo existe el modelo `State` (`id`, `code`,
  `sort_order`). No hay modelos `Project` ni `Task`.
- `app/db.py`: define `Base` (DeclarativeBase), `engine` (async, lee
  `DATABASE_URL` del entorno) y `async_session_factory`. No expone todavía
  una función de dependencia (`Depends`) para inyectar una sesión por
  request.
- `app/seed_states.py`: siembra `PENDIENTE`, `EN_CURSO`, `BLOQUEADA`,
  `HECHA` de forma idempotente (`on_conflict_do_nothing`). Reutilizable tal
  cual para obtener un `state_id` válido en tests.
- `alembic/env.py:10-11` importa `Base` y cada modelo nuevo con
  `# noqa: F401` para registrarlo en `Base.metadata` antes de autogenerar
  migraciones; el patrón se repite para `Project` y `Task`.
- `alembic/versions/`: dos revisiones. `3a357a419009` (inicial, sin cambios
  de esquema) y `00cbe98f3c48` (tabla `states` con seed). Sirve de plantilla
  directa para las migraciones de `projects` y `tasks`.
- `tests/`: solo `tests/test_health.py` y `tests/test_states_migration.py`.
  Este último es el patrón a seguir para tests de migración: sube y baja con
  `alembic.command` despachado a un hilo (`asyncio.to_thread`) porque
  `command.upgrade`/`downgrade` corren su propio `asyncio.run()` interno.
- `pyproject.toml:6-12`: ya incluye `sqlalchemy[asyncio]`, `asyncpg` y
  `alembic` como dependencias de producción, y `httpx`, `pytest`,
  `pytest-asyncio`, `ruff` en desarrollo. No hace falta añadir dependencias
  nuevas para Proyectos ni Tareas v1.
- `compose.yaml` y `.env.example` ya definen `DATABASE_URL`; no requieren
  cambios.
- `docs/onboarding.md` describe un estado sin SQLAlchemy/Alembic/driver de
  Postgres (secciones 3 y 5): quedó desactualizado tras
  `ab0e242`/`fa6c881`. No se usó para las afirmaciones de código de esta
  sección; se contrastó contra el repo actual.

## Decisiones

- **Alcance ampliado a Tareas v1.** `DELETE /projects/{id}` debe responder
  `409` si el proyecto tiene tareas (`docs/contrato-api.md:92,94-95`), pero
  no existe tabla de tareas en el repo. Sin ella, el chequeo de "tiene
  tareas" no es implementable ni comprobable con un test real. Se preguntó
  al usuario cómo resolver esta dependencia; decidió ampliar este plan para
  cubrir Proyectos y Tareas v1 completas (sin `due_at`), de modo que el
  `409` se implemente y se pruebe contra un modelo de tareas real desde el
  principio, en vez de dejar una implementación parcial que luego haya que
  rehacer.
- **Código HTTP para referencia inexistente en tareas: `422`.** El contrato
  exige que `POST /tasks` "valida proyecto, estado y título"
  (`docs/contrato-api.md:103`) sin fijar el código para una referencia
  inexistente. Se preguntó al usuario: decidió `422`, tratándolo como
  entrada inválida del cuerpo de la petición, igual que un título vacío, en
  vez de `404` (reservado en este plan para cuando el recurso inexistente es
  el identificado en la propia URL: `GET/PATCH/DELETE /projects/{id}` y
  `GET/PATCH/DELETE /tasks/{id}`). Aplica igual si `PATCH /tasks/{id}`
  cambia `project_id` o `state_id` a un valor inexistente.
- **`GET /tasks` con `project_id` o `state_id` que no existen no valida,
  filtra.** El contrato pide validación explícita solo para `POST /tasks`
  (`docs/contrato-api.md:103`); para el listado solo dice que "admite
  `project_id` y `state_id`, solos o combinados" (`docs/contrato-api.md:104`),
  sin mencionar validación. Un filtro por un id que no existe simplemente no
  encuentra coincidencias: devuelve `200` con lista vacía, no `404` ni `422`.
- **Sin cascada a nivel de esquema.** `tasks.project_id` y `tasks.state_id`
  son claves foráneas sin `ON DELETE CASCADE` (comportamiento por defecto:
  la base rechaza el borrado de una fila referenciada). Esto es consistente
  con "no hay borrado en cascada implícito" (`docs/contrato-api.md:95`): la
  restricción de la base es la red de seguridad; el chequeo explícito en el
  endpoint (incremento 9) es lo que produce el `409` legible en vez de un
  error de integridad crudo.
- **Sesión de base de datos por request.** Se añade una función de
  dependencia en `app/db.py` que abre una sesión con
  `async_session_factory` y la cierra al terminar el request, inyectada con
  `Depends` en cada ruta. Sigue el estilo async ya establecido por
  `app/db.py` y `docs/plan-persistencia.md`.
- **Organización de módulos nueva** (la estructura interna queda abierta por
  contrato, `docs/contrato-api.md:3-4`; esto es una propuesta concreta para
  que el plan sea ejecutable, no una exigencia del contrato): esquemas
  Pydantic en `app/schemas.py`, rutas en `app/routers/projects.py` y
  `app/routers/tasks.py` incluidos con `app.include_router` en
  `app/main.py`, dependencia de sesión en `app/db.py`.
- **Esquemas de respuesta estrictos.** `ProjectRead` y `TaskRead` (Pydantic,
  `from_attributes=True`) declaran exactamente los campos del contrato
  (`docs/contrato-api.md:130-141`) — `description` presente y `null` cuando
  no hay valor, nunca omitido — sin usar los modelos ORM directamente como
  `response_model`.

## Incrementos

### Incremento 1 — Migración de la tabla `projects`

- Modelo `Project` en `app/models.py`: `id` (PK), `name` (`String`, no
  nulo), `description` (`String`, nullable).
- Import en `alembic/env.py` junto al de `State`, para registrar `Project`
  en `Base.metadata`.
- Migración Alembic que crea `projects` con esas columnas; `downgrade` la
  elimina.
- Test de migración (`tests/test_projects_migration.py`, mismo patrón que
  `tests/test_states_migration.py`): subir crea la tabla; insertar un
  proyecto sin `description` vía SQLAlchemy y leerlo de vuelta da
  `description is None`; bajar elimina la tabla.
- **Comprobación:** con la base levantada, `uv run pytest -q
  tests/test_projects_migration.py` pasa; `uv run alembic downgrade -1` y
  `uv run alembic upgrade head` funcionan en los dos sentidos.

### Incremento 2 — `POST /projects` y `GET /projects`

- Dependencia de sesión por request en `app/db.py`.
- Esquemas `ProjectCreate` (`name` obligatorio, `description` opcional) y
  `ProjectRead` (`id`, `name`, `description`) en `app/schemas.py`.
- Router `app/routers/projects.py` con `POST /projects` (`201`) y
  `GET /projects` (`200`, orden por `id` ascendente), incluido en
  `app/main.py`.
- Test que falla primero (`tests/test_projects.py`): `POST /projects` con
  solo `name` responde `201` con `description: null`; con `name` y
  `description` responde `201` con ambos; el cuerpo de la respuesta no trae
  más campos que los del contrato; `GET /projects` tras crear varios
  proyectos los devuelve en orden de `id` ascendente, y dos llamadas
  idénticas dan el mismo orden.
- **Comprobación:** `uv run pytest -q` pasa (incluye `test_health.py`
  sin regresión); `uv run ruff check .` limpio.

### Incremento 3 — `GET /projects/{id}` y `PATCH /projects/{id}`

- Rutas `GET /projects/{id}` (`200` o `404` con
  `{"detail": "<mensaje>"}`) y `PATCH /projects/{id}` (actualización
  parcial de `name` y/o `description`, `200` con el recurso actualizado,
  `404` si el id no existe).
- Test que falla primero: `GET` de un id inexistente da `404` con la forma
  de error del contrato; `PATCH` solo `description` deja `name` intacto y
  viceversa; `PATCH` de un id inexistente da `404`.
- **Comprobación:** `uv run pytest -q tests/test_projects.py` pasa junto con
  el resto de la suite.

### Incremento 4 — Migración de la tabla `tasks` (esquema v1, sin `due_at`)

- Modelo `Task` en `app/models.py`: `id` (PK), `title` (no nulo),
  `description` (nullable), `project_id` (FK a `projects.id`, no nulo, sin
  cascada), `state_id` (FK a `states.id`, no nulo, sin cascada).
- Import en `alembic/env.py` junto a `State` y `Project`.
- Migración que crea `tasks` con esas columnas y claves foráneas;
  `downgrade` la elimina.
- Test de migración (`tests/test_tasks_migration.py`): subir crea la tabla;
  insertar una tarea con `project_id`/`state_id` válidos (creados antes vía
  SQLAlchemy) funciona; insertar con un `project_id` inexistente falla por
  la restricción de clave foránea; bajar elimina la tabla.
- **Comprobación:** con la base levantada, `uv run pytest -q
  tests/test_tasks_migration.py` pasa; `uv run alembic downgrade -1` y
  `uv run alembic upgrade head` funcionan en los dos sentidos.

### Incremento 5 — Normalización y validación de `title`

- Función de normalización (por ejemplo en `app/schemas.py` o un módulo
  propio): recorta espacio de los extremos y rechaza el resultado si queda
  vacío. Solo cubre el caso ASCII (cadena vacía o solo espacios); el caso
  Unicode invisible queda fuera de alcance (ver sección correspondiente).
- Se conecta como validador de `title` en el esquema de creación de tareas
  (usado por el incremento 6).
- Test que falla primero: título vacío da `422`; título de solo espacios
  ASCII da `422`; título con espacio en los extremos se guarda recortado.
- **Comprobación:** `uv run pytest -q` pasa con los tests nuevos de
  normalización.

### Incremento 6 — `POST /tasks`

- Esquemas `TaskCreate` (`title`, `description` opcional, `project_id`,
  `state_id`) y `TaskRead` (`id`, `title`, `description`, `project_id`,
  `state_id` — sin `due_at`, que es de v2) en `app/schemas.py`.
- Router `app/routers/tasks.py` con `POST /tasks`: valida que `project_id`
  exista (si no, `422`), que `state_id` exista (si no, `422`), aplica la
  normalización de `title` del incremento 5, y crea la tarea (`201`).
- Test que falla primero: creación válida da `201` con el esquema exacto
  del contrato; `project_id` inexistente da `422`; `state_id` inexistente
  da `422`; no se crea ninguna fila en ninguno de esos dos casos.
- **Comprobación:** `uv run pytest -q tests/test_tasks.py` pasa junto con el
  resto de la suite; `uv run ruff check .` limpio.

### Incremento 7 — `GET /tasks` con filtros `project_id` y `state_id`

- Ruta `GET /tasks` que admite `project_id` y `state_id` como query params,
  solos o combinados, sin validar su existencia (ver Decisiones). Orden por
  `id` ascendente, también con filtros aplicados.
- Test que falla primero: sin filtros devuelve todas las tareas ordenadas
  por `id`; con `project_id` devuelve solo las de ese proyecto; con
  `state_id` devuelve solo las de ese estado; con ambos combinados,
  la intersección; con un `project_id` inexistente, lista vacía (`200`);
  dos llamadas idénticas devuelven el mismo orden.
- **Comprobación:** `uv run pytest -q tests/test_tasks.py` pasa.

### Incremento 8 — `GET /tasks/{id}`, `PATCH /tasks/{id}` y `DELETE /tasks/{id}`

- `GET /tasks/{id}`: `200` o `404`.
- `PATCH /tasks/{id}`: actualización parcial; si el cuerpo trae `title`,
  aplica la misma normalización del incremento 5; si trae `project_id` o
  `state_id`, valida su existencia igual que `POST /tasks` (`422` si no
  existen); `404` si el id de la tarea no existe.
- `DELETE /tasks/{id}`: `204` sin cuerpo si existe; `404` si no.
- Test que falla primero para cada caso, incluyendo que `PATCH` con
  `project_id` inexistente no modifica la tarea.
- **Comprobación:** `uv run pytest -q tests/test_tasks.py` pasa junto con el
  resto de la suite.

### Incremento 9 — `DELETE /projects/{id}` con el chequeo real de tareas

- Ruta `DELETE /projects/{id}`: `404` si el proyecto no existe; si existe,
  consulta si hay alguna tarea con ese `project_id`; de haberla, `409` con
  `{"detail": "<mensaje>"}` y no borra nada; si no hay ninguna, borra el
  proyecto y responde `204` sin cuerpo.
- Test que falla primero: proyecto sin tareas se borra con `204`; proyecto
  con una tarea da `409`, y tanto el proyecto como la tarea siguen
  existiendo después; borrar primero la tarea y después el proyecto da
  `204`.
- **Comprobación:** `uv run pytest -q` pasa la suite completa; `uv run ruff
  check .` limpio.
