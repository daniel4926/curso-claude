import asyncio

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db import engine

ALEMBIC_CFG = Config("alembic.ini")


async def _table_exists() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(text("select to_regclass('public.projects') is not null"))
        return bool(result.scalar())


async def _insert_project_without_description() -> tuple[int, None]:
    async with engine.begin() as conn:
        result = await conn.execute(
            text("insert into projects (name) values ('Casa') returning id, description")
        )
        row = result.one()
        return row.id, row.description


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

    _, description = await _insert_project_without_description()
    assert description is None

    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, "base")
    assert await _table_exists() is False

    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")


def test_upgrade_creates_table_and_downgrade_drops_it() -> None:
    asyncio.run(_scenario())
