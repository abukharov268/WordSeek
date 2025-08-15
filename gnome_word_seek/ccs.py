import gi

try:
    gi.require_version("Gtk", "4.0")
    gi.require_version("Gdk", "4.0")

    from gi.repository import Gtk, Gdk
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    exit(1)


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
