from dataclasses import dataclass


@dataclass(slots=True, frozen=True, eq=True)
class range_lim[T]:
    start: T | None
    end: T | None
