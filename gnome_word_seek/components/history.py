import asyncio
from datetime import date, datetime, timezone
from itertools import groupby
from functools import partial
from collections import OrderedDict

import gi

from word_seek.db import repo
from word_seek.db.models import ViewLog
from word_seek.utils.models import range_lim

try:
    gi.require_version("GObject", "2.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    from gi.repository import Adw, GObject, Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


LOG_COUNT = 10_000


def log_day(log: ViewLog) -> date:
    return log.shown_at_utc.replace(tzinfo=timezone.utc).astimezone().date()


class HistoryPage(Adw.PreferencesPage):
    def __init__(self) -> None:
        super().__init__()
        self.groups = list[Adw.PreferencesGroup]()

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST)
    def selected(self, phrase: str) -> None:
        pass

    def load(self) -> None:
        asyncio.create_task(self.populate())

    def clear_page(self) -> None:
        for grp in self.groups:
            self.remove(grp)
        self.groups.clear()

    def on_item_select(self, row: Adw.ActionRow, *args) -> None:
        self.emit("selected", row.props.title)

    def on_delete_items(
        self,
        *args,
        logs: list[ViewLog] | None = None,
        before: datetime | None = None,
    ) -> None:
        asyncio.create_task(self.delete_items(logs, before))

    async def delete_items(
        self,
        logs: list[ViewLog] | None = None,
        before: datetime | None = None,
    ) -> None:
        await repo.clear_view_logs(
            items=logs,
            shown_at_utc=range_lim(None, before) if before else None,
        )
        await self.populate(animate=False)

    async def populate(self, animate: bool = True) -> None:
        logs = await repo.list_view_logs(limit=LOG_COUNT)
        log_days = [(day, list(items)) for day, items in groupby(logs, log_day)]

        self.clear_page()
        pause = 0.1 / (len(log_days) + 1)

        for day, items in log_days:
            grp = Adw.PreferencesGroup(
                vexpand=True, hexpand=True, title=day.strftime("%Y-%m-%d")
            )
            phrase_groups = OrderedDict[str, list[ViewLog]]()
            for log in items:
                if log.phrase.text not in items:
                    phrase_groups[log.phrase.text] = []

                phrase_groups[log.phrase.text].append(log)

            for phrase, items in phrase_groups.items():
                row = Adw.ActionRow(title=phrase, activatable=True)
                btn = Gtk.Button(
                    icon_name="edit-delete-symbolic",
                    valign=Gtk.Align.CENTER,
                    vexpand=False,
                )
                row.add_suffix(btn)
                grp.add(row)

                row.connect("activated", self.on_item_select)
                btn.connect("clicked", partial(self.on_delete_items, logs=items))

            self.add(grp)
            self.groups.append(grp)

            if animate:
                await asyncio.sleep(pause)
