from typing import Self
from collections.abc import Callable
import itertools

import gi

from .scroll import Scroll

try:
    gi.require_version("Gtk", "4.0")

    from gi.repository import Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


TAG_HIGHLIGHT = Gtk.TextTag(
    name="base:highlight",
    foreground="black",
    background="yellow",
)


class TextSearchSelection:
    invalid: bool = True
    empty: bool = True
    text: str | None = None
    _current: tuple[Gtk.TextView, Gtk.TextIter | None, Gtk.TextIter | None] | None = (
        None
    )

    @property
    def active(self) -> bool:
        return not self.invalid and not self.empty

    def __init__(
        self,
        scroll: Scroll,
        views: list[Gtk.TextView],
        on_selected: "Callable[[TextSearchSelection], None]",
    ) -> None:
        self._scroll = scroll
        self._views = views
        self._on_selected = on_selected

    def invalidate(self) -> None:
        self.invalid = True

        for view in self._views:
            buffer = view.get_buffer()
            start = buffer.get_start_iter()
            end = buffer.get_end_iter()
            buffer.remove_tag(TAG_HIGHLIGHT, start, end)

            buffer.delete_selection(True, False)

        self._on_selected(self)

    def search_inplace(self, text: str) -> None:
        self.empty = True
        self.invalid = False
        self.text = text
        self._current = None
        for view in self._views:
            buffer = view.get_buffer()
            buffer.delete_selection(True, False)
            it = buffer.get_start_iter()
            while it:
                occurence = it.forward_search(
                    text, Gtk.TextSearchFlags.CASE_INSENSITIVE
                )
                if not occurence:
                    break

                start, end = occurence
                it = end
                buffer.apply_tag(TAG_HIGHLIGHT, start, end)

                if self.empty:
                    self._current = view, start.copy(), end.copy()
                    buffer.select_range(start, end)
                    self._scroll.focus_at_iter(view, start)
                self.empty = False

        self._on_selected(self)

    def search(self, text: str) -> Self:
        self.invalidate()
        selection = type(self)(self._scroll, self._views, self._on_selected)
        selection.search_inplace(text)
        return selection

    def next(self) -> None:
        self._next()
        self._on_selected(self)

    def prev(self) -> None:
        self._prev()
        self._on_selected(self)

    def _next(self) -> None:
        if not self._current or not self.text or self.invalid:
            return
        cur_view, _, cur_end = self._current

        view_itr = iter(
            itertools.dropwhile(lambda v: v != cur_view, itertools.cycle(self._views))
        )
        for view in view_itr:
            buffer = view.get_buffer()
            it = cur_end or buffer.get_start_iter()

            occurence = it.forward_search(
                self.text, Gtk.TextSearchFlags.CASE_INSENSITIVE
            )
            if not occurence:
                buffer.delete_selection(True, False)
                cur_end = None
                continue
            else:
                start, end = occurence
                self._current = view, start.copy(), end.copy()
                buffer.select_range(start, end)
                self._scroll.focus_at_iter(view, start)
                break

    def _prev(self) -> None:
        if not self._current or not self.text or self.invalid:
            return
        cur_view, cur_start, _ = self._current

        view_itr = iter(
            itertools.dropwhile(
                lambda v: v != cur_view, itertools.cycle(reversed(self._views))
            )
        )
        for view in view_itr:
            buffer = view.get_buffer()
            it = cur_start or buffer.get_end_iter()

            occurence = it.backward_search(
                self.text, Gtk.TextSearchFlags.CASE_INSENSITIVE
            )
            if not occurence:
                buffer.delete_selection(True, False)
                cur_start = None
                continue
            else:
                start, end = occurence
                self._current = view, start.copy(), end.copy()
                buffer.select_range(start, end)
                self._scroll.focus_at_iter(view, start)
                break
