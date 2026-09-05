import asyncio

from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from alembic import command
from app.db import engine

ALEMBIC_CFG = Config("alembic.ini")


async def _table_exists() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(text("select to_regclass('public.tasks') is not null"))
        return bool(result.scalar())


async def _insert_project_and_get_state_id() -> tuple[int, int]:
    async with engine.begin() as conn:
        project_id = (
            await conn.execute(text("insert into projects (name) values ('Casa') returning id"))
        ).scalar_one()
        state_id = (
            await conn.execute(text("select id from states order by sort_order limit 1"))
        ).scalar_one()
        return project_id, state_id


async def _insert_task(project_id: int, state_id: int) -> None:
    async with engine.begin() as conn:
        await conn.execute(
            text(
                "insert into tasks (title, project_id, state_id) "
                "values ('Regar las plantas', :project_id, :state_id)"
            ),
            {"project_id": project_id, "state_id": state_id},
        )


async def _scenario() -> None:
    # El pool de asyncpg de `engine` queda atado al event loop que lo usó por
    # última vez; como cada test de migración corre su propio asyncio.run(),
    # hay que soltarlo al empezar para no reusar conexiones de otro loop.
    await engine.dispose()

    # command.upgrade/downgrade corren su propio asyncio.run() interno (ver
    # alembic/env.py), así que se despachan en un hilo aparte para no chocar
    # con el loop de este test.
    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, "base")
    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")

    assert await _table_exists() is True

    project_id, state_id = await _insert_project_and_get_state_id()
    await _insert_task(project_id, state_id)

    nonexistent_project_id = project_id + 1000
    try:
        await _insert_task(nonexistent_project_id, state_id)
    except IntegrityError:
        pass
    else:
        raise AssertionError("insertar una tarea con project_id inexistente debía fallar")

    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, "base")
    assert await _table_exists() is False

    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")


def test_upgrade_creates_table_with_fk_and_downgrade_drops_it() -> None:
    asyncio.run(_scenario())
