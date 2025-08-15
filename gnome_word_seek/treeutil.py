from collections.abc import Callable

import gi

try:
    gi.require_version("Gtk", "4.0")

    from gi.repository import Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


def find_near_widget(
    widget: Gtk.Widget, predicate: Callable[[Gtk.Widget], bool]
) -> Gtk.Widget | None:
    widgets, next_widgets = [widget], list[Gtk.Widget]()
    while widgets:
        for w in widgets:
            if predicate(w):
                return w
            nxt = w.get_first_child()
            while nxt:
                next_widgets.append(nxt)
                nxt = nxt.get_next_sibling()
        widgets, next_widgets = next_widgets, []

    return None


def find_near_type[T](widget: Gtk.Widget, widget_type: type[T]) -> T | None:
    result = find_near_widget(widget, lambda w: isinstance(w, widget_type))
    if isinstance(result, widget_type):
        return result
    return None


def is_descendant(widget: Gtk.Widget | None, root: Gtk.Widget) -> bool:
    while widget:
        if widget == root:
            return True
        widget = widget.get_parent()
    return False
