import asyncio
import sys
from datetime import datetime, timedelta, timezone
from importlib import resources

import gi
import gi.events
import typer

import word_seek.cli.app
from word_seek.db import repo
from word_seek.db.config import APP_ID, ensure_db
from word_seek.db.models import ViewLog

from . import res
from .components.dicts import DictionariesPage
from .components.history import HistoryPage
from .components.imports import ImportDialog
from .components.page import ArticlesPage
from .components.suggestion import SuggestPopup
from .gasync import wait_gasync
from .typings import preserve_type_decorator

try:
    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Adw", "1")

    from gi.repository import Adw, Gdk, Gio, Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    sys.exit(1)


def create_welcome_page() -> Adw.StatusPage:
    return Adw.StatusPage(
        title="Find Translations",
        description="Type a phrase to find the transation",
        icon_name="system-search-symbolic",
    )


def create_no_result_page() -> Adw.StatusPage:
    return Adw.StatusPage(
        title="No Results Founds",
        description="Try a different search",
        icon_name="system-search-symbolic",
    )


@preserve_type_decorator(
    Gtk.Template(string=resources.files(res).joinpath("ui/window.ui").read_text())
)
class MainWindow(Adw.ApplicationWindow):
    __gtype_name__ = "main_window"

    main_view: Adw.ToolbarView = Gtk.Template.Child()  # type: ignore[misc]
    page_find_view: Adw.ToolbarView = Gtk.Template.Child()  # type: ignore[misc]
    history_view: Adw.ToolbarView = Gtk.Template.Child()  # type: ignore[misc]
    nav_view: Adw.NavigationView = Gtk.Template.Child()  # type: ignore[misc]
    search_entry: Gtk.SearchEntry = Gtk.Template.Child()  # type: ignore[misc]
    page_find_entry: Gtk.SearchEntry = Gtk.Template.Child()  # type: ignore[misc]
    next_button: Gtk.Button = Gtk.Template.Child()  # type: ignore[misc]
    prev_button: Gtk.Button = Gtk.Template.Child()  # type: ignore[misc]

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.import_dialog = ImportDialog(self)

        self.dictionaries_page = DictionariesPage()
        self.nav_view.add(self.dictionaries_page)

        self.suggest_popup = SuggestPopup(self.search_entry, self)
        self.suggest_popup.connect("selected", self.on_phrase_selected)

        self.no_result_page = create_no_result_page()
        self.page = ArticlesPage()
        self.main_view.set_content(create_welcome_page())
        self.page.connect("selected", self.on_selection_changed)

        self.history = HistoryPage()
        self.history_view.set_content(self.history)
        self.history.connect("selected", self.on_history_selected)

        page_find_act = Gio.SimpleAction(name="page_find", enabled=True)
        page_find_act.connect("activate", self.on_page_find)
        self.add_action(page_find_act)

        search_clipboard_act = Gio.SimpleAction(name="search_clipboard", enabled=True)
        search_clipboard_act.connect("activate", self.on_search_clipboard)
        self.add_action(search_clipboard_act)

        history_act = Gio.SimpleAction(name="show_history", enabled=True)
        history_act.connect("activate", self.on_show_history)
        self.add_action(history_act)

        history_clear_act = Gio.SimpleAction(name="clear_history", enabled=True)
        history_clear_act.connect("activate", self.history.on_delete_items)
        self.add_action(history_clear_act)

        history_clear_old_act = Gio.SimpleAction(name="clear_old_history", enabled=True)
        history_clear_old_act.connect(
            "activate",
            lambda *args: self.history.on_delete_items(
                before=datetime.now(timezone.utc) + timedelta(days=90)
            ),
        )
        self.add_action(history_clear_old_act)

        import_dict_act = Gio.SimpleAction(name="import_dictionaries", enabled=True)
        import_dict_act.connect("activate", self.import_dialog.start_import)
        self.add_action(import_dict_act)

        edit_dictionaries_act = Gio.SimpleAction(name="edit_dictionaries", enabled=True)
        edit_dictionaries_act.connect("activate", self.on_edit_dictionaries)
        self.add_action(edit_dictionaries_act)

        quit_act = Gio.SimpleAction(name="quit", enabled=True)
        quit_act.connect("activate", self.quit_app)
        self.add_action(quit_act)

        self.next_action = Gio.SimpleAction(name="next_match", enabled=False)
        self.next_action.connect("activate", self.on_page_find_next)
        self.add_action(self.next_action)

        self.prev_action = Gio.SimpleAction(name="prev_match", enabled=False)
        self.prev_action.connect("activate", self.on_page_find_prev)
        self.add_action(self.prev_action)

        evk = Gtk.EventControllerKey.new()
        evk.connect("key-pressed", self.on_main_view_key_pressed)
        self.main_view.add_controller(evk)

    @property
    def nav_view_tag(self) -> str | None:
        page = self.nav_view.get_visible_page()
        return page.props.tag if page else None

    @Gtk.Template.Callback()
    def on_close_request(self, win: Adw.ApplicationWindow) -> bool:
        hold = False
        for task in asyncio.all_tasks():
            if not task.done():
                task.cancel()
                hold = True
        if hold:
            asyncio.create_task(asyncio.wait(asyncio.all_tasks())).add_done_callback(
                self.quit_app
            )
        return hold

    @Gtk.Template.Callback()
    def on_search_activate(self, entry: Gtk.SearchEntry) -> None:
        self.suggest_popup.popdown()
        asyncio.create_task(self.search(entry.get_text()))

    @Gtk.Template.Callback()
    def on_page_find_activate(self, entry: Gtk.SearchEntry) -> None:
        self.page.search(entry.get_text())

    def set_search_entry_uncompleted(self, text: str) -> None:
        try:
            self.suggest_popup.ignore_change = True
            self.search_entry.set_text(text)
        finally:
            self.suggest_popup.ignore_change = False

    def quit_app(self, *args) -> None:
        self.close()

    async def search_clipboard(self) -> None:
        clipboard = self.get_clipboard()

        res = await wait_gasync(clipboard.read_text_async)
        text = clipboard.read_text_finish(res) or ""
        text = text.strip()
        if text:
            self.suggest_popup.popdown()
            self.set_search_entry_uncompleted(text)
            await self.search(text)

    def on_search_clipboard(self, *args) -> None:
        asyncio.create_task(self.search_clipboard())

    def on_show_history(self, *args) -> None:
        self.page.unselected()
        self.history.load()
        self.nav_view.push_by_tag("history")

    def on_history_selected(self, history: HistoryPage, phrase: str) -> None:
        if self.nav_view_tag != "main":
            self.nav_view.pop()
        self.suggest_popup.popdown()
        self.set_search_entry_uncompleted(phrase)
        asyncio.create_task(self.search(phrase))

    def on_page_find_next(self, *args) -> None:
        if self.page.selection.invalid or self.page.selection.empty:
            return

        self.page.selection.next()

    def on_page_find_prev(self, *args) -> None:
        if self.page.selection.invalid or self.page.selection.empty:
            return

        self.page.selection.prev()

    @Gtk.Template.Callback()
    def on_nav_back(
        self, view: Adw.NavigationView, page: Adw.NavigationPage, *args
    ) -> None:
        if page.props.tag == "page-find":
            self.page.unselected()
            self.page_find_view.set_content(None)
            self.page.unparent()
            self.main_view.set_content(self.page)

    @Gtk.Template.Callback()
    def on_page_find_stop(self, _: Gtk.SearchEntry) -> None:
        self.nav_view.pop()

    def on_page_find(self, *_) -> None:
        self.show_page_find()

    def on_main_view_key_pressed(
        self, event: Gdk.Event, keyval: int, keycode: int, state: Gdk.ModifierType
    ) -> None:
        if keyval == Gdk.KEY_Escape:
            self.search_entry.grab_focus()

    def on_selection_changed(self, page: ArticlesPage) -> None:
        enabled = page.selection.active
        self.next_action.set_enabled(enabled)
        self.prev_action.set_enabled(enabled)

    def main_view_content_clear(self) -> None:
        content = self.main_view.get_content()
        if content:
            self.main_view.set_content(None)
            content.unparent()

    def show_page_find(self) -> None:
        if self.main_view.get_content() != self.page:
            return

        self.nav_view.push_by_tag("page-find")
        self.main_view_content_clear()
        self.page_find_view.set_content(self.page)
        self.page_find_entry.grab_focus()
        self.page.connect("selected", self.on_selection_changed)

    def on_phrase_selected(self, _: SuggestPopup, phrase: str) -> None:
        asyncio.create_task(self.search(phrase))

    async def search(self, term: str) -> None:
        found = await repo.find_phrases(term, 1)
        if found and found[0].text.strip() == term.strip():
            phrase = found[0]
            articles = await repo.find_articles(phrase)
            self.main_view_content_clear()
            self.main_view.set_content(self.page)
            self.page.populate(articles)

            time = datetime.now(timezone.utc)
            log = ViewLog(phrase_id=phrase.id, shown_at_utc=time)
            await repo.update_view_log(log)
        else:
            self.main_view_content_clear()
            self.main_view.set_content(self.no_result_page)

    def on_edit_dictionaries(self, *args) -> None:
        self.nav_view.push_by_tag("dictionaries")
        self.dictionaries_page.load()


class Application(Adw.Application):
    def __init__(self):
        Adw.Application.__init__(
            self, application_id=APP_ID, flags=Gio.ApplicationFlags.FLAGS_NONE
        )

    def do_activate(self):
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
            asyncio.create_task(ensure_db())
        win.present()


app = typer.Typer()
app.add_typer(word_seek.cli.app.app, name="cli")


@app.callback(invoke_without_command=True)
def gui(ctx: typer.Context):
    if ctx.invoked_subcommand is not None:
        return

    app = Application()
    policy = gi.events.GLibEventLoopPolicy()
    asyncio.set_event_loop_policy(policy)
    app.run(sys.argv)
