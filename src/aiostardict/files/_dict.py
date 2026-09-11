import operator as op
import zlib
from array import array
from collections.abc import AsyncIterable, Awaitable, Callable, Sequence
from datetime import date
from os import PathLike
from struct import iter_unpack, unpack, unpack_from

import anyio
from anyio import AsyncFile

from ..errors import StarDictError
from ..models import (
    DictEntry,
    DzInfo,
    EntryDataType,
    GzipExtraFlag,
    GzipFlag,
    IdxEntry,
    OperatingSystemType,
    RandomAccessInfo,
)
from ._ifo import parse_entry_type


async def read_dz_info(file_path: str | PathLike[str]) -> DzInfo:
    async with await anyio.open_file(file_path, "rb") as file:
        (
            header,
            compression_method,
            flags_byte,
            modify_word,
            extra_flags_byte,
            os_type_byte,
        ) = unpack("<HBBLBB", await file.read(10))

        if header != 0x8B1F:
            raise StarDictError("Wrong header magic bytes.")

        flags = GzipFlag(flags_byte)
        extra_flags = GzipExtraFlag(extra_flags_byte)
        modify_time = date.fromtimestamp(modify_word)  # noqa: DTZ012
        os_type = OperatingSystemType(os_type_byte)

        xsize, random_access_info = 0, None
        if GzipFlag.EXTRA in flags:
            xsize, random_access_info = await _read_gzip_extra(file)

        file_name_size, file_name = 0, None
        if GzipFlag.NAME in flags:
            file_name_size, file_name = await _read_iso_8859_1(file)

        comment_size, comment = 0, None
        if GzipFlag.COMMENT in flags:
            comment_size, comment = await _read_iso_8859_1(file)

        crc16_size, crc16_value = 0, None
        if GzipFlag.HCRC in flags:
            crc16_size, crc16_value = 2, *unpack("<H", await file.read(2))

        return DzInfo(
            compression_method=compression_method,
            flags=flags,
            modify_time=modify_time,
            extra_flags=extra_flags,
            operating_system_type=os_type,
            random_access_info=random_access_info,
            original_file_name=file_name,
            comment=comment,
            crc16_value=crc16_value,
            header_length=12 + xsize + file_name_size + comment_size + crc16_size,
        )


async def _read_iso_8859_1(file: AsyncFile[bytes]) -> tuple[int, str]:
    str_bytes = array("B")
    read_byte = await file.read1(1)
    while read_byte and read_byte[-1] != 0:
        str_bytes.extend(read_byte)
        read_byte = await file.read1(1)
    return len(str_bytes) + len(read_byte), str(bytes(str_bytes), "iso-8859-1")


async def _read_gzip_extra(
    file: AsyncFile[bytes],
) -> tuple[int, RandomAccessInfo | None]:
    (xsize,) = unpack("<H", await file.read(2))
    xbyte_count = 0
    random_access_info: RandomAccessInfo | None = None
    while xsize and xbyte_count < xsize:
        xheader, info_size = unpack("<2sH", await file.read(4))
        xbyte_count += 4 + info_size
        if xheader != b"RA":
            await file.read(info_size)
            continue
        (xversion,) = unpack("<H", await file.read(2))
        if xversion != 1:
            raise StarDictError("Invalid random access version.")
        chunk_size, chunk_count = unpack("<HH", await file.read(4))

        words = bytearray()
        while len(words) < chunk_count * 2:
            read_bytes = await file.read(chunk_count * 2 - len(words))
            if not read_bytes:
                break
            words += read_bytes

        chunk_seq = iter_unpack("<H", words)
        chunk_lengths = [w for (w,) in chunk_seq]
        random_access_info = RandomAccessInfo(chunk_size, chunk_lengths)
    return xsize, random_access_info


SIZE_PREFIXED_DTYPES = (
    EntryDataType.WAV,
    EntryDataType.PICTURE,
    EntryDataType.EXTENSION,
)


