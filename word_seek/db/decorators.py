from collections.abc import AsyncIterable, Awaitable, Callable
from functools import wraps
from typing import Concatenate

from sqlalchemy.exc import DatabaseError, OperationalError
from sqlalchemy.ext.asyncio import AsyncSession

from .exec import new_session


class transact[**P, Res]:
    def __init__(
        self, orig_func: Callable[Concatenate[AsyncSession, P], Awaitable[Res]]
    ) -> None:
        self._orig_func = orig_func
        self._tx_func = _make_transact(orig_func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[Res]:
        return self.transact(*args, **kwargs)

    def transact(self, *args: P.args, **kwargs: P.kwargs) -> Awaitable[Res]:
        return self._tx_func(*args, **kwargs)

    def in_session(
        self, session: AsyncSession, *args: P.args, **kwargs: P.kwargs
    ) -> Awaitable[Res]:
        return self._orig_func(session, *args, **kwargs)


class transact_iter[**P, Res]:
    def __init__(
        self, orig_func: Callable[Concatenate[AsyncSession, P], AsyncIterable[Res]]
    ) -> None:
        self._orig_func = orig_func
        self._tx_func = _make_transact_iter(orig_func)

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> AsyncIterable[Res]:
        return self.transact(*args, **kwargs)

    def transact(self, *args: P.args, **kwargs: P.kwargs) -> AsyncIterable[Res]:
        return self._tx_func(*args, **kwargs)

    def in_session(
        self, session: AsyncSession, *args: P.args, **kwargs: P.kwargs
    ) -> AsyncIterable[Res]:
        return self._orig_func(session, *args, **kwargs)


def _make_transact[**P, Res](
    query: Callable[Concatenate[AsyncSession, P], Awaitable[Res]],
) -> Callable[P, Awaitable[Res]]:
    @wraps(query)
    async def decorated(*args: P.args, **kwargs: P.kwargs) -> Res:
        async with new_session() as session:
            return await query(session, *args, **kwargs)

    return decorated


def _make_transact_iter[**P, Res](
    query: Callable[Concatenate[AsyncSession, P], AsyncIterable[Res]],
) -> Callable[P, AsyncIterable[Res]]:
    @wraps(query)
    async def decorated(*args: P.args, **kwargs: P.kwargs) -> AsyncIterable[Res]:
        async with new_session() as session:
            async for item in query(session, *args, **kwargs):
                yield item

    return decorated


def retry_on_transient[**P, Res](
    count: int,
    errors: type[Exception] | tuple[type[Exception], ...] = (
        DatabaseError,
        OperationalError,
    ),
) -> Callable[[Callable[P, Awaitable[Res]]], Callable[P, Awaitable[Res]]]:
    def decorator(func: Callable[P, Awaitable[Res]]) -> Callable[P, Awaitable[Res]]:
        @wraps(func)
        async def decorated(*args: P.args, **kwargs: P.kwargs) -> Res:
            attempts = count
            while True:
                try:
                    return await func(*args, **kwargs)
                except errors:
                    attempts -= 1
                    if attempts:
                        continue
                    raise

        return decorated

    return decorator
