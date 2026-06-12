import os
import sys
import queue

ICONS = {"idle": "🎙", "recording": "🔴", "processing": "⏳"}

_RES_DIR = os.path.join(os.path.dirname(__file__), "resources")
_MAC_ICONS = {
    "idle":       os.path.join(_RES_DIR, "MenuBarIconTemplate.png"),
    "recording":  os.path.join(_RES_DIR, "MenuBarIconRecording.png"),
    "processing": os.path.join(_RES_DIR, "MenuBarIconProcessing.png"),
}


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
            icon_path = _MAC_ICONS["idle"] if os.path.exists(_MAC_ICONS["idle"]) else None
            super().__init__("Murmur", icon=icon_path, title=None if icon_path else ICONS["idle"],
                             template=True)
            self._ctrl = controller
            self._state_queue = queue.Queue()
            self._timer = rumps.Timer(self._poll_state, 0.1)
            self._timer.start()
            self.menu = [
                rumps.MenuItem(f"Model: {controller.cfg['model']}"),
                rumps.MenuItem(f"Hotkey: {controller.cfg['hotkey']}"),
                None,
                rumps.MenuItem("Settings",              callback=self._open_settings),
                rumps.MenuItem("Vocabulary",            callback=self._open_vocabulary),
                rumps.MenuItem("Fix Last Transcription", callback=self._fix_last),
            ]

        def set_state(self, state):
            self._state_queue.put(state)

        def _poll_state(self, _):
            try:
                while True:
                    state = self._state_queue.get_nowait()
                    icon_path = _MAC_ICONS.get(state, _MAC_ICONS["idle"])
                    if os.path.exists(icon_path):
                        is_template = (state == "idle")
                        self.template = is_template
                        self.icon = icon_path
                        self.title = None
                    else:
                        self.title = ICONS.get(state, ICONS["idle"])
            except queue.Empty:
                pass

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
