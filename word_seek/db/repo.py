from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.models import range_lim

from . import queries, exec
from .decorators import transact
from .models import Article, Dictionary, Phrase, ViewLog


@transact
async def find_checksum(session: AsyncSession, checksum: str) -> Dictionary | None:
    return await exec.scalar_one_or_none(session, queries.find_checksum(checksum))


@transact
async def find_phrases(
    session: AsyncSession, phrase: str, limit: int = 16, offset: int = 0
) -> list[Phrase]:
    return await exec.scalars_list(session, queries.find_phrase(phrase, limit, offset))


@transact
async def find_articles(session: AsyncSession, phrase: Phrase) -> list[Article]:
    return await exec.scalars_list(session, queries.find_articles(phrase))


@transact
async def list_dicts(session: AsyncSession) -> list[Dictionary]:
    return await exec.scalars_list(session, queries.list_dicts())


@transact
async def list_view_logs(
    session: AsyncSession, limit: int = 16, offset: int = 0
) -> list[ViewLog]:
    return await exec.scalars_list(session, queries.list_view_logs(limit, offset))


@transact
async def update_view_log(session: AsyncSession, log: ViewLog) -> None:
    session.add(log)
    await session.commit()


@transact
async def clear_view_logs(
    session: AsyncSession,
    *,
    items: ViewLog | int | list[ViewLog] | list[int] | None = None,
    shown_at_utc: range_lim[datetime] | datetime | None = None,
) -> None:
    await exec.execute(
        session, queries.delete_view_logs(items=items, shown_at_utc=shown_at_utc)
    )
    await session.commit()
