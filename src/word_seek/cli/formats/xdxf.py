import logging
from collections import deque
from collections.abc import Mapping
from typing import Any

from curtsies.formatstring import FmtStr, fmtstr
from webcolors import IntegerRGB, hex_to_rgb, name_to_rgb

from ...formats.visitor import XmlNodeVisitor

logger = logging.getLogger()


def parse_rgba(color: str) -> IntegerRGB:
    if "#" in color:
        return hex_to_rgb(color)
    return name_to_rgb(color)


def rgba_delta(c1: str, c2: str) -> float:
    return float(sum((x1 - x2) ** 2 for x1, x2 in zip(parse_rgba(c1), parse_rgba(c2))))


COLORS = [
    "red",
    "green",
    "yellow",
    "blue",
    "magenta",
    "cyan",
]


STYLES: dict[str, dict[str, Any]] = {
    "k": {"bold": True},
    "tr": {"bold": True},
    "sup": {"fg": "red", "bg": "gray"},
    "sub": {"fg": "blue", "bg": "gray"},
    "ex": {"dark": True},
    "abr": {"fg": "yellow", "dark": True},
    "co": {"fg": "gray"},
    "kref": {"fg": "blue", "underline": True},
    "iref": {"fg": "blue", "underline": True},
    "opt": {"fg": "gray"},
    "b": {"bold": True},
    "i": {"dark": True},
}


def render_xdxf_lines(content: str) -> list[FmtStr]:
    try:
        visitor = XdxfVisitor()
        visitor.visit(f"<root>{content}</root>")
        return visitor.lines
    except Exception:
        logger.exception("XDXF display error")
        return [fmtstr(content)]


class XdxfVisitor(XmlNodeVisitor):
    def __init__(self, lines: list[FmtStr] | None = None) -> None:
        super().__init__()

        self.lines = list[FmtStr]() if lines is None else lines
        self.cur = FmtStr()
        self.blockquotes = 0
        self.styles = deque[dict[str, Any]]()

    def visit_tag(self, tag: str, attrs: Mapping[str, str]) -> None:
        style = STYLES.get(tag) or {}
        combined = self.styles[-1].copy() if self.styles else {}
        combined.update(style)
        self.styles.append(combined)

        match tag:
            case "c":
                if "c" in attrs:
                    try:
                        deltas = [(c, rgba_delta(c, attrs["c"])) for c in COLORS]
                        deltas.sort(key=lambda x: x[1])
                        color, _ = deltas[0]
                        combined["fg"] = color
                    except ValueError:
                        pass
                super().visit_tag(tag, attrs)
            case "rref":
                pass
            case "iref":
                super().visit_tag(tag, attrs)
                if "href" in attrs:
                    self.visit_text(" ➤ ")
                    self.visit_text(attrs["href"])
            case "blockquote":
                self.blockquotes += 1
                if self.cur and not self.cur.isspace():
                    self.lines.append(self.cur)
                self.cur = fmtstr("")
                super().visit_tag(tag, attrs)
                self.blockquotes -= 1
            case _:
                super().visit_tag(tag, attrs)

        self.styles.pop()

    def visit_text(self, text: str) -> None:
        lines = text.split("\n")
        style = self.styles[-1].copy() if self.styles else {}
        prev_style = self.styles[-2].copy() if len(self.styles) > 1 else {}
        prefix = fmtstr(
            " " * self.blockquotes if self.blockquotes else "", **prev_style
        )
        if self.cur:
            self.cur += fmtstr(lines[0], **style)
        else:
            self.cur += prefix + fmtstr(lines[0], **style)
        if len(lines) > 1:
            self.lines.append(self.cur)
            for line in lines[1:-1]:
                self.lines.append(prefix + fmtstr(line, **style))
            self.cur = prefix + fmtstr(lines[-1], **style)
