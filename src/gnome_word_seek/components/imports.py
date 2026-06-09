import asyncio
import sys
from importlib import resources

import gi

from word_seek import importer
from word_seek.importer import ProgressCategory

from .. import res
from ..typings import preserve_type_decorator
from ..gasync import wait_gasync

try:
    gi.require_version("GLib", "2.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    from gi.repository import Adw, Gtk, GLib
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    sys.exit(1)

DEFAULT_TAG = Gtk.TextTag(name=ProgressCategory.OK.value, scale=0.8)
TAGS = {
    tag.props.name: tag
    for tag in (
        DEFAULT_TAG,
        Gtk.TextTag(name=ProgressCategory.SKIP.value, foreground="grey", scale=0.8),
        Gtk.TextTag(name=ProgressCategory.WARN.value, foreground="yellow", scale=0.8),
        Gtk.TextTag(name=ProgressCategory.ERROR.value, foreground="red", scale=0.8),
    )
}


@preserve_type_decorator(
    Gtk.Template(
        string=resources.files(res).joinpath("ui/import_dialog.ui").read_text()
    )
)
class ImportDialog(Adw.Dialog):
    __gtype_name__ = "import_dialog"

    import_group: Adw.PreferencesGroup = Gtk.Template.Child()  # type: ignore[misc]
    progress_bar: Gtk.ProgressBar = Gtk.Template.Child()  # type: ignore[misc]
    console_view: Gtk.TextView = Gtk.Template.Child()  # type: ignore[misc]
    console_scroll: Gtk.ScrolledWindow = Gtk.Template.Child()  # type: ignore[misc]
    in_progress: bool = False

    def __init__(self, parent: Gtk.Window) -> None:
        super().__init__()
        self.parent = parent

        for tag in TAGS.values():
            self.console_view.get_buffer().get_tag_table().add(tag)
        self.console_view.get_style_context().add_provider(
            Gtk.CssProvider(), Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

        self.folder_dialog = Gtk.FileDialog(
            title="Import dictionaries",
            modal=True,
        )
        self.parent.connect("notify::default-width", self.on_width_changed)

    def on_width_changed(self, *args) -> None:
        parent_width = self.parent.get_size(Gtk.Orientation.HORIZONTAL)
        self.import_group.set_size_request(max(320, 3 * parent_width // 4), -1)

    def show_progress(self) -> None:
        self.on_width_changed()
        self.present(self.parent)

    def start_import(self, *args) -> None:
        if self.in_progress:
            self.show_progress()
        else:
            asyncio.create_task(self.import_dict())

    async def import_dict(self) -> None:
        res = await wait_gasync(self.folder_dialog.select_folder, parent=self.parent)
        try:
            file = self.folder_dialog.select_folder_finish(res)
        except GLib.Error:
            file = None

        path = file.get_path() if file else None
        if not path:
            return

        self.in_progress = True
        self.show_progress()
        vadj = self.console_scroll.get_vadjustment()
        async for step in importer.bulk_import(path):
            console = self.console_view.get_buffer()
            end_iter = console.get_end_iter()
            if console.props.text:
                console.insert(end_iter, "\n")
            msg = f"[{step.num}/{step.total}] {step.name} | {step.msg}"
            tag = TAGS.get(step.category.value, DEFAULT_TAG)
            console.insert_with_tags(end_iter, msg, tag)

            await asyncio.sleep(0.05)
            vadj.set_value(vadj.get_upper())
            self.progress_bar.set_fraction(step.num / step.total)
        vadj.set_value(vadj.get_upper())

        await asyncio.sleep(3)

        if self.props.visible:
            self.close()
        self.in_progress = False
