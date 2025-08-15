import asyncio
import os
from functools import partial

import reactivex as rx
import reactivex.operators as op
from curtsies.window import CursorAwareWindow

from ....eventsrc.autocomplete import FoundPhrases, PhrasesQuery, create_autocomplete
from ....eventsrc.input import (
    InputEvent,
    KeyEvent,
    PasteEvent,
    SigIntEvent,
    InputScope,
    keys,
)
from ....rxutil import till_complete_async

from . import _rendering as rendering
from ._models import SUGGEST_ROWS, InputState


def is_not_end(key: InputEvent) -> bool:
    return key != keys.ENTER and not isinstance(key, SigIntEvent)


def consume_key_when_enter(state: InputState, key: InputEvent) -> None:
    match key:
        case keys.BACKSPACE:
            if state.value:
                state.place("", -1)
        case keys.TAB if len(state.suggestions):
            state.move_selection(0)
        case keys.RIGHT:
            state.move_cursor(1)
        case keys.LEFT:
            state.move_cursor(-1)
        case keys.SPACE:
            state.place(" ")
        case PasteEvent():
            state.place(key.text())
        case KeyEvent() if key.char:
            state.place(key.char)


def consume_key_when_select(state: InputState, key: InputEvent) -> None:
    match key:
        case keys.ESC:
            state.deselect()
        case keys.RIGHT:
            state.move_selection(SUGGEST_ROWS)
        case keys.LEFT:
            state.move_selection(-SUGGEST_ROWS)
        case keys.UP | keys.SHIFT_TAB:
            state.move_selection(-1)
        case keys.DOWN | keys.TAB:
            state.move_selection(1)
        case keys.ENTER:
            state.value = state.suggestions[state.select_index]
            state.deselect()


def consume_key(state: InputState, key: InputEvent) -> None:
    match key:
        case SigIntEvent():
            state.exited = True

    if state.is_selection():
        consume_key_when_select(state, key)
    else:
        consume_key_when_enter(state, key)


def to_phase_query(state: InputState) -> PhrasesQuery:
    return PhrasesQuery(state.value)


def apply_completion(state: InputState, found: FoundPhrases) -> None:
    state.suggestions = found.suggestions


def render(win: CursorAwareWindow, state: InputState) -> None:
    size = os.get_terminal_size()
    win.render_to_terminal(rendering.fmt_input(state, size), (0, state.cursor_index))


async def input() -> str:
    with CursorAwareWindow(hide_cursor=False) as win, InputScope() as input_src:
        state = InputState()
        suggest_source = rx.Subject[PhrasesQuery]()
        main_pipeline = input_src.observable().pipe(
            op.do_action(partial(consume_key, state)),
            op.take_while(is_not_end),
            op.map(lambda _: state),
            op.do_action(partial(render, win)),
            op.map(to_phase_query),
            op.do_action(
                on_next=suggest_source.on_next,
                on_completed=suggest_source.on_completed,
            ),
            op.ignore_elements(),
        )
        suggest_pipeline = create_autocomplete(suggest_source).pipe(
            op.do_action(partial(apply_completion, state)),
            op.map(lambda _: state),
            op.do_action(partial(render, win)),
            op.ignore_elements(),
        )
        await asyncio.gather(
            till_complete_async(main_pipeline),
            till_complete_async(suggest_pipeline),
        )
        if state.exited:
            exit(0)
        return state.value
