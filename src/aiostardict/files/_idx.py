import gzip
from os import PathLike
from struct import unpack

import anyio

from ..models import IdxEntry, OffsetBits


async def read_indexes(
    file_path: str | PathLike[str], offset_bits: OffsetBits
) -> list[IdxEntry]:
    memory = await _read_idx_bytes(file_path)
    memory_view = memoryview(memory)
    suffix_bytes = offset_bits // 8 + 4
    suffix_format = ">QL" if offset_bits == 64 else ">LL"
    index = 0
    result = []
    while True:
        if index == 0 and memory[:4] == b"\x00\x00\xb4\x97":
            index += 4  # hard-code the case of "mueller" dictionry

        word_end = memory.find(b"\0", index)
        suffix_start = word_end + 1
        end_index = suffix_start + suffix_bytes
        if word_end < 0 or end_index >= len(memory):
            break
        word = str(memory_view[index:word_end], "utf-8")
        tail_memory = memory_view[suffix_start:end_index]
        result.append(IdxEntry(word, *unpack(suffix_format, tail_memory)))
        index = end_index
    return result


async def _read_idx_bytes(file_path: str | PathLike[str]) -> bytes:
    async with await anyio.open_file(file_path, "rb") as file:
        raw_bytes = await file.read()
        if str(file_path).endswith(".gz"):
            return gzip.decompress(raw_bytes)
        else:
            return raw_bytes
