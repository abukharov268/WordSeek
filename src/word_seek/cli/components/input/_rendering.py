import math
from os import terminal_size

from curtsies import fmtfuncs as fmt
from curtsies.formatstring import FmtStr, fmtstr

from ....utils import collections
from ._models import SUGGEST_ROWS, InputState


def fmt_input(state: InputState, term: terminal_size) -> list[FmtStr]:
    """Render current state of the input"""

    if state.invalid:
        line = fmt.red(state.value)
    elif 0 <= state.select_index < len(state.suggestions):
        suggestion = state.suggestions[state.select_index]
        prefix = suggestion[0 : max(0, suggestion.find(state.value))]
        suffix = suggestion[len(prefix) + len(state.value) :]
        line = fmt.yellow(prefix) + state.value + fmt.yellow(suffix)
    else:
        line = fmtstr(state.value)

    display_rows = fmt_suggestions(state, term)
    return [line] + display_rows


def highlighted_selection(text: str, value: str) -> FmtStr | str:
    start = text.find(value)
    if start < 0:
        return text

    selection = fmtstr(value, underline=True)
    rest = text[start + len(selection) :]
    return text[:start] + selection + rest


def measure_columns(
    suggestions: list[str], term: terminal_size
) -> list[tuple[list[str], int]]:
    PAD = len("  ")
    BAR = len("│")
    columns = list(collections.chunks(suggestions, SUGGEST_ROWS))
    widths = list(max(map(len, c)) + PAD for c in columns)

    total_width = 2 * BAR
    for i, width in enumerate(widths):
        new_width = total_width + width
        if new_width > term.columns:
            columns = columns[:i]
            widths = widths[:i]
            break
        total_width = new_width

    padding = int(math.floor((term.columns - total_width) / len(widths)))
    last_padding = term.columns - total_width - padding * (len(columns) - 1)
    for i in range(len(widths) - 1):
        widths[i] += padding
    widths[-1] += last_padding

    return list(zip(columns, widths))


def fmt_suggestions(state: InputState, term: terminal_size) -> list[FmtStr]:
    """Prepare list of rows with drawn suggestions"""

    if state.suggestions:
        columns = measure_columns(state.suggestions, term)
        rows = [fmtstr("│")] * len(columns[0][0])
        index = 0
        for col_rows, col_width in columns:
            for i in range(len(rows)):
                cell_str = col_rows[i] if i < len(col_rows) else ""
                cell_str = cell_str.ljust(col_width)
                cell = highlighted_selection(cell_str, state.value)
                rows[i] += fmtstr(cell, invert=index == state.select_index)
                index += 1
        for i in range(len(rows)):
            rows[i] += "│"

        return [
            fmtstr("┌" + "─" * (term.columns - 2) + "┐"),
            *rows,
            fmtstr("└" + "─" * (term.columns - 2) + "┘"),
        ]

    return []
