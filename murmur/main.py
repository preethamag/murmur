import os
import sys
import subprocess
import threading

from . import config
from .recorder import Recorder
from .hotkey import HotkeyListener
from . import injector, transcriber, tray, permissions
from .settings_window import SettingsWindow


class MurmurController:
    def __init__(self):
        self.cfg = config.load()
        self._recorder = Recorder(self.cfg["sample_rate"])
        self._state = "idle"
        self._set_state = lambda s: None  # replaced by tray after init

        self._hotkey = HotkeyListener(
            self.cfg["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )

    def start(self):
        permissions.check()        # blocks until accessibility granted
        self._hotkey.start()
        tray.run_tray(self)        # blocks on main thread

    # ── state ──────────────────────────────────────────────────────────────────

    def _set(self, state):
        self._state = state
        self._set_state(state)

    # ── hotkey callbacks (background thread) ───────────────────────────────────

    def _on_press(self):
        if self._state != "idle":
            return
        self._set("recording")
        self._recorder.start()

    def _on_release(self):
        if self._state != "recording":
            return
        self._set("processing")
        audio_path = self._recorder.stop()

        if not audio_path:
            self._set("idle")
            return

        threading.Thread(target=self._process, args=(audio_path,), daemon=True).start()

    def _process(self, audio_path):
        try:
            text = transcriber.transcribe(
                audio_path,
                model=self.cfg["model"],
                language=self.cfg["language"],
            )
            if text:
                injector.inject(text)
        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass
            self._set("idle")

    # ── settings ───────────────────────────────────────────────────────────────

    def open_settings(self):
        def _run():
            proc = subprocess.Popen(
                [sys.executable, "-m", "murmur.settings_window"],
                text=True,
            )
            proc.wait()
            if proc.returncode == 0:
                self._reload_config()

        threading.Thread(target=_run, daemon=True).start()

    def _reload_config(self):
        self.cfg = config.load()
        self._hotkey.stop()
        self._hotkey = HotkeyListener(
            self.cfg["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._hotkey.start()


def main():
    MurmurController().start()


if __name__ == "__main__":
    main()
