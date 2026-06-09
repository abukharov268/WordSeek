from typing import NamedTuple
from curtsies.events import SigIntEvent, ScheduledEvent


class KeyEvent(NamedTuple):
    code: str

    @property
    def char(self) -> str:
        return self.code if len(self.code) == 1 else ""


class PasteEvent(NamedTuple):
    keys: list[KeyEvent]

    def text(self) -> str:
        return "".join(
            k.char or " " for k in self.keys if k.char or k.code == "<SPACE>"
        )


type InputEvent = KeyEvent | PasteEvent | ScheduledEvent | SigIntEvent

__all__ = ["InputEvent", "KeyEvent", "PasteEvent", "ScheduledEvent", "SigIntEvent"]
