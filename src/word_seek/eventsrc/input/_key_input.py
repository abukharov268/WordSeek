import signal
from collections.abc import Callable, Iterator
from contextlib import AbstractContextManager
from threading import Thread
from types import TracebackType
from typing import Self

from curtsies import events
from curtsies.input import Input
from reactivex import Observable, Subject

from .models import InputEvent, KeyEvent, PasteEvent


def map_event(key: str | events.Event | None) -> InputEvent | None:
    match key:
        case str():
            return KeyEvent(key)
        case events.SigIntEvent() | events.ScheduledEvent():
            return key
        case events.PasteEvent():
            keys = [KeyEvent(k) for k in key.events]
            return PasteEvent(keys)
        case _:
            return None


class InputScope(AbstractContextManager["InputScope"]):
    def __init__(self) -> None:
        self._input = Input(sigint_event=True)
        self._prev_sig_handler: Callable[..., None] | signal.Handlers | int | None = (
            None
        )
        self._subject = Subject[InputEvent]()
        self._thread = Thread(target=self._run)

    def _run(self) -> None:
        input = iter(self._input)
        while not self._subject.is_disposed:
            key = input.send(0.1)
            event = map_event(key)
            if event and not self._subject.is_disposed:
                self._subject.on_next(event)

    def _sig_handler(self, *_) -> None:
        self._input.threadsafe_event_trigger(events.SigIntEvent)

    def input(self) -> Iterator[InputEvent]:
        for key in self._input:
            event = map_event(key)
            if event:
                yield event

    def observable(self) -> Observable[InputEvent]:
        if not self._thread.ident:
            self._thread.start()
        return self._subject

    def __enter__(self) -> Self:
        self._input = self._input.__enter__()
        self._prev_sig_handler = signal.signal(signal.SIGINT, self._sig_handler)
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
        /,
    ) -> None:
        if not self._subject.is_disposed:
            self._subject.dispose()

        if self._thread.ident and self._thread.is_alive():
            self._sig_handler()
            self._thread.join()

        signal.signal(signal.SIGINT, self._prev_sig_handler)

        return self._input.__exit__(exc_type, exc_value, traceback)
