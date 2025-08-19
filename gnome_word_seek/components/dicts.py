import asyncio
import sys
from importlib import resources
from functools import partial

import gi

from word_seek.db.models import Dictionary
from word_seek.db import repo

from .. import res
from ..typings import preserve_type_decorator

try:
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    from gi.repository import Adw, Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    sys.exit(1)


@preserve_type_decorator(
    Gtk.Template(
        string=resources.files(res).joinpath("ui/dictionaries_page.ui").read_text()
    )
)
class DictionariesPage(Adw.NavigationPage):
    __gtype_name__ = "dictionaries_page"

    dict_view: Adw.ToolbarView = Gtk.Template.Child()  # type: ignore[misc]
    dict_row_group: Adw.PreferencesGroup = Gtk.Template.Child()  # type: ignore[misc]
    dict_sort_entry: Gtk.SpinButton = Gtk.Template.Child()  # type: ignore[misc]
    dict_edit_apply_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore[misc]
    dict_edit_cancel_btn: Gtk.Button = Gtk.Template.Child()  # type: ignore[misc]
    rows: list[Adw.PreferencesRow] = []
    selected_dict: Dictionary | None = None

    def __init__(self):
        super().__init__()
        self.dict_edit_apply_btn.connect("clicked", self.on_apply)
        self.dict_edit_cancel_btn.connect("clicked", self.deselect_rows)

    def load(self) -> None:
        asyncio.create_task(self.populate())

    def deselect_rows(self, *args) -> None:
        self.selected_dict = None
        self.dict_view.set_reveal_bottom_bars(False)
        for row in self.rows:
            row.set_sensitive(True)

    async def populate(self) -> None:
        self.deselect_rows()
        dicts = await repo.list_dicts()

        for row in self.rows:
            self.dict_row_group.remove(row)
        self.rows = []

        for dct in dicts:
            row = Adw.ActionRow(title=dct.title, selectable=True)
            self.rows.append(row)

            if dct.sort_order is not None:
                row.set_subtitle(f"№{dct.sort_order}")

            btn = Gtk.Button(
                icon_name="document-edit-symbolic",
                valign=Gtk.Align.CENTER,
                vexpand=False,
            )
            btn.connect("clicked", partial(self.show_editor, row, dct))
            row.add_suffix(btn)

        for row in self.rows:
            self.dict_row_group.add(row)

    def show_editor(self, selected_row: Adw.ActionRow, dct: Dictionary, *args) -> None:
        self.dict_sort_entry.set_text(str(dct.sort_order or 1))

        self.dict_view.set_reveal_bottom_bars(True)
        for row in self.rows:
            row.set_sensitive(False)
        selected_row.set_sensitive(True)

        self.selected_dict = dct

    def on_apply(self, *arg) -> None:
        if not self.selected_dict:
            return
        asyncio.create_task(self.apply(self.selected_dict))

    async def apply(self, dct: Dictionary) -> None:
        order = self.dict_sort_entry.get_value_as_int()
        await repo.sort_dict(dct, order)

        await self.populate()
