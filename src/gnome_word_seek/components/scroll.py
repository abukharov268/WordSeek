from typing import Self
import gi
import asyncio

from ..treeutil import find_near_type

try:
    gi.require_version("Graphene", "1.0")
    gi.require_version("Gtk", "4.0")

    from gi.repository import Gtk, Graphene
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


ANIMATE_RATE = 0.05
ANIMATE_SECS = 0.3


class Scroll:
    def __init__(self, scrollable: Gtk.ScrolledWindow, container: Gtk.Widget) -> None:
        self._scroll = scrollable
        self._container = container
        self._animation: asyncio.Task | None = None

    @classmethod
    def find_in_container(cls, container: Gtk.Widget) -> Self:
        scroll_win = find_near_type(container, Gtk.ScrolledWindow)
        if scroll_win:
            scroll_win.set_propagate_natural_height(True)
            scroll_win.set_kinetic_scrolling(True)
            return cls(scroll_win, container)
        raise TypeError("Can't find a ScrolledWindow of the container")

    async def _animation_loop(
        self, vadj_target: float, frames: int = int(1 / ANIMATE_RATE)
    ) -> None:
        vadj = self._scroll.get_vadjustment()
        while frames > 0:
            rate = 1 / frames
            diff = rate * (vadj_target - vadj.props.value)
            vadj.set_value(vadj.props.value + diff)
            frames -= 1
            await asyncio.sleep(ANIMATE_RATE * ANIMATE_SECS)

    def _stop_animation(self) -> None:
        if self._animation:
            self._animation.cancel()
            self._animation = None

    def _animate_scroll(self, vadj_target: float) -> None:
        self._stop_animation()
        self._animation = asyncio.create_task(self._animation_loop(vadj_target))

    def focus_at_iter(self, view: Gtk.TextView, text_iter: Gtk.TextIter) -> None:
        local_rect = view.get_iter_location(text_iter)
        local_point = Graphene.Point().init(local_rect.x, local_rect.y)

        ok, point = view.compute_point(self._container, local_point)

        if not ok or not point:
            view.grab_focus()
        else:
            vadj = self._scroll.get_vadjustment()
            vadj_target = vadj.get_value() + point.y
            self._animate_scroll(vadj_target)

    def move_page(self, ratio: float = 1.0) -> None:
        vadj = self._scroll.get_vadjustment()
        vadj_target = vadj.get_value() + ratio * vadj.get_page_size()
        self._animate_scroll(vadj_target)

    def move_end(self) -> None:
        vadj = self._scroll.get_vadjustment()
        self._animate_scroll(vadj.get_upper())

    def move_start(self) -> None:
        vadj = self._scroll.get_vadjustment()
        self._animate_scroll(vadj.get_lower())
