import asyncio
import os

from curtsies import fmtfuncs as fmt
from curtsies.formatstring import FmtStr, fmtstr
from curtsies.window import CursorAwareWindow

from ....db.models import Article, ArticleFormat
from ....eventsrc.input import InputScope, KeyEvent, SigIntEvent, keys
from ...formats.xdxf import render_xdxf_lines

LINES_PAUSE = 0.2


def render_article_lines(articles: list[Article]) -> list[FmtStr]:
    if not articles:
        lines = [fmt.red("No phrases are found.")]
    else:
        lines = [fmtstr(f"Found {len(articles)} result(s):")]
    for a in articles:
        lines.append(fmtstr(""))
        lines.append(fmtstr(a.dictionary.title, fg="yellow", style="underline"))
        if a.dtype == ArticleFormat.XDXF:
            for line in render_xdxf_lines(a.text):
                lines.append(line)
        else:
            for text_line in a.text.rstrip().splitlines():
                lines.append(fmtstr(text_line))

    return lines


async def print_lines(lines: list[FmtStr]) -> None:
    pause = LINES_PAUSE / max(1, len(lines))
    for line in lines:
        print(line)
        await asyncio.sleep(pause)


async def view(articles: list[Article]) -> None:
    lines = render_article_lines(articles)
    term = os.get_terminal_size()
    scroll_size = term.lines // 2

    await print_lines(lines[:scroll_size])
    rest = lines[scroll_size:]

    while rest:
        with CursorAwareWindow(), InputScope() as key_src:
            key = next(key_src.input())
        match key:
            case keys.ENTER | keys.SPACE:
                await print_lines(rest[:scroll_size])
                rest = rest[scroll_size:]
            case keys.DOWN:
                await print_lines(rest[:1])
                rest = rest[1:]
            case KeyEvent("q") | KeyEvent("Q") | None:
                break
            case SigIntEvent():
                exit(0)
    print()
