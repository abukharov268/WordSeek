import sys

import gi

try:
    gi.require_version("Adw", "1")
    gi.require_version("Gdk", "4.0")
    gi.require_version("GLib", "2.0")
    gi.require_version("GObject", "2.0")
    gi.require_version("Graphene", "1.0")
    gi.require_version("Gtk", "4.0")
    gi.require_version("Pango", "1.0")

    from gi.repository import Adw, Gdk, Gio, GLib, GObject, Graphene, Gtk, Pango
except (ImportError, ValueError) as exc:
    print("Error: Dependencies not met.", exc)
    sys.exit(1)


__all__ = ["Adw", "GLib", "GObject", "Gdk", "Gio", "Graphene", "Gtk", "Pango"]
