from reactivex import Subject
from reactivex.scheduler.mainloop import GtkScheduler
from word_seek.eventsrc.autocomplete import create_autocomplete
from word_seek.eventsrc.autocomplete import FoundPhrases, PhrasesQuery

import gi

try:
    gi.require_version("GObject", "2.0")
    gi.require_version("GLib", "2.0")
    gi.require_version("Gdk", "4.0")
    gi.require_version("Gtk", "4.0")

    from gi.repository import Gdk, Gtk, GLib, GObject
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


class SuggestItemFactory(Gtk.SignalListItemFactory):
    def __init__(self) -> None:
        super().__init__()
        self.connect("bind", self.bind)
        self.connect("unbind", self.unbind)
        self.connect("setup", self.setup)
        self.connect("teardown", self.teardown)

    @staticmethod
    def bind(_: "SuggestItemFactory", item: Gtk.ListItem) -> None:
        widget = item.get_child()
        assert isinstance(widget, Gtk.Label)
        data = item.get_item()
        if isinstance(data, Gtk.StringObject):
            widget.set_label(data.get_string())

    @staticmethod
    def unbind(*_) -> None:
        pass

    @staticmethod
    def setup(_: "SuggestItemFactory", item: Gtk.ListItem) -> None:
        data = item.get_item()
        widget = Gtk.Label(
            justify=Gtk.Justification.LEFT,
            halign=Gtk.Align.START,
            focusable=False,
            selectable=False,
        )
        if isinstance(data, Gtk.StringObject):
            widget.set_label(data.get_string())
        item.set_child(widget)

    @staticmethod
    def teardown(*_) -> None:
        pass


class ConstrainedBoxLayout(Gtk.BoxLayout):
    def __init__(
        self,
        hmax: int,
        vmax: int,
        orientation: Gtk.Orientation = Gtk.Orientation.VERTICAL,
    ) -> None:
        super().__init__(orientation=orientation)
        self.hmax = hmax
        self.vmax = vmax

    def do_measure(
        self, widget: Gtk.Widget, orientation: Gtk.Orientation, for_size: int
    ) -> tuple[int, int, int, int]:
        sizes = Gtk.BoxLayout.do_measure(self, widget, orientation, for_size)
        limit = self.vmax if orientation is Gtk.Orientation.VERTICAL else self.hmax
        s1, s2, s3, s4 = (min(limit, size) for size in sizes)
        return s1, s2, s3, s4


class SuggestPopup(Gtk.Popover):
    list_view: Gtk.ListView | None = None
    suggestion: str | None = None
    win_event_hnd_id: int | None = None
    ignore_change: bool = False

    def __init__(self, entry: Gtk.SearchEntry, window: Gtk.Window) -> None:
        super().__init__(
            position=Gtk.PositionType.BOTTOM,
            has_arrow=False,
            hexpand=True,
            vexpand=True,
            valign=Gtk.Align.START,
            halign=Gtk.Align.START,
            autohide=False,
        )

        self.entry = entry
        self.window = window
        self.entry.set_key_capture_widget(self.entry)
        self.suggest_model = Gtk.StringList()
        self.selection_model = Gtk.SingleSelection(
            model=self.suggest_model,
            can_unselect=True,
            autoselect=False,
        )
        self.set_parent(entry)
        self.phrase_subject = Subject[PhrasesQuery]()
        self.subscription = create_autocomplete(self.phrase_subject).subscribe(
            on_next=self.on_phrase_found, scheduler=GtkScheduler(GLib)
        )
        self.list_view = Gtk.ListView(
            model=self.selection_model,
            factory=SuggestItemFactory(),
            single_click_activate=True,
            valign=Gtk.Align.START,
            halign=Gtk.Align.START,
            hscroll_policy=Gtk.ScrollablePolicy.NATURAL,
            vscroll_policy=Gtk.ScrollablePolicy.NATURAL,
            layout_manager=ConstrainedBoxLayout(hmax=600, vmax=300),
        )
        self.set_child(self.list_view)

        self.entry.connect("changed", self.on_entry_changed)
        focus_ctrl = Gtk.EventControllerFocus.new()
        focus_ctrl.connect("enter", self.on_entry_focus_enter)
        focus_ctrl.connect("leave", self.on_entry_focus_leave)
        self.entry.add_controller(focus_ctrl)
        key_ctrl = Gtk.EventControllerKey.new()
        key_ctrl.connect("key-pressed", self.on_entry_key_pressed)
        self.entry.add_controller(key_ctrl)

        self.connect("show", self.on_show)
        self.connect("hide", self.on_hide)

        self.list_view.connect("activate", self.on_activate)

        self.win_ctrl = Gtk.EventControllerLegacy.new()
        self.window.add_controller(self.win_ctrl)
        self.window.connect("notify::is-active", self.on_is_active_changed)

    @GObject.Signal(flags=GObject.SignalFlags.RUN_LAST, arg_types=(str,))
    def selected(self, phrase: str) -> None:
        self.suggestion = phrase
        self.entry.set_text(phrase)
        self.entry.set_position(-1)
        self.popdown()

    def on_activate(self, _: Gtk.ListView, position: int) -> None:
        item = self.selection_model.get_item(position)
        assert isinstance(item, Gtk.StringObject)
        self.emit("selected", item.get_string())

    def on_is_active_changed(
        self, obj: GObject.GObject, pspec: GObject.ParamSpec
    ) -> None:
        if not self.window.is_active():
            self.popdown()

    def on_win_event(self, ctrl: Gtk.EventControllerLegacy, *args) -> None:
        match ctrl.get_current_event():
            case Gdk.ButtonEvent():
                self.popdown()

    def on_show(self, widget: Gtk.Widget) -> None:
        if self.ignore_change:
            return

        self.on_hide(widget)
        self.win_event_hnd_id = self.win_ctrl.connect("event", self.on_win_event)

    def on_hide(self, widget: Gtk.Widget) -> None:
        if not self.win_event_hnd_id:
            return
        self.win_ctrl.disconnect(self.win_event_hnd_id)
        self.win_event_hnd_id = None

    def on_entry_focus_enter(self, ctrl: Gtk.EventControllerFocus) -> None:
        self.on_entry_changed(self.entry)

    def on_entry_focus_leave(self, ctrl: Gtk.EventControllerFocus) -> None:
        self.popdown()

    def on_entry_key_pressed(
        self, event: Gdk.Event, keyval: int, keycode: int, state: Gdk.ModifierType
    ) -> None:
        if self.ignore_change:
            return

        if keyval == Gdk.KEY_Escape:
            self.entry.select_region(0, len(self.entry.props.text))
            self.popdown()

    def on_entry_changed(self, entry: Gtk.SearchEntry) -> None:
        if (
            self.ignore_change
            or not entry.get_state_flags() & Gtk.StateFlags.FOCUS_WITHIN
        ):
            return

        self.popdown()
        if self.suggestion == entry.props.text or not entry.props.text:
            return

        self.suggestion = None
        self.phrase_subject.on_next(PhrasesQuery(entry.props.text))

    def on_phrase_found(self, found: FoundPhrases) -> None:
        if self.entry.props.text != found.query.phrase:
            return

        self.suggest_model.splice(
            0, self.suggest_model.get_n_items(), found.suggestions
        )
        if found.suggestions:
            self.popup()
