from dataclasses import dataclass, field


SUGGEST_ROWS = 5


@dataclass
class InputState:
    cursor_index: int = 0
    value: str = ""
    exited: bool = False
    invalid: bool = False
    suggestions: list[str] = field(default_factory=list)
    suggestions_exhausted: bool = False
    select_index: int = -1

    def is_selection(self) -> bool:
        return self.select_index >= 0

    def move_cursor(self, offset: int):
        self.cursor_index = min(len(self.value), max(0, self.cursor_index + offset))

    def move_selection(self, offset: int):
        self.select_index = min(
            len(self.suggestions) - 1, max(0, self.select_index + offset)
        )
        if self.select_index >= 0:
            self.cursor_index = len(self.suggestions[self.select_index])

    def deselect(self):
        self.select_index = -1
        self.cursor_index = len(self.value)

    def place(self, replacement: str, offset: int = 0, end_offest: int = 0):
        before = self.value[: max(0, self.cursor_index + offset)]
        rest = self.value[max(0, self.cursor_index + end_offest) :]
        self.value = before + replacement + rest
        self.cursor_index = len(self.value) - len(rest)
