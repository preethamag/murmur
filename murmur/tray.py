import sys
import threading

ICONS = {"idle": "🎙", "recording": "🔴", "processing": "⏳"}


def run_tray(app):
    if sys.platform == "darwin":
        _run_mac(app)
    else:
        _run_win(app)


# ── macOS ──────────────────────────────────────────────────────────────────────

def _run_mac(app):
    import rumps

    class _MacApp(rumps.App):
        def __init__(self, controller):
            super().__init__("Murmur", title=ICONS["idle"])
            self._ctrl = controller
            self.menu = [
                rumps.MenuItem(f"Model: {controller.cfg['model']}"),
                rumps.MenuItem(f"Hotkey: {controller.cfg['hotkey']}"),
                None,
                rumps.MenuItem("Settings",              callback=self._open_settings),
                rumps.MenuItem("Vocabulary",            callback=self._open_vocabulary),
                rumps.MenuItem("Fix Last Transcription", callback=self._fix_last),
                None,
                rumps.MenuItem("Quit", callback=rumps.quit_application),
            ]

        def set_state(self, state):
            self.title = ICONS.get(state, ICONS["idle"])

        def refresh_labels(self):
            self.menu["Model: " + self._ctrl.cfg["model"]] and None  # noop guard
            # Rebuild info items to reflect updated config
            for item in list(self.menu._menu):
                pass  # rumps doesn't support live label edits cleanly; reload on next open

        def _open_settings(self, _):
            self._ctrl.open_settings()

        def _open_vocabulary(self, _):
            self._ctrl.open_vocabulary()

        def _fix_last(self, _):
            self._ctrl.fix_last()

    mac_app = _MacApp(app)
    app._set_state = mac_app.set_state
    mac_app.run()


# ── Windows ────────────────────────────────────────────────────────────────────

def _run_win(app):
    import pystray
    from PIL import Image, ImageDraw

    def _make_icon(color):
        img = Image.new("RGB", (64, 64), color="black")
        d = ImageDraw.Draw(img)
        d.ellipse([16, 16, 48, 48], fill=color)
        return img

    icons = {
        "idle": _make_icon("white"),
        "recording": _make_icon("red"),
        "processing": _make_icon("yellow"),
    }

    tray = pystray.Icon(
        "Murmur",
        icon=icons["idle"],
        title="Murmur",
        menu=pystray.Menu(
            pystray.MenuItem(f"Model: {app.cfg['model']}", None),
            pystray.MenuItem("Settings",               lambda: app.open_settings()),
            pystray.MenuItem("Vocabulary",             lambda: app.open_vocabulary()),
            pystray.MenuItem("Fix Last Transcription", lambda: app.fix_last()),
            pystray.MenuItem("Quit",                   lambda: tray.stop()),
        ),
    )

    def set_state(state):
        tray.icon = icons.get(state, icons["idle"])

    app._set_state = set_state
    tray.run()