def _parse_dict_entries(
    data: bytes, sametypesequence: list[EntryDataType] | None
) -> list[DictEntry]:
    result = list[DictEntry]()
    oft = 0
    idx = -1
    while oft < len(data):
        idx += 1
        if sametypesequence:
            dtype = sametypesequence[idx]
        else:
            dtype = parse_entry_type(data[oft : oft + 1].decode())
            oft += 1

        if dtype in SIZE_PREFIXED_DTYPES:
            (size,) = unpack_from(">L", data, oft)
            end: int = oft + 4 + size
            result.append(DictEntry(dtype, data[oft + 4 : end]))
        else:
            end = data.find(b"\0", oft)
            if end < 0:
                end = len(data)
            result.append(DictEntry(dtype, data[oft:end]))
        oft = end
    return result


DICT_BUFFER_SIZE = 8388608
DICT_BATCH_SIZE = 1000


async def iter_dict_entries(
    file_path: str,
    indexes: Sequence[IdxEntry],
    sametypesequence: list[EntryDataType] | None,
    batch_size: int = DICT_BATCH_SIZE,
    buffer_size: int = DICT_BUFFER_SIZE,
) -> AsyncIterable[tuple[IdxEntry, list[DictEntry]]]:
    entries = sorted(indexes, key=op.attrgetter("offset"))
    idx = 0
    dz_info = await read_dz_info(file_path) if file_path.endswith(".dz") else None

    async with await anyio.open_file(file_path, "rb", buffering=buffer_size) as file:
        if dz_info:
            if not dz_info.random_access_info:
                raise StarDictError("Missing random access info in .dict.dz file")

            await file.seek(dz_info.header_length)
            read = _to_decommpress_reader(file, dz_info.random_access_info)
        else:
            read = file.read

        for idx in range(0, len(entries), batch_size):
            next_idx = min(idx + batch_size, len(entries))

            if next_idx < len(entries):
                entry_size = entries[next_idx].offset - entries[idx].offset
                raw = b""
                while len(raw) < entry_size:
                    chunk = await read(entry_size - len(raw))
                    if not chunk:
                        break
                    raw += chunk
            else:
                raw = await read(-1)

            for i in range(idx, next_idx):
                start = entries[i].offset - entries[idx].offset
                end = start + entries[i].size
                data = raw[start:end]
                yield (entries[i], _parse_dict_entries(data, sametypesequence))


def _to_decommpress_reader(
    file: AsyncFile[bytes], ra: RandomAccessInfo
) -> Callable[[int], Awaitable[bytes]]:
    decommressor = zlib.decompressobj(wbits=-15)
    eof: bool = False
    tail_size = 0
    next_chunk_idx = 0

    async def read(size: int) -> bytes:
        nonlocal eof, next_chunk_idx, tail_size
        if size > 0:
            compressed_size = 0
            while tail_size < size and next_chunk_idx < len(
                ra.compressed_chunk_lengths
            ):
                compressed_size += ra.compressed_chunk_lengths[next_chunk_idx]
                tail_size += ra.chunk_length
                next_chunk_idx += 1

            chunk = b""
            while not eof and len(chunk) < compressed_size:
                read_bytes = await file.read(compressed_size - len(chunk))
                eof |= not read_bytes
                chunk += read_bytes
            chunk = decommressor.unconsumed_tail + chunk
            res = decommressor.decompress(chunk, size)
            tail_size -= len(res)
            return res
        elif size == -1:
            chunk = decommressor.unconsumed_tail
            if not eof:
                chunk += await file.read(-1)
            eof = True
            return decommressor.decompress(chunk)
        else:
            return b""

    return read


async def read_dict_entries(
    file_path: str | PathLike[str],
    indexes: Sequence[IdxEntry],
    sametypesequence: list[EntryDataType] | None,
) -> list[tuple[IdxEntry, list[DictEntry]]]:
    if str(file_path).endswith(".dz"):
        dz_info = await read_dz_info(file_path)
    else:
        dz_info = None

    result = list[tuple[IdxEntry, list[DictEntry]]]()
    async with await anyio.open_file(file_path, "rb") as file:
        if dz_info:
            await file.seek(dz_info.header_length)
            raw = await file.read()
            data = zlib.decompress(raw, wbits=-15)
        else:
            data = await file.read()

    ascending_indexes = sorted(indexes, key=op.attrgetter("offset"))
    idx = 0
    while idx < len(ascending_indexes):
        idx_entry = ascending_indexes[idx]
        end_offset = idx_entry.offset + idx_entry.size
        entry_bytes = data[idx_entry.offset : end_offset]
        result.append((idx_entry, _parse_dict_entries(entry_bytes, sametypesequence)))
        idx += 1

    return result
