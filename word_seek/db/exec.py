from sqlalchemy.ext.asyncio import AsyncSession

from .models import Base
from .queries import Query, ModifyQuery


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
