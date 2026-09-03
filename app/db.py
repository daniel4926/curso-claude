import os

from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


def _database_url() -> str:
    return os.environ["DATABASE_URL"]


class Base(DeclarativeBase):
    pass


engine: AsyncEngine = create_async_engine(_database_url())

async_session_factory = async_sessionmaker(engine, expire_on_commit=False)
