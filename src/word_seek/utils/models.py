from dataclasses import dataclass
from typing import Self


class RangeLimAtStart:
    __slots__ = ()
    _inst: Self | None = None

    def __new__(cls) -> Self:
        if not cls._inst:
            cls._inst = super().__new__(cls)
        return cls._inst


@dataclass(slots=True, frozen=True, eq=True, init=False)
class range_lim[T]:
    start: T | None
    end: T | None

    def __init__(
        self,
        start: T | None = None,
        end: T | None | RangeLimAtStart = RangeLimAtStart(),
    ) -> None:
        object.__setattr__(self, "start", start)
        object.__setattr__(
            self, "end", start if isinstance(start, RangeLimAtStart) else end
        )
