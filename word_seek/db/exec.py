from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import get_db_connection_url
from .models import Base
from .queries import ModifyQuery, Query

engine = create_async_engine(get_db_connection_url(), echo=False, future=True)


def new_session() -> AsyncSession:
    return async_sessionmaker(engine)()


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
