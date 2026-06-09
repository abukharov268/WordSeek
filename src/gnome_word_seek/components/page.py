import asyncio
import gi


from word_seek.db.models import Article, ArticleFormat
from .scroll import Scroll
from .search import TAG_HIGHLIGHT, TextSearchSelection
from ..formats import xdxf


try:
    gi.require_version("GObject", "2.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Adw", "1")
    gi.require_version("Gtk", "4.0")

    from gi.repository import Adw, GObject, Gdk, Gtk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)

TAG_DICT = Gtk.TextTag(
    name="base:dict_desc",
    weight=600,
    scale=0.8,
    justification=Gtk.Justification.RIGHT,
    pixels_below_lines=5,
)
TAG_TXT = Gtk.TextTag(
    name="base:text",
    justification=Gtk.Justification.LEFT,
)


def setup_tags(tag_table: Gtk.TextTagTable | None = None) -> Gtk.TextTagTable:
    tag_table = xdxf.setup_tags(tag_table)
    tag_table.add(TAG_DICT)
    tag_table.add(TAG_TXT)
    tag_table.add(TAG_HIGHLIGHT)

    return tag_table


class ArticlesPage(Adw.PreferencesPage):
    def __init__(self) -> None:
        super().__init__()
        self.groups = list[Adw.PreferencesGroup]()
        self.views = list[Gtk.TextView]()
        self.css_provider = Gtk.CssProvider()

        self.scroll = Scroll.find_in_container(self)

        self.selection = TextSearchSelection(self.scroll, self.views, self._on_selected)
        self.tag_table = setup_tags()

        evk = Gtk.EventControllerKey.new()
        evk.connect("key-pressed", self.on_key_pressed)
        self.add_controller(evk)

    def on_key_pressed(
        self, event: Gdk.Event, keyval: int, keycode: int, state: Gdk.ModifierType
    ) -> bool:
        match keyval:
            case Gdk.KEY_Page_Down:
                self.scroll.move_page(1.0)
                return True
            case Gdk.KEY_Page_Up:
                self.scroll.move_page(-1.0)
                return True
            case Gdk.KEY_Down:
                self.scroll.move_page(0.2)
                return True
            case Gdk.KEY_Up:
                self.scroll.move_page(-0.2)
                return True
            case Gdk.KEY_Home:
                self.scroll.move_start()
                return True
            case Gdk.KEY_End:
                self.scroll.move_end()
                return True
            case _:
                return False

    def clear(self) -> None:
        for grp in self.groups:
            self.remove(grp)
        self.groups.clear()
        self.views.clear()

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST)
    def unselected(self) -> None:
        self.selection.invalidate()
        self.selected()

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST)
    def selected(self) -> None:
        pass

    def _on_selected(self, selection: TextSearchSelection) -> None:
        self.selection = selection
        self.emit("selected")

    def search(self, text: str) -> TextSearchSelection:
        self.selection = self.selection.search(text)
        return self.selection

    def populate(self, articles: list[Article]) -> None:
        self.scroll.move_start()
        asyncio.create_task(self.animate_populating(articles))

    def _insert_content(self, buffer: Gtk.TextBuffer, article: Article) -> None:
        iter = buffer.get_end_iter()
        buffer.insert_with_tags(iter, f"{article.dictionary.title}\n", TAG_DICT)
        if article.dtype == ArticleFormat.XDXF:
            xdxf.insert_xdxf_buffer(buffer, article.text)
        else:
            buffer.insert_with_tags(iter, article.text, TAG_TXT)

    async def animate_populating(self, articles: list[Article]) -> None:
        self.clear()
        pause = 0.1 / (len(articles) + 1)

        for article in articles:
            txt = Gtk.TextView(
                wrap_mode=Gtk.WrapMode.WORD_CHAR,
                left_margin=6,
                right_margin=6,
                top_margin=2,
                bottom_margin=6,
                buffer=Gtk.TextBuffer(tag_table=self.tag_table),
                editable=False,
                cursor_visible=False,
                vexpand=True,
                margin_start=2,
                margin_end=2,
                margin_top=2,
                margin_bottom=2,
            )
            row = Adw.PreferencesRow(
                child=txt,
                selectable=True,
                activatable=False,
                overflow=Gtk.Overflow.HIDDEN,
                vexpand=True,
            )
            grp = Adw.PreferencesGroup(vexpand=True, hexpand=True)
            grp.add(row)
            self.add(grp)
            self.groups.append(grp)
            self.views.append(txt)
            txt.get_style_context().add_provider(
                self.css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

            self._insert_content(txt.get_buffer(), article)

            evk = Gtk.EventControllerKey.new()
            evk.connect("key-pressed", self.on_key_pressed)
            txt.add_controller(evk)

            await asyncio.sleep(pause)
