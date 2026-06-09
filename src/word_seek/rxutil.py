import asyncio
import weakref
from collections.abc import AsyncIterable, Awaitable, Callable, Coroutine
from typing import Any

from reactivex import Observable
from reactivex.abc import DisposableBase, ObservableBase
from reactivex.scheduler import ThreadPoolScheduler
from reactivex.scheduler.eventloop import AsyncIOThreadSafeScheduler
from reactivex.subject import AsyncSubject


class NullDisposable(DisposableBase):
    def dispose(self) -> None:
        pass


class FlagDisposable(DisposableBase):
    disposed: bool = False

    def dispose(self) -> None:
        self.disposed = True


class TaskDisposable(DisposableBase):
    def __init__(self, task: asyncio.Task) -> None:
        self.task = task

    def dispose(self) -> None:
        self.task.cancel()


class CallbackDisposable(DisposableBase):
    disposed: bool = False

    def __init__(self, callback: Callable[[], None]) -> None:
        self._callback = callback

    def dispose(self) -> None:
        if not self.disposed:
            self.disposed = True
            self._callback()


async def till_complete_async[T](observable: ObservableBase[T]) -> None:
    future = asyncio.Future[None]()
    loop = asyncio.get_running_loop()

    def set_result() -> None:
        loop.call_soon_threadsafe(future.set_result, None)

    with observable.subscribe(
        on_completed=set_result,
        scheduler=AsyncIOThreadSafeScheduler(loop),
    ):
        await future


async def next_async[T](observable: ObservableBase[T]) -> T | None:
    future = asyncio.Future[T]()
    loop = asyncio.get_running_loop()

    def set_result(item: T) -> None:
        if not future.done():
            future.set_result(item)

    def set_error(error: Exception) -> None:
        if not future.done():
            future.set_exception(error)

    def call_threadsafe[R](func: Callable[[R], None], arg: R) -> None:
        loop.call_soon_threadsafe(func, arg)

    with observable.subscribe(
        on_next=lambda item: call_threadsafe(set_result, item),
        on_error=lambda err: call_threadsafe(set_error, err),
        on_completed=lambda: call_threadsafe(set_error, StopAsyncIteration()),
        scheduler=ThreadPoolScheduler(),
    ):
        try:
            return await future
        except StopAsyncIteration:
            return None


async def iterate_async[T](observable: Observable[T]) -> AsyncIterable[T]:
    complete = False
    next_event = asyncio.Event()
    next_items = list[T]()
    err: Exception | None = None

    loop = asyncio.get_running_loop()

    def on_completed() -> None:
        nonlocal complete
        complete = True
        loop.call_soon_threadsafe(next_event.set)

    def on_next(item: T) -> None:
        print("next")
        next_items.append(item)
        loop.call_soon_threadsafe(next_event.set)

    def on_error(error: Exception) -> None:
        nonlocal err
        err = error
        loop.call_soon_threadsafe(next_event.set)

    with observable.subscribe(
        on_next=on_next,
        on_error=on_error,
        on_completed=on_completed,
        scheduler=AsyncIOThreadSafeScheduler(loop),
    ):
        while not complete:
            await next_event.wait()

            for item in next_items:
                yield item
            next_items.clear()
            if err:
                raise err


def async_observable[T](
    awaitable: Awaitable[T] | Coroutine[Any, Any, T],
    loop: asyncio.AbstractEventLoop,
) -> Observable[T]:
    subject = AsyncSubject[T]()
    task_refs = weakref.WeakKeyDictionary[object, asyncio.Task]()

    async def run() -> None:
        try:
            res = await awaitable
            subject.on_next(res)
        except Exception as exc:
            subject.on_error(exc)
            raise
        finally:
            subject.on_completed()

    def start_task() -> None:
        task = loop.create_task(run())
        task_refs[subject] = task

    loop.call_soon_threadsafe(start_task)
    return subject
