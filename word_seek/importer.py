from dataclasses import dataclass
from enum import StrEnum
from os import PathLike
from collections.abc import AsyncIterable

from anyio import Path

import aiostardict
from aiostardict import StarDictFileCollection
from aiostardict.models import StarDictFiles, EntryDataType, IdxEntry, DictEntry

from .db import repo
from .db.config import new_session
from .db.imports import import_dictionary
from .db.models import ArticleImportItem, Dictionary, ArticleFormat
from .utils.collections import aio_count
from .utils.files import checksum_file


class ProgressCategory(StrEnum):
    OK = "ok"
    WARN = "warn"
    ERROR = "error"
    SKIP = "skip"


@dataclass(slots=True)
class ImportProgress:
    category: ProgressCategory
    name: str
    total: int
    num: int
    msg: str


async def bulk_import(dir_path: str | PathLike[str]) -> AsyncIterable[ImportProgress]:
    dir = Path(dir_path)
    stardicts = StarDictFileCollection()
    async for path in dir.glob("**/*.*"):
        stardicts.filter_path_in(path)

    stard_items = list(stardicts)
    for stard_num, stard_item in enumerate(stard_items, 1):
        name, cnt, bad_formats = await _import_item(stard_item)
        ctg, msg = _map_progess_category(cnt, bad_formats)
        yield ImportProgress(ctg, name, len(stard_items), stard_num, msg)


def _map_progess_category(
    cnt: int | None, bad_formats: set[str]
) -> tuple[ProgressCategory, str]:
    match cnt:
        case None:
            ctg, msg = ProgressCategory.SKIP, "Skip existing dictionary."
        case 0 if bad_formats:
            ctg = ProgressCategory.ERROR
            msg = f"No data imported. Unsupported formats: {', '.join(bad_formats)}."
        case 0:
            ctg, msg = ProgressCategory.ERROR, "No data imported."
        case _ if bad_formats:
            ctg = ProgressCategory.WARN
            msg = f"Some formats are unsupported: {', '.join(bad_formats)}."
        case _:
            ctg = ProgressCategory.OK
            msg = "Successful import."
    return ctg, msg


async def _map_dict_entries(
    dict_entries: AsyncIterable[tuple[IdxEntry, list[DictEntry]]],
    error_formats: set[str],
) -> AsyncIterable[ArticleImportItem]:
    async for ientry, entries in dict_entries:
        for idx, entry in enumerate(entries):
            match entry.dtype:
                case EntryDataType.XDXF:
                    format = ArticleFormat.XDXF
                case EntryDataType.MEANING:
                    format = ArticleFormat.TEXT
                case _:
                    error_formats.add(entry.dtype.value)
                    continue
            yield ArticleImportItem(
                phrase=ientry.word, index=idx, format=format, text=entry.data.decode()
            )


async def _import_item(item: StarDictFiles) -> tuple[str, int | None, set[str]]:
    error_formats = set[str]()
    checksum = await checksum_file(item.dict)
    existing = await repo.find_checksum(checksum)
    if existing:
        return existing.title, None, error_formats

    ifo = await aiostardict.read_info(item.ifo)
    indexes = await aiostardict.read_indexes(item.idx, ifo.idxoffsetbits)
    dict_entries = aiostardict.iter_dict_entries(
        item.dict, indexes, ifo.sametypesequence
    )
    articles = _map_dict_entries(dict_entries, error_formats)
    async with new_session() as session:
        cnt = await aio_count(
            import_dictionary(
                session, Dictionary(title=ifo.bookname, checksum=checksum), articles
            )
        )
        if cnt:
            await session.commit()
    return ifo.bookname, cnt, error_formats
