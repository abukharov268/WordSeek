import pytest

import aiostardict
from tests.fixtures.dict_files import DictionaryFiles


@pytest.fixture
def simple_dict_info() -> aiostardict.StarDictInfo:
    return aiostardict.StarDictInfo(
        version="2.4.2",
        bookname="simple",
        wordcount=3,
        idxfilesize=39,
        idxoffsetbits=32,
        sametypesequence=[aiostardict.EntryDataType.MEANING],
    )


@pytest.fixture
def simple_dict_entries() -> list[aiostardict.IdxEntry]:
    return [
        aiostardict.IdxEntry(word="hello", offset=0, size=2 * 12),
        aiostardict.IdxEntry(word="hi", offset=2 * 12, size=2 * 6),
        aiostardict.IdxEntry(word="world", offset=2 * (12 + 6), size=2 * 3),
    ]


async def test_read_info(
    simple_dict_file: DictionaryFiles, simple_dict_info: aiostardict.StarDictInfo
) -> None:
    result = await aiostardict.read_info(simple_dict_file.ifo_path)

    assert result == simple_dict_info


async def test_read_indexes(
    simple_dict_file: DictionaryFiles, simple_dict_entries: list[aiostardict.IdxEntry]
) -> None:
    result = await aiostardict.read_indexes(simple_dict_file.idx_path, 32)

    assert result == simple_dict_entries


async def test_iter_dict_entries(
    simple_dict_file: DictionaryFiles,
    simple_dict_info: aiostardict.StarDictInfo,
    simple_dict_entries: list[aiostardict.IdxEntry],
) -> None:
    result = [
        entry
        async for entry in aiostardict.iter_dict_entries(
            simple_dict_file.dict_path,
            simple_dict_entries,
            simple_dict_info.sametypesequence,
        )
    ]
    idx_entries = [entry[0] for entry in result]
    dict_entries = [entry[1] for entry in result]

    assert len(result) == 3
    assert idx_entries == simple_dict_entries
    assert len(dict_entries[0]) == 1
    assert dict_entries[0][0].dtype == aiostardict.EntryDataType.MEANING
    assert dict_entries[0][0].data == "здравствуйте".encode()
    assert len(dict_entries[1]) == 1
    assert dict_entries[1][0].dtype == aiostardict.EntryDataType.MEANING
    assert dict_entries[1][0].data == "привет".encode()
    assert len(dict_entries[2]) == 1
    assert dict_entries[2][0].dtype == aiostardict.EntryDataType.MEANING
    assert dict_entries[2][0].data == "мир".encode()
