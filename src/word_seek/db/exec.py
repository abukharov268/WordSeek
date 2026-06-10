from functools import cache

import aiosqlite
import sqlalchemy.event
import sqlite_icu
from sqlalchemy import AdaptedConnection
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.pool import ConnectionPoolEntry
from sqlalchemy.util.concurrency import await_only

from .config import get_db_connection_url
from .models import Base
from .queries import ModifyQuery, Query


@cache
def engine() -> AsyncEngine:
    engine = create_async_engine(get_db_connection_url(), echo=False, future=True)

    async def load_extensions(connection: aiosqlite.Connection) -> None:
        await connection.enable_load_extension(True)
        await connection.load_extension(sqlite_icu.extension_path().replace(".so", ""))

    @sqlalchemy.event.listens_for(engine.sync_engine, "connect")
    def _config_sqlite(
        dbapi_connection: AdaptedConnection, connection_record: ConnectionPoolEntry
    ) -> None:
        await_only(load_extensions(dbapi_connection.driver_connection))

    return engine


def new_session() -> AsyncSession:
    return async_sessionmaker(engine())()


async def scalar[T: Base](session: AsyncSession, query: Query[T]) -> T | None:
    return await session.scalar(query)


async def scalar_one[T](session: AsyncSession, query: Query[T]) -> T:
    res = await session.execute(query)
    return res.scalar_one()


async def scalar_one_or_none[T: Base](
    session: AsyncSession, query: Query[T]
) -> T | None:
    res = await session.execute(query)
    return res.scalar_one_or_none()


async def scalars_list[T](session: AsyncSession, query: Query[T]) -> list[T]:
    res = await session.scalars(query)
    return list(res.all())


async def execute(session: AsyncSession, query: ModifyQuery) -> None:
    await session.execute(query)
