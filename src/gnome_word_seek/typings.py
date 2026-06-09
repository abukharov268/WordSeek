from collections.abc import Callable
from typing import Any


def preserve_type_decorator[T](decorator: Callable[[T], Any]) -> Callable[[T], T]:
    def casted(target: T) -> T:
        return decorator(target)

    return casted
