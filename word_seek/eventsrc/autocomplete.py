import asyncio
from async_lru import alru_cache
from dataclasses import dataclass
from reactivex import Observable
from reactivex import operators as op

from ..db import repo
from ..rxutil import async_observable


@dataclass(slots=True, frozen=True)
class PhrasesQuery:
    phrase: str
    limit: int = 50
    offset: int = 0


@dataclass
class FoundPhrases:
    query: PhrasesQuery
    suggestions: list[str]
    has_more: bool


@alru_cache(maxsize=32)
async def find_phrases(query: PhrasesQuery) -> FoundPhrases:
    result = await repo.find_phrases(query.phrase, query.limit + 1, query.offset)

    return FoundPhrases(
        query=query,
        suggestions=[item.text for item in result[: query.limit]],
        has_more=len(result) > query.limit,
    )


def create_autocomplete(query: Observable[PhrasesQuery]) -> Observable[FoundPhrases]:
    loop = asyncio.get_running_loop()

    def query_observable(query: PhrasesQuery) -> Observable[FoundPhrases]:
        return async_observable(find_phrases(query), loop)

    return query.pipe(op.flat_map(query_observable))
