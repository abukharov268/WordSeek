from datetime import timezone
from itertools import chain

from curtsies.formatstring import FmtStr, fmtstr
from curtsies.window import CursorAwareWindow

from ....db import repo
from ....db.models import ViewLog
from ....eventsrc.input import InputScope, KeyEvent, SigIntEvent, keys

ITEM_COUNT = 10


def render_logs(logs: list[ViewLog], select_idx: int) -> list[FmtStr]:
    lines = list[FmtStr]()
    for idx, log in enumerate(logs):
        date = log.shown_at_utc.replace(tzinfo=timezone.utc).astimezone()
        line = fmtstr(date.strftime("%Y:%m:%d %H:%M:%S | "), "gray") + log.phrase.text
        lines.append(line if idx != select_idx else fmtstr(line, "invert"))
    return lines


async def select_history() -> ViewLog | None:
    skip, idx, logs = -ITEM_COUNT, -1, list[ViewLog]()

    def within_range(idx: int) -> bool:
        return 0 <= idx < min(len(logs), ITEM_COUNT)

    with CursorAwareWindow() as win, InputScope() as key_src:
        for key in chain([...], key_src.input()):
            match key:
                case keys.ENTER | keys.SPACE:
                    break
                case keys.DOWN if within_range(idx + 1) or len(logs) > ITEM_COUNT:
                    idx += 1
                case keys.UP:
                    idx -= 1
                case keys.PAGEDOWN if len(logs) > ITEM_COUNT:
                    idx += ITEM_COUNT
                case keys.PAGEUP:
                    idx -= ITEM_COUNT
                case KeyEvent("q") | KeyEvent("Q") | None:
                    return None
                case SigIntEvent():
                    exit(0)
            if not within_range(idx):
                skip = max(0, skip - ITEM_COUNT) if idx < 0 else skip + ITEM_COUNT
                logs = await repo.list_view_logs(ITEM_COUNT + 1, skip)
                idx = 0
            lines = render_logs(logs[:ITEM_COUNT], idx)
            win.render_to_terminal(lines)

    return logs[idx] if 0 <= idx < len(logs) else None
