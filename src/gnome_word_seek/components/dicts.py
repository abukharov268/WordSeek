import asyncio
from collections.abc import Awaitable, Callable
from functools import partial
from importlib import resources
from typing import Self

from word_seek.db import repo
from word_seek.db.models import Dictionary

from .. import res
from ..gnome_libs import Adw, Gtk
from ..typings import preserve_type_decorator


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
    rows: list[Adw.PreferencesRow]
    selected_dict: Dictionary | None = None

    def __init__(self):
        super().__init__()
        self.rows = []
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

            edit_btn = Gtk.Button(
                icon_name="document-edit-symbolic",
                valign=Gtk.Align.CENTER,
                vexpand=False,
            )
            edit_btn.connect("clicked", partial(self.show_editor, row, dct))
            row.add_suffix(edit_btn)
            delete_btn = Gtk.Button(
                icon_name="edit-delete-symbolic",
                valign=Gtk.Align.CENTER,
                vexpand=False,
            )
            delete_btn.connect("clicked", partial(self.confirm_deletion, row, dct))
            row.add_suffix(delete_btn)

        for row in self.rows:
            self.dict_row_group.add(row)

    def show_editor(self, selected_row: Adw.ActionRow, dct: Dictionary, *args) -> None:
        self.dict_sort_entry.set_text(str(dct.sort_order or 1))

        self.dict_view.set_reveal_bottom_bars(True)
        for row in self.rows:
            row.set_sensitive(False)
        selected_row.set_sensitive(True)

        self.selected_dict = dct

    def confirm_deletion(
        self, selected_row: Adw.ActionRow, dct: Dictionary, *args
    ) -> None:
        selected_row.set_sensitive(False)
        dialog = ConfirmDeletionDialog(
            dct, on_deleted=self.populate, on_canceled=self.deselect_rows
        )
        dialog.present(self)

    def on_apply(self, *arg) -> None:
        if not self.selected_dict:
            return
        asyncio.create_task(self.apply(self.selected_dict))

    async def apply(self, dct: Dictionary) -> None:
        order = self.dict_sort_entry.get_value_as_int()
        await repo.sort_dict(dct, order)

        await self.populate()


class ConfirmDeletionDialog(Adw.AlertDialog):
    def __init__(
        self,
        dictinary: Dictionary,
        on_deleted: Callable[[], Awaitable],
        on_canceled: Callable[[], None],
    ) -> None:
        super().__init__(
            heading="Delete Dictionary?",
            body=f'Do you really want to delete "{dictinary.title}" and all its acticles?',
            default_response="cancel",
            close_response="cancel",
        )
        self.add_response("cancel", "_Cancel")
        self.add_response("delete", "_Delete")
        self.set_response_appearance("delete", Adw.ResponseAppearance.DESTRUCTIVE)
        self.connect("response", self.on_delete)
        self.dictionary = dictinary
        self.on_deleted = on_deleted
        self.on_canceled = on_canceled

    def on_delete(self, dialog: Self, response: str, *args) -> None:
        if response == "delete":
            asyncio.create_task(self.delete())
        else:
            self.on_canceled()

    async def delete(self) -> None:
        await repo.delete_dict(self.dictionary)
        await self.on_deleted()
