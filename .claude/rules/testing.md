# Tests

## Dónde viven

- Todo test vive en `conftest.py` o en un archivo `test_*.py`, uno por recurso (`test_projects.py`, `test_tasks.py`) o uno por migración (`test_tasks_migration.py`, `test_tasks_due_at_migration.py`).
- Los fixtures de base de datos viven en `conftest.py`; no existe una fixture compartida de cliente HTTP — cada archivo de test de endpoint define su propio `_client()`.

## Cómo se nombran

- Nombre largo y descriptivo, `test_<acción>_<condición>_<resultado>` (ej. `test_patch_task_with_nonexistent_project_returns_422_and_does_not_change_task`), nunca abreviado.
- Un test de migración se nombra por lo que prueba (`test_upgrade_adds_due_at_and_downgrade_drops_it`), nunca por el id de la revisión.

## Preparar y revertir la base entre pruebas

- Una fixture `autouse` de scope `session` corre `alembic upgrade head` una sola vez al empezar la sesión de tests.
- Una fixture `autouse` async trunca las tablas mutables (`tasks`, `projects`, con `cascade`) antes de cada test; las tablas de catálogo (`states`) nunca se truncan.
- Antes de usar `engine` en un test de migración o en la fixture de limpieza, se llama `await engine.dispose()`: el pool de asyncpg queda atado al event loop que lo usó por última vez, y pytest-asyncio puede asignarle uno nuevo a cada test.
- Un test de migración es una función síncrona que despacha `alembic.command.upgrade`/`downgrade` con `asyncio.to_thread(...)` dentro de un `asyncio.run(...)` propio, porque esos comandos abren su propio loop interno y chocarían si se llamaran desde una corrutina.

## Invariantes del contrato que no pueden faltar (Matriz Mínima de Tests)

- Salud.
- CRUD feliz de proyectos y de tareas.
- IDs inexistentes.
- Título vacío y espacios ASCII (los invisibles Unicode son la regresión de la sesión 7, fuera de esta matriz).
- Proyecto o estado inexistente al crear una tarea.
- Borrado de proyecto con tareas responde `409`.
- Filtros solos y combinados.
- Orden estable: dos llamadas idénticas devuelven los ids en la misma posición.
- Esquema de respuesta exacto: los campos declarados, ni uno más.
- Migración desde base vacía y su rollback.
- El catálogo de estados existe tras migrar, y migrar dos veces no lo duplica.
- `due_at` omitido, válido, sin zona, vencido, futuro y tarea hecha.
- `priority` omitido, dentro de rango y fuera de rango.

## Lo que se aprendió a la fuerza

- Un test que prueba un comportamiento no se edita para que un cambio nuevo pase: si el comportamiento acordado cambió, primero se actualiza el contrato y después el test, en un commit separado del que introdujo el cambio.
