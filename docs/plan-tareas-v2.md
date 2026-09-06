# Plan: Tareas v2 (fechas límite)

Plan de incrementos para cerrar la sección **Tareas v2: Fechas Límite** del
contrato. **Tareas v1 ya está completa** en el código (ver "Estado del
repositorio al planificar"); este plan no la modifica, solo añade `due_at` y
el filtro `overdue`. Cada incremento es un commit; al terminar uno se para y
se espera aprobación antes de seguir con el siguiente.

## Fuentes

- `docs/contrato-api.md` (secciones Convenciones, Tareas v1, Tareas v2,
  Esquemas de Respuesta, Matriz Mínima de Tests).
- `docs/decisiones-ingenieria.md`.
- `CLAUDE.md`.
- `README.md`.
- `docs/onboarding.md` (con reservas: describe un estado del repo anterior a
  toda la persistencia; no se usó para ninguna afirmación de código de este
  plan, se contrastó todo contra el repo actual).
- Código actual: `app/models.py`, `app/schemas.py`, `app/routers/tasks.py`,
  `app/db.py`, `alembic/versions/*`, `tests/test_tasks.py`,
  `tests/test_tasks_migration.py`.
- `docs/plan-proyectos.md`, como referencia de formato y de las decisiones ya
  tomadas para Tareas v1 (código `422` para referencia inexistente, filtros
  sin validar existencia, sesión de base por request).

## Fuera de alcance

- Recordatorios, scheduler, zona horaria preferida del usuario y cambio
  automático de estado: el propio contrato los excluye explícitamente
  (`docs/contrato-api.md:118-119`).
- Cualquier cambio a Proyectos o a los endpoints de Tareas v1 ya
  implementados (`POST /tasks`, `GET /tasks` sin `overdue`, `GET/PATCH/DELETE
  /tasks/{id}`, `DELETE /projects/{id}`): ya están completos y probados
  (`docs/plan-proyectos.md`, incrementos 1-9); este plan solo añade el campo
  `due_at` y el filtro `overdue` sobre ellos.
- Implementar `GET /states`: sigue sin existir ningún router de estados
  (`app/main.py:1-7` solo incluye `projects` y `tasks`), pero es un hueco
  preexistente y ajeno a Tareas v2, ya marcado fuera de alcance en
  `docs/plan-proyectos.md`.
- Detección de caracteres invisibles Unicode en `title` (categorías `Cc`,
  `Cf`, `Zl`, `Zp`, `Zs`): el contrato la asigna explícitamente a la sesión 7
  (`docs/contrato-api.md:30-31,157`) y ya quedó fuera de alcance en
  `docs/plan-proyectos.md`. Tareas v2 no toca `title`.
- Autenticación, autorización y cualquier control de acceso: el contrato no
  los menciona.
- Corregir el archivo `d` vacío en la raíz ni el enlace roto a
  `docs/glosario.md#idempotente` (`docs/contrato-api.md:79`): huecos
  preexistentes sin relación con `due_at`.

## Estado del repositorio al planificar

- Rama activa: `feature/tasks`, creada desde `main` (que está al día con
  `origin/main`); árbol de trabajo limpio al momento de planificar.
- **Tareas v1 completa:** `app/routers/tasks.py:1-92` ya implementa `POST
  /tasks` (valida proyecto y estado, `201`), `GET /tasks` (filtros
  `project_id`/`state_id`, solos o combinados, sin `overdue`), `GET
  /tasks/{id}` (`200`/`404`), `PATCH /tasks/{id}` (parcial, valida
  referencias) y `DELETE /tasks/{id}` (`204`). Probado en
  `tests/test_tasks.py` (18 tests) y `tests/test_tasks_migration.py`.
- `app/models.py:23-30`: `Task` tiene `id`, `title`, `description`,
  `project_id`, `state_id`. **No tiene `due_at`.**
- `app/schemas.py:32-65`: `TaskCreate`, `TaskUpdate` y `TaskRead` no declaran
  `due_at`.
- `alembic/versions/30937db24e05_tabla_tasks.py` es la migración de cabecera
  (`head`) de la tabla `tasks`; crea la tabla sin columna `due_at`.
- `pyproject.toml:6-12`: ya incluye `sqlalchemy[asyncio]`, `asyncpg` y
  `alembic`. No hace falta ninguna dependencia nueva: Pydantic v2 (traída por
  FastAPI) ya parsea `datetime` con offset de zona sin librerías adicionales.
- `app/seed_states.py:6`: `STATE_CODES = ("PENDIENTE", "EN_CURSO",
  "BLOQUEADA", "HECHA")`. El contrato fija el código de cada estado pero no
  su `id` (`docs/contrato-api.md:58`); no hay que asumir que `HECHA` tiene un
  `id` concreto.
- No hay ningún endpoint ni columna relacionados con `due_at` en el repo
  actual: es una capacidad enteramente nueva.

## Decisiones

- **Tipo de columna: `TIMESTAMP WITH TIME ZONE`.** SQLAlchemy
  `DateTime(timezone=True)`. PostgreSQL lo normaliza a UTC internamente y
  `asyncpg` devuelve `datetime` *aware* en UTC al leerlo, lo que encaja
  directo con "normalizado a UTC" (`docs/contrato-api.md:111`) sin
  conversión manual en cada lectura.
- **Rechazo de fecha sin zona con un validador Pydantic.** `TaskCreate` y
  `TaskUpdate` revisan `value.tzinfo is None` y lanzan `ValueError`, que
  FastAPI traduce a `422` con la forma de error del framework (admitida por
  el contrato, `docs/contrato-api.md:14-17`). Mismo mecanismo que ya usa
  `_normalize_title` para `title`.
- **Serialización con `field_serializer`.** Convierte a UTC, trunca
  microsegundos y reemplaza el sufijo `+00:00` por `Z`
  (`docs/contrato-api.md:147-148`), para que un `due_at` con cualquier zona
  de entrada (`-03:00`, `Z`, `+02:00`) salga siempre como
  `2026-03-01T09:00:00Z`.
- **Instante de evaluación de `overdue`: reloj del servidor de base de
  datos.** La consulta usa `func.now()` de PostgreSQL en el propio `WHERE`,
  no `datetime.now()` del proceso Python, para no depender de que los
  relojes de la app y la base estén sincronizados.
- **"Distinto de `HECHA`" se resuelve por `code`, no por `id` fijo.** Vía
  subconsulta a `states` filtrando `code == "HECHA"`. El contrato fija el
  código de cada estado pero no su `id` (`docs/contrato-api.md:58`); atarse
  a un `id` concreto asumiría un orden de siembra que el contrato no
  promete.
- **`overdue` solo filtra cuando su valor es exactamente `true`.** El
  contrato únicamente define comportamiento para `overdue=true`
  (`docs/contrato-api.md:115`); omitirlo o mandar `overdue=false` no aplica
  ningún filtro por fecha (no se inventa un filtro inverso que el contrato no
  pide).
- **`overdue=true` se combina por AND con `project_id` y `state_id`.** Igual
  que estos dos ya se combinan entre sí (`docs/contrato-api.md:104`, ya
  implementado en `app/routers/tasks.py:48-60`).
- **`PATCH /tasks/{id}` admite limpiar `due_at` enviando `null`
  explícito.** Mismo patrón que ya permite `TaskUpdate` para `description`
  vía `exclude_unset=True` (`app/routers/tasks.py:73,80-81`): si el campo
  viene en el cuerpo con valor `null`, se aplica; si no viene, se ignora.

## Incrementos

### Incremento 1 — Migración: columna `due_at` en `tasks`

- `app/models.py`: `Task.due_at: Mapped[datetime | None]` con
  `mapped_column(DateTime(timezone=True), nullable=True)`.
- Migración Alembic nueva (`down_revision` = `30937db24e05`, la cabecera
  actual) que añade la columna `due_at` (`TIMESTAMP WITH TIME ZONE`,
  nullable) a `tasks`; `downgrade` la elimina.
- Extiende `tests/test_tasks_migration.py` (mismo patrón de
  `asyncio.to_thread` para `command.upgrade`/`downgrade`): tras `upgrade
  head`, insertar una tarea con `due_at` vía SQL y leerla de vuelta con
  `tzinfo` no nulo; insertar una tarea sin `due_at` sigue funcionando
  (columna nullable); bajar la migración y confirmar que la columna ya no
  existe (`information_schema.columns`); volver a subir.
- **Comprobación:** con la base levantada, `uv run pytest -q
  tests/test_tasks_migration.py` pasa; `uv run alembic downgrade -1` y `uv
  run alembic upgrade head` funcionan en los dos sentidos.

### Incremento 2 — `due_at` en creación y lectura de tareas

- `app/schemas.py`: `TaskCreate` y `TaskRead` ganan `due_at: datetime |
  None`. Validador en `TaskCreate` que rechaza una fecha sin zona
  (`tzinfo is None`) con `422`. `field_serializer` en `TaskRead` que
  convierte a UTC, trunca microsegundos y formatea con `Z` final.
- `app/routers/tasks.py`: `create_task` guarda `due_at` si viene en el
  payload.
- Test que falla primero (`tests/test_tasks.py`): `POST /tasks` sin
  `due_at` responde `201` con `due_at: null`; con `due_at` en una zona
  distinta de UTC (p. ej. `-03:00`) responde `201` con el valor normalizado
  a UTC y formato `...Z` sin microsegundos; con `due_at` sin zona responde
  `422` y no crea la tarea; el esquema de respuesta exacto sigue siendo
  `{id, title, description, project_id, state_id, due_at}`, ni un campo de
  más; `GET /tasks/{id}` devuelve el mismo `due_at` normalizado.
- **Comprobación:** `uv run pytest -q tests/test_tasks.py` pasa junto con el
  resto de la suite; `uv run ruff check .` limpio.

### Incremento 3 — `due_at` en `PATCH /tasks/{id}`

- `app/schemas.py`: `TaskUpdate` gana `due_at: datetime | None`, con el
  mismo validador de zona horaria que `TaskCreate` (solo se aplica cuando el
  valor no es `None`, igual que ya hace `_validate_title` en `TaskUpdate`).
- `app/routers/tasks.py`: `update_task` ya aplica genéricamente cualquier
  campo presente en `exclude_unset=True`; no requiere lógica nueva más allá
  de que `due_at` pase por el validador del esquema.
- Test que falla primero: `PATCH` añade `due_at` a una tarea que no tenía;
  `PATCH` cambia un `due_at` existente por otro; `PATCH` con `due_at` sin
  zona responde `422` y no modifica la tarea (el `due_at` previo se
  mantiene); `PATCH` con `due_at: null` explícito limpia la fecha
  (`due_at` vuelve a `null` en la respuesta y en un `GET` posterior).
- **Comprobación:** `uv run pytest -q tests/test_tasks.py` pasa junto con el
  resto de la suite.

### Incremento 4 — `GET /tasks?overdue=true`

- `app/routers/tasks.py`: `list_tasks` gana el query param `overdue: bool |
  None = None`. Cuando es exactamente `True`, añade al `WHERE`: `due_at IS
  NOT NULL`, `due_at < func.now()` y `state_id != (subconsulta a states por
  code == "HECHA")`. Se combina por `AND` con `project_id`/`state_id` si
  también vienen. Cualquier otro valor (`False` u omitido) no aplica este
  filtro.
- Test que falla primero: una tarea con `due_at` pasado y estado distinto de
  `HECHA` aparece en `overdue=true`; una con `due_at` futuro no aparece; una
  sin `due_at` no aparece; una con `due_at` pasado pero en estado `HECHA` no
  aparece; `overdue=true` combinado con `project_id` o `state_id` devuelve
  la intersección; sin `overdue` o con `overdue=false` la lista no cambia
  respecto al comportamiento ya probado en el Incremento previo (todas las
  tareas, vencidas o no).
- **Comprobación:** `uv run pytest -q` pasa la suite completa; `uv run ruff
  check .` limpio.
