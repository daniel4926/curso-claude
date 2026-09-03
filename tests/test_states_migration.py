import asyncio

from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db import engine
from app.seed_states import STATE_CODES, seed_states

ALEMBIC_CFG = Config("alembic.ini")


async def _table_exists() -> bool:
    async with engine.connect() as conn:
        result = await conn.execute(text("select to_regclass('public.states') is not null"))
        return bool(result.scalar())


async def _fetch_states() -> list[tuple[str, int]]:
    async with engine.connect() as conn:
        result = await conn.execute(
            text("select code, sort_order from states order by sort_order, id")
        )
        return [(row.code, row.sort_order) for row in result.all()]


async def _seed_twice_and_count() -> int:
    async with engine.begin() as conn:
        await conn.run_sync(seed_states)
        await conn.run_sync(seed_states)
        result = await conn.execute(text("select count(*) from states"))
        return result.scalar_one()


async def _scenario() -> None:
    # command.upgrade/downgrade corren su propio asyncio.run() interno (ver
    # alembic/env.py), así que se despachan en un hilo aparte para no chocar
    # con el loop de este test.
    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, "base")
    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")

    assert await _table_exists() is True
    assert await _fetch_states() == list(zip(STATE_CODES, range(1, 5), strict=True))

    assert await _seed_twice_and_count() == len(STATE_CODES)

    await asyncio.to_thread(command.downgrade, ALEMBIC_CFG, "base")
    assert await _table_exists() is False

    await asyncio.to_thread(command.upgrade, ALEMBIC_CFG, "head")


def test_upgrade_seeds_catalog_and_downgrade_drops_table() -> None:
    asyncio.run(_scenario())
