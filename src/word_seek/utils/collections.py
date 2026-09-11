from collections.abc import AsyncIterable, Iterable


def head[T](seq: Iterable[T]) -> T | None:
    return next(iter(seq), None)


def chunks[T](items: Iterable[T], size: int) -> Iterable[list[T]]:
    chunk: list[T] = []
    for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


async def achunks[T](items: AsyncIterable[T], size: int) -> AsyncIterable[list[T]]:
    chunk: list[T] = []
    async for item in items:
        chunk.append(item)
        if len(chunk) >= size:
            yield chunk
            chunk = []
    if chunk:
        yield chunk


async def aiter_exaust[T](items: AsyncIterable[T]) -> None:
    async for _ in items:
        pass


async def acount[T](items: AsyncIterable[T]) -> int:
    count = 0
    async for _ in items:
        count += 1
    return count
