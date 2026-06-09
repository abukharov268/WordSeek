from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import null

from ..utils.models import range_lim
from . import exec, queries
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
async def sort_dict(
    session: AsyncSession, dictionary: Dictionary | int, order: int
) -> None:
    id = dictionary if isinstance(dictionary, int) else dictionary.id
    target = await session.get_one(Dictionary, id)
    following = await exec.scalars_list(
        session,
        queries.list_dicts().where(
            (Dictionary.id != id)
            & (Dictionary.sort_order != null())
            & (Dictionary.sort_order >= order)
        ),
    )
    target.sort_order = order
    next_order = order + 1
    session.add(target)
    for dct in following:
        if dct.sort_order is None:
            continue
        if dct.sort_order < next_order:
            dct.sort_order = next_order
            session.add(dct)
        next_order = dct.sort_order + 1
    await session.commit()


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
