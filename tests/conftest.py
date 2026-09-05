import pytest
import pytest_asyncio
from alembic.config import Config
from sqlalchemy import text

from alembic import command
from app.db import engine

ALEMBIC_CFG = Config("alembic.ini")


@pytest.fixture(scope="session", autouse=True)
def _migrated_database() -> None:
    command.upgrade(ALEMBIC_CFG, "head")


@pytest_asyncio.fixture(autouse=True)
async def _clean_database() -> None:
    # El pool de asyncpg de `engine` queda atado al event loop que lo usó por
    # última vez; pytest-asyncio puede darle un loop nuevo a cada test, así
    # que hay que soltarlo antes de usarlo en este test.
    await engine.dispose()
    async with engine.begin() as conn:
        await conn.execute(text("truncate table tasks, projects cascade"))
