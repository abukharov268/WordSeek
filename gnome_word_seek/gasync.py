import asyncio
import sys
from collections.abc import Awaitable, Callable
from typing import cast

import gi

try:
    gi.require_version("GObject", "2.0")

    from gi.repository import Gio, GObject
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    sys.exit(1)


def wait_gasync[**P](
    operation: Callable[P, None], *args: P.args, **kwargs: P.kwargs
) -> Awaitable[Gio.AsyncResult]:
    future = asyncio.Future[Gio.AsyncResult]()

    def callback(_: GObject.GObject, res: Gio.AsyncResult) -> None:
        future.set_result(res)

    untyped_operation = cast(Callable[..., None], operation)
    untyped_operation(*args, callback=callback, **kwargs)
    return future
