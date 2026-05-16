import os
import sys
import subprocess
import threading

from . import config
from .recorder import Recorder
from .hotkey import HotkeyListener
from . import injector, transcriber, tray
from .settings_window import SettingsWindow


class MurmurController:
    def __init__(self):
        self.cfg = config.load()
        self._recorder = Recorder(self.cfg["sample_rate"])
        self._state = "idle"
        self._set_state = lambda s: None  # replaced by tray after init
        self._overlay = None

        self._hotkey = HotkeyListener(
            self.cfg["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )

    def start(self):
        self._start_overlay()
        self._hotkey.start()
        tray.run_tray(self)  # blocks on main thread

    # ── overlay subprocess ─────────────────────────────────────────────────────

    def _start_overlay(self):
        try:
            self._overlay = subprocess.Popen(
                [sys.executable, "-m", "murmur.overlay"],
                stdin=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception:
            self._overlay = None   # overlay is optional — don't crash if it fails

    def _overlay_send(self, cmd: str):
        if self._overlay and self._overlay.poll() is None:
            try:
                self._overlay.stdin.write(cmd + "\n")
                self._overlay.stdin.flush()
            except BrokenPipeError:
                pass

    # ── state ──────────────────────────────────────────────────────────────────

    def _set(self, state):
        self._state = state
        self._set_state(state)

    # ── hotkey callbacks (background thread) ───────────────────────────────────

    def _on_press(self):
        if self._state != "idle":
            return
        self._set("recording")
        self._overlay_send("recording")
        self._recorder.start(on_level=self._on_level)

    def _on_level(self, level: float):
        self._overlay_send(f"level:{level:.3f}")

    def _on_release(self):
        if self._state != "recording":
            return
        self._set("processing")
        self._overlay_send("processing")
        audio_path = self._recorder.stop()

        if not audio_path:
            self._overlay_send("hide")
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
            self._overlay_send("hide")
            self._set("idle")

    # ── settings ───────────────────────────────────────────────────────────────

    def open_settings(self):
        def _run():
            proc = subprocess.Popen(
                [sys.executable, "-m", "murmur.settings_window"],
                text=True,
            )
            proc.wait()
            if proc.returncode == 0:   # saved
                self._reload_config()

        threading.Thread(target=_run, daemon=True).start()

    def _reload_config(self):
        self.cfg = config.load()
        # Restart hotkey listener with potentially new key
        self._hotkey.stop()
        self._hotkey = HotkeyListener(
            self.cfg["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )
        self._hotkey.start()

    def __del__(self):
        if self._overlay:
            self._overlay.terminate()


def main():
    MurmurController().start()


if __name__ == "__main__":
    main()
