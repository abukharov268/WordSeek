from collections.abc import Callable


class typearg[*Ts]:
    @classmethod
    def func[U](cls, f: Callable[[*Ts], U], /) -> Callable[[*Ts], U]:
        return f
