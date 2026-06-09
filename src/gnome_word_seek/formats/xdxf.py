import logging
from collections.abc import Mapping

import gi

from word_seek.formats.visitor import XmlNodeVisitor

logger = logging.getLogger()
try:
    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Pango", "1.0")

    from gi.repository import Gdk, Gtk, Pango
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


def parse_rgba(color: str) -> Gdk.RGBA:
    rgba = Gdk.RGBA()
    ok = rgba.parse(color)

    if ok:
        return rgba
    raise ValueError("Incorrect color")


def rgba_delta(c1: Gdk.RGBA, c2: Gdk.RGBA) -> float:
    return (
        (c1.red - c2.red) ** 2
        + (c1.green - c2.green) ** 2
        + (c1.blue - c2.blue) ** 2
        + (c1.alpha - c2.alpha) ** 2
    )


COLORS = [
    parse_rgba("maroon"),
    parse_rgba("green"),
    parse_rgba("navy"),
    parse_rgba("olive"),
]


COLOR_TAGS = [
    (c, Gtk.TextTag(name=f"c{i}", foreground=c.to_string()))
    for i, c in enumerate(COLORS)
]


TAGS = [
    Gtk.TextTag(name="k", weight=600, scale=1.2),
    Gtk.TextTag(name="tr", weight=400),
    Gtk.TextTag(name="sup", scale=0.5, rise=10),
    Gtk.TextTag(name="sub", scale=0.5, rise=-5),
    Gtk.TextTag(name="ex", style=Pango.Style.ITALIC),
    Gtk.TextTag(name="abr", style=Pango.Style.ITALIC, foreground="grey"),
    Gtk.TextTag(name="co", style=Pango.Style.ITALIC, foreground="grey", scale=0.8),
    Gtk.TextTag(
        name="kref",
        underline=Pango.Underline.SINGLE,
        foreground="blue",
    ),
    Gtk.TextTag(
        name="iref",
        style=Pango.Style.ITALIC,
        underline=Pango.Underline.SINGLE,
        foreground="grey",
        scale=0.8,
    ),
    Gtk.TextTag(name="opt", foreground="grey"),
    Gtk.TextTag(name="b", weight=600),
    Gtk.TextTag(name="i", style=Pango.Style.ITALIC),
    Gtk.TextTag(
        name="blockquote",
        left_margin=10,
        indent=5,
        accumulative_margin=True,
    ),
]


def setup_tags(tag_table: Gtk.TextTagTable | None = None) -> Gtk.TextTagTable:
    tag_table = tag_table or Gtk.TextTagTable()

    for tag in TAGS:
        tag_table.add(tag)
    for _, tag in COLOR_TAGS:
        tag_table.add(tag)

    return tag_table


def insert_xdxf_buffer(buffer: Gtk.TextBuffer, content: str) -> None:
    try:
        XdxfVisitor(buffer).visit(f"<root>{content}</root>")
        return
    except Exception as exc:
        logger.error("XDXF display error", exc)

    iter = buffer.get_end_iter()
    buffer.insert(iter, content)


class XdxfVisitor(XmlNodeVisitor):
    def __init__(self, buffer: Gtk.TextBuffer) -> None:
        super().__init__()
        self.buf = buffer

    def visit_tag(self, tag: str, attrs: Mapping[str, str]) -> None:
        start_mark = self.buf.create_mark(
            None, self.buf.get_end_iter(), left_gravity=True
        )

        for t in TAGS:
            match tag:
                case "c":
                    if "c" in attrs:
                        try:
                            color = parse_rgba(attrs["c"])
                            deltas = [
                                (c, rgba_delta(rgb, color)) for rgb, c in COLOR_TAGS
                            ]
                            deltas.sort(key=lambda x: x[1])
                            t, _ = deltas[0]
                        except Exception:
                            pass
                    super().visit_tag(tag, attrs)
                case "rref":
                    break
                case "iref":
                    super().visit_tag(tag, attrs)
                    if "href" in attrs:
                        self.visit_text(" ➤ ")
                        self.visit_text(attrs["href"])
                case t.props.name:
                    super().visit_tag(tag, attrs)
                case _:
                    continue
            self.buf.apply_tag(
                t,
                self.buf.get_iter_at_mark(start_mark),
                self.buf.get_end_iter(),
            )
            self.buf.delete_mark(start_mark)
            break
        else:
            super().visit_tag(tag, attrs)

    def visit_text(self, text: str) -> None:
        end_iter = self.buf.get_end_iter()
        self.buf.insert(end_iter, text)
