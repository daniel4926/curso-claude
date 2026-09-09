import asyncio

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db import engine

ALEMBIC_CFG = Config("alembic.ini")
PREVIOUS_REVISION = "30937db24e05"


async def _column_exists() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(
            text(
                "select column_name is not null from information_schema.columns "
                "where table_name = 'tasks' and column_name = 'due_at'"
            )
        )
        row = result.first()
        return row is not None


async def _insert_project_and_state() -> tuple[int, int]:
    async with engine.begin() as conn:
        project_id = (
            await conn.execute(text("insert into projects (name) values ('Casa') returning id"))
        ).scalar_one()
        state_id = (
            await conn.execute(text("select id from states order by sort_order limit 1"))
        ).scalar_one()
        return project_id, state_id


async def _scenario() -> None:
    # El pool de asyncpg de `engine` queda atado al event loop que lo usó por
    # última vez; como cada test de migración corre su propio asyncio.run(),
    # hay que soltarlo al empezar para no reusar conexiones de otro loop.
    await engine.dispose()

    # command.upgrade/downgrade corren su propio asyncio.run() interno (ver
    # alembic/env.py), así que se despachan en un hilo aparte para no chocar
    # con el loop de este test.
    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, PREVIOUS_REVISION)
    assert await _column_exists() is False

    project_id, state_id = await _insert_project_and_state()
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "insert into tasks (title, project_id, state_id) "
                "values ('Tarea previa', :project_id, :state_id)"
            ),
            {"project_id": project_id, "state_id": state_id},
        )

    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")
    assert await _column_exists() is True

    async with engine.connect() as conn:
        due_at = (
            await conn.execute(text("select due_at from tasks where title = 'Tarea previa'"))
        ).scalar_one()
    assert due_at is None

    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, PREVIOUS_REVISION)
    assert await _column_exists() is False

    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")


def test_upgrade_adds_due_at_and_downgrade_drops_it() -> None:
    asyncio.run(_scenario())
