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
                rumps.MenuItem("Quit", callback=rumps.quit_application),
            ]

        def set_state(self, state):
            self.title = ICONS.get(state, ICONS["idle"])

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
            pystray.MenuItem("Quit", lambda: tray.stop()),
        ),
    )

    def set_state(state):
        tray.icon = icons.get(state, icons["idle"])

    app._set_state = set_state
    tray.run()
