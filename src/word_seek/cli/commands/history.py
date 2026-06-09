from datetime import datetime, timedelta, timezone
from curtsies.formatstring import fmtstr

from ...utils.models import range_lim

from ...db import repo
from ..components import select_history, view


async def browse_history() -> None:
    log = await select_history()
    if log:
        articles = await repo.find_articles(log.phrase)
        await view(articles)


async def clear_history() -> None:
    await repo.clear_view_logs()
    print(fmtstr("All history is cleared!", fg="red"))


async def flush_history() -> None:
    end = datetime.now(timezone.utc) + timedelta(days=90)
    await repo.clear_view_logs(shown_at_utc=range_lim(None, end))
    print(fmtstr("Old history is cleared!", fg="yellow", dark=True))
