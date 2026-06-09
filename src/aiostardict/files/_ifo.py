from os import PathLike

import anyio

from ..errors import StarDictError
from ..models import (
    IFO_AUTHOR,
    IFO_BOOKNAME,
    IFO_DATE,
    IFO_DESCRIPTION,
    IFO_DICTTYPE,
    IFO_EMAIL,
    IFO_IDXFILESIZE,
    IFO_IDXOFFSETBITS,
    IFO_MAGIC_STRING,
    IFO_SAMETYPESEQUENCE,
    IFO_SYNWORDCOUNT,
    IFO_VERSION,
    IFO_WEBSITE,
    IFO_WORDCOUNT,
    EntryDataType,
    OffsetBits,
    StarDictInfo,
    Version,
)


async def read_info(file_path: str) -> StarDictInfo:
    """Read info from .ifo file."""

    items = await _read_info_items(file_path)
    get = items.get

    return StarDictInfo(
        version=_parse_version(get(IFO_VERSION)),
        bookname=_parse_bookname(get(IFO_BOOKNAME)),
        wordcount=_parse_wordcount(get(IFO_WORDCOUNT)),
        synwordcount=_parse_synwordcount(get(IFO_SYNWORDCOUNT)),
        idxfilesize=_parse_idxfilesize(get(IFO_IDXFILESIZE)),
        idxoffsetbits=_parse_idxoffsetbits(get(IFO_IDXOFFSETBITS)),
        author=get(IFO_AUTHOR),
        email=get(IFO_EMAIL),
        website=get(IFO_WEBSITE),
        description=get(IFO_DESCRIPTION),
        date=get(IFO_DATE),
        sametypesequence=parse_entry_typesequence(get(IFO_SAMETYPESEQUENCE)),
        dicttype=get(IFO_DICTTYPE),
    )


def parse_entry_type(value: str) -> EntryDataType:
    try:
        return EntryDataType(value)
    except ValueError:
        raise StarDictError("Unknown dict entry data type.")


def parse_entry_typesequence(value: str | None) -> list[EntryDataType] | None:
    if not value:
        return None
    return [parse_entry_type(ch) for ch in value]


async def _read_info_items(file_path: str | PathLike[str]) -> dict[str, str]:
    async with await anyio.open_file(file_path, "r") as file:
        leading_line = await file.readline()

        if leading_line != IFO_MAGIC_STRING:
            raise StarDictError("The file is of unknown format.")

        items: dict[str, str] = {}
        for line in await file.readlines():
            name, value = line.split("=", maxsplit=1)
            items[name] = value[:-1] if value and value[-1] == "\n" else value

        return items


def _parse_version(value: str | None) -> Version:
    match value:
        case "2.4.2" | "3.0.0":
            return value
        case _:
            raise StarDictError("Invalid version.")


def _parse_bookname(value: str | None) -> str:
    if value is None:
        raise StarDictError("'bookname' is expected.")
    return value


def _parse_wordcount(value: str | None) -> int:
    match value:
        case None:
            raise StarDictError("'wordcount' is expected.")
        case str() if str.isdecimal(value):
            return int(value)
        case _:
            raise StarDictError("Invalid wordcount format.")


def _parse_synwordcount(value: str | None) -> int | None:
    match value:
        case None:
            return None
        case str() if str.isdecimal(value):
            return int(value)
        case _:
            raise StarDictError("Invalid 'synwordcount' format.")


def _parse_idxfilesize(value: str | None) -> int:
    match value:
        case None:
            raise StarDictError("'idxfilesize' is expected.")
        case str() if str.isdecimal(value):
            return int(value)
        case _:
            raise StarDictError("Invalid 'idxfilesize' format.")


def _parse_idxoffsetbits(value: str | None) -> OffsetBits:
    match value:
        case "32" | None:
            return 32
        case "64":
            return 64
        case _:
            raise StarDictError("Invalid offset bits size.")
