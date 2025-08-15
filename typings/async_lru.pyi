from typing import Callable, Awaitable

def alru_cache[T: Awaitable, **P](
    maxsize: int = 128, typed: bool = False, *, cache_exceptions: bool = True
) -> Callable[[Callable[P, T]], Callable[P, T]]: ...
