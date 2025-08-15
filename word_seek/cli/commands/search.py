from datetime import datetime, timezone

from ...db import repo
from ...db.models import ViewLog
from ..components import input, view


async def enter_search() -> None:
    phrase_txt = await input()
    phrases = await repo.find_phrases(phrase_txt, limit=1)
    phrase = phrases[0] if phrases else None
    time = datetime.now(timezone.utc)
    if phrase:
        articles = await repo.find_articles(phrase)
        log = ViewLog(phrase_id=phrase.id, shown_at_utc=time)
        await repo.update_view_log(log)
    else:
        articles = []
        log = None
    await view(articles)
