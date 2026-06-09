from collections.abc import AsyncIterable
from typing import Final

from sqlalchemy import String, bindparam, select
from sqlalchemy.dialects.sqlite import insert
from sqlalchemy.ext.asyncio import AsyncSession

from ..utils.collections import aio_chunks
from .models import Article, ArticleImportItem, Dictionary, Phrase

BATCH_ROWS: Final = 16384


async def _import_batch(
    session: AsyncSession, dict_id: int, batch: list[ArticleImportItem]
) -> None:
    p, phrase_prm = Phrase, bindparam("phrase", type_=String())
    phrases_prms = [{"text": txt} for txt in {item.phrase for item in batch}]
    prm_batch = [
        {
            "dictionary_id": dict_id,
            "phrase": i.phrase,
            "index": i.index,
            "dtype": i.format,
            "text": i.text,
        }
        for i in batch
    ]
    phrase_id_query = select(p.id).where(p.text == phrase_prm).scalar_subquery()

    await session.execute(
        insert(Phrase).on_conflict_do_nothing(index_elements=["text"]),
        phrases_prms,
    )
    await session.execute(
        insert(Article).values(phrase_id=phrase_id_query),
        prm_batch,
    )


async def import_dictionary(
    session: AsyncSession,
    dictionary: Dictionary,
    articles: AsyncIterable[ArticleImportItem],
    batch_row_count: int = BATCH_ROWS,
) -> AsyncIterable[list[ArticleImportItem]]:
    session.add(dictionary)
    await session.flush()
    async for batch in aio_chunks(articles, batch_row_count):
        await _import_batch(session, dictionary.id, batch)
        yield batch
