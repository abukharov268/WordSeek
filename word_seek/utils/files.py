import hashlib
import anyio

CHECKSUM_CHUNK_SIZE = 4196


async def checksum_file(file_path: str) -> str:
    checksum = hashlib.md5()

    async with await anyio.open_file(file_path, "rb") as file:
        chunk = await file.read(CHECKSUM_CHUNK_SIZE)
        checksum.update(chunk)

    return checksum.hexdigest()
