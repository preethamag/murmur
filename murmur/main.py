import os
import sys
import time
import json
import subprocess
import threading

from . import config
from .recorder import Recorder
from .hotkey import HotkeyListener
from . import (injector, transcriber, tray, permissions,
               cleaner, vocabulary, sounds, punctuation, launcher)

_LAST_FILE = config.CONFIG_DIR / ".last.json"


class MurmurController:
    def __init__(self):
        self.cfg = config.load()
        self._recorder = self._build_recorder()
        self._state = "idle"
        self._session_id = 0           # bumped each new recording
        self._state_lock = threading.Lock()
        self._set_state = lambda s: None  # replaced by tray after init

        self._hotkey = HotkeyListener(
            self.cfg["hotkey"],
            on_press=self._on_press,
            on_release=self._on_release,
        )

    def _build_recorder(self):
        return Recorder(
            self.cfg["sample_rate"],
            self.cfg.get("device"),
            max_duration=self.cfg.get("max_duration", 60),
        )

    def start(self):
        permissions.check()
        self._hotkey.start()
        tray.run_tray(self)

    # ── state ──────────────────────────────────────────────────────────────────

    def _set(self, state):
        with self._state_lock:
            self._state = state
        self._set_state(state)

    # ── recording helpers ───────────────────────────────────────────────────────

    def _start_recording(self):
        # Atomic check-and-set so two fast hotkey events can't both start a recording.
        with self._state_lock:
            if self._state != "idle":
                return None
            self._state = "recording"
            self._session_id += 1
            session = self._session_id
        self._set_state("recording")

        try:
            self._recorder.start()
        except Exception as e:
            print(f"[murmur] recorder failed to start: {e}", file=sys.stderr)
            with self._state_lock:
                self._state = "idle"
            self._set_state("idle")
            return None

        if self.cfg.get("sound_feedback", True):
            sounds.play_start()
        threading.Thread(
            target=self._max_duration_watchdog, args=(session,), daemon=True
        ).start()
        return session

    def _max_duration_watchdog(self, session):
        max_dur = self.cfg.get("max_duration", 60)
        time.sleep(max_dur)
        # Only stop if THIS session is still recording — never clobber a later one.
        with self._state_lock:
            if self._state != "recording" or self._session_id != session:
                return
        self._stop_recording()

    def _stop_recording(self):
        with self._state_lock:
            if self._state != "recording":
                return
            self._state = "processing"
        self._set_state("processing")

        if self.cfg.get("sound_feedback", True):
            sounds.play_stop()
        audio_path = self._recorder.stop()

        if not audio_path:
            self._set("idle")
            return

        threading.Thread(target=self._process, args=(audio_path,), daemon=True).start()

    # ── hotkey callbacks (background thread) ───────────────────────────────────

    def _on_press(self):
        mode = self.cfg.get("input_mode", "hold")
        # _start_recording returns the new session id (or None if a recording was
        # already in progress). Only spawn the silence watchdog if WE actually
        # started the recording.
        session = None
        if self._state == "idle":
            session = self._start_recording()
            if session is not None and mode == "tap":
                threading.Thread(
                    target=self._silence_watchdog, args=(session,), daemon=True
                ).start()
        elif self._state == "recording" and mode == "tap":
            # Second tap = manual early stop
            self._stop_recording()

    def _on_release(self):
        if self.cfg.get("input_mode", "hold") == "hold":
            self._stop_recording()

    # ── silence watchdog (tap mode only) ───────────────────────────────────────

    def _silence_watchdog(self, session):
        threshold = self.cfg.get("silence_threshold", 200)   # RMS energy
        silence_needed = self.cfg.get("silence_duration", 1.5)  # seconds
        min_record = 0.8  # always capture at least this long before checking

        time.sleep(min_record)

        silence_start = None
        while True:
            with self._state_lock:
                if self._state != "recording" or self._session_id != session:
                    return
            energy = self._recorder.current_energy()
            if energy < threshold:
                if silence_start is None:
                    silence_start = time.time()
                elif time.time() - silence_start >= silence_needed:
                    self._stop_recording()
                    return
            else:
                silence_start = None
            time.sleep(0.05)

    # ── transcription pipeline ─────────────────────────────────────────────────

    def _process(self, audio_path):
        try:
            raw = transcriber.transcribe(
                audio_path,
                model=self.cfg["model"],
                language=self.cfg["language"],
            )
            if raw:
                text = raw
                if self.cfg.get("punctuation_commands", True):
                    text = punctuation.apply(text)
                vocab = vocabulary.load()
                text = cleaner.clean(text, self.cfg, vocab)
                self._save_last(raw, text)
                injector.inject(text)
        except Exception as e:
            print(f"[murmur] transcription pipeline failed: {e}", file=sys.stderr)
        finally:
            try:
                os.unlink(audio_path)
            except OSError:
                pass
            self._set("idle")

    def _save_last(self, raw: str, final: str):
        try:
            config.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
            _LAST_FILE.write_text(
                json.dumps({"raw": raw, "final": final}), encoding="utf-8"
            )
            try:
                os.chmod(_LAST_FILE, 0o600)
            except OSError:
                pass
        except OSError:
            pass

    # ── tray actions ───────────────────────────────────────────────────────────

    def open_settings(self):
        def _run():
            proc = subprocess.Popen(
                [sys.executable, "-m", "murmur.settings_window"], text=True
            )
            proc.wait()
            if proc.returncode == 0:
                self._reload_config()

        threading.Thread(target=_run, daemon=True).start()

    def open_vocabulary(self):
        threading.Thread(
            target=lambda: subprocess.Popen(
                [sys.executable, "-m", "murmur.vocabulary_window"], text=True
            ).wait(),
            daemon=True,
        ).start()

    def fix_last(self):
        if not _LAST_FILE.exists():
            return
        threading.Thread(
            target=lambda: subprocess.Popen(
                [sys.executable, "-m", "murmur.fix_window"], text=True
            ).wait(),
            daemon=True,
        ).start()

    def _reload_config(self):
        self.cfg = config.load()
        launcher.set_enabled(self.cfg.get("launch_at_login", False))
        self._recorder = self._build_recorder()
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
