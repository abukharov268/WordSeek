from .gnome_libs import Gdk, Gtk


def setup_css(css: str) -> None:
    display = Gdk.Display.get_default()
    if not display:
        return

    provider = Gtk.CssProvider()
    provider.load_from_string(css)
    Gtk.StyleContext.add_provider_for_display(
        display,
        provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION,
    )
