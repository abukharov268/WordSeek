import asyncio
from collections.abc import Awaitable, Callable
from typing import cast

from .gnome_libs import Gio, GObject


def wait_gasync[**P](
    operation: Callable[P, None], *args: P.args, **kwargs: P.kwargs
) -> Awaitable[Gio.AsyncResult]:
    future = asyncio.Future[Gio.AsyncResult]()

    def callback(_: GObject.GObject, res: Gio.AsyncResult) -> None:
        future.set_result(res)

    untyped_operation = cast(Callable[..., None], operation)
    untyped_operation(*args, callback=callback, **kwargs)
    return future
