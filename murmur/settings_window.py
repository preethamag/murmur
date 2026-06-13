"""
Settings window — runs as a subprocess, reads/writes ~/.murmur/config.yaml directly.
Exits with code 0 when the user saves, so the main process knows to reload config.
"""

import sys
import tkinter as tk

from . import config, launcher, theme
from .recorder import list_input_devices

# ── option maps ───────────────────────────────────────────────────────────────

INPUT_MODES = [
    ("Hold to talk  — hold hotkey, release to transcribe", "hold"),
    ("Tap to talk   — tap to start, silence auto-stops",   "tap"),
]

HOTKEYS = [
    ("Right Option (⌥)  — macOS default", "right_option"),
    ("Left Option (⌥)",                   "left_option"),
    ("Right Ctrl",                         "right_ctrl"),
    ("Left Ctrl",                          "left_ctrl"),
    ("F4",                                 "f4"),
    ("F5",                                 "f5"),
    ("F6",                                 "f6"),
]

MODELS = [
    ("tiny     —  75 MB   fastest, basic accuracy",        "tiny"),
    ("base     — 145 MB   fast, good accuracy",            "base"),
    ("small    — 466 MB   balanced speed & accuracy",      "small"),
    ("turbo    — 809 MB   near-best accuracy, 8× faster",  "turbo"),
    ("medium   —  1.5 GB  high accuracy",                  "medium"),
    ("large-v3 —  3.0 GB  best accuracy",                  "large-v3"),
]

LANGUAGES = [
    ("Auto-detect", "auto"),
    ("English",     "en"),
    ("Spanish",     "es"),
    ("French",      "fr"),
    ("German",      "de"),
    ("Italian",     "it"),
    ("Portuguese",  "pt"),
    ("Japanese",    "ja"),
    ("Chinese",     "zh"),
    ("Korean",      "ko"),
    ("Hindi",       "hi"),
    ("Arabic",      "ar"),
]

# ── helpers ───────────────────────────────────────────────────────────────────

def _label_for(options, value):
    for label, val in options:
        if val == value:
            return label
    return options[0][0]

def _value_for(options, label):
    for lbl, val in options:
        if lbl == label:
            return val
    return options[0][1]


# ── window ────────────────────────────────────────────────────────────────────

class SettingsWindow:
    W = 540

    def __init__(self):
        self.cfg = config.load()

        root = tk.Tk()
        theme.setup_window(root, "Murmur — Settings", self.W)

        self._root = root
        self._build(root)

        theme.center_window(root, self.W)
        root.mainloop()

    def _dropdown(self, parent, label, options, current_val):
        """Create a label + custom dropdown pair, return the Dropdown widget."""
        theme.field_label(parent, label)
        labels = [lbl for lbl, _ in options]
        dd = theme.Dropdown(parent, labels, current=_label_for(options, current_val))
        dd.pack(fill="x", padx=theme.PAD, pady=(0, 2))
        return dd

    def _build(self, root):
        theme.header(root, "Settings", "Configure your Murmur preferences.")
        theme.separator(root, top=10, bottom=4)

        # ── Dropdowns ────────────────────────────────────────────────────
        self._mode_dd = self._dropdown(
            root, "Input mode", INPUT_MODES,
            self.cfg.get("input_mode", "hold"))

        self._hotkey_dd = self._dropdown(
            root, "Hotkey", HOTKEYS, self.cfg["hotkey"])

        self._model_dd = self._dropdown(
            root, "Model", MODELS, self.cfg["model"])

        self._lang_dd = self._dropdown(
            root, "Language", LANGUAGES, self.cfg["language"])

        # Microphone
        self._devices = [{"name": "System default", "index": None}] + list_input_devices()
        mic_labels = [d["name"] for d in self._devices]
        current_mic = self.cfg.get("device") or "System default"
        theme.field_label(root, "Microphone")
        self._mic_dd = theme.Dropdown(
            root, mic_labels,
            current=current_mic if current_mic in mic_labels else "System default")
        self._mic_dd.pack(fill="x", padx=theme.PAD, pady=(0, 2))

        # Max duration
        theme.field_label(root, "Max duration")
        dur_frame = tk.Frame(root, bg=theme.BG)
        dur_frame.pack(fill="x", padx=theme.PAD, pady=(0, 2))
        self._dur_var = tk.StringVar(value=str(self.cfg.get("max_duration", 60)))
        e = tk.Entry(dur_frame, textvariable=self._dur_var, width=6,
                     font=theme.BODY, bg=theme.FIELD_BG, fg=theme.TEXT,
                     relief="solid", bd=1, highlightthickness=0,
                     insertbackground=theme.TEXT)
        e.pack(side="left")
        tk.Label(dur_frame, text="  seconds", bg=theme.BG, fg=theme.MUTED,
                 font=theme.BODY).pack(side="left")

        # ── Toggles ─────────────────────────────────────────────────────
        theme.separator(root, top=12, bottom=8)

        self._ai_var = tk.BooleanVar(value=self.cfg.get("ai_cleanup", False))
        theme.checkbox(root, self._ai_var,
                       "AI cleanup", "Remove fillers & fix grammar (requires Ollama)")

        self._snd_var = tk.BooleanVar(value=self.cfg.get("sound_feedback", True))
        theme.checkbox(root, self._snd_var,
                       "Sound feedback", "Play tones on record start/stop")

        self._login_var = tk.BooleanVar(value=launcher.is_enabled())
        theme.checkbox(root, self._login_var,
                       "Launch at login", "Start Murmur automatically at login")

        # ── Save ─────────────────────────────────────────────────────────
        theme.separator(root, top=12, bottom=12)
        btn = theme.dark_button(root, "Save Settings", self._save)
        btn.pack(fill="x", padx=theme.PAD, pady=(0, theme.PAD))

    def _save(self):
        try:
            dur = int(self._dur_var.get())
        except ValueError:
            dur = 60

        self.cfg["input_mode"]           = _value_for(INPUT_MODES, self._mode_dd.get())
        self.cfg["hotkey"]               = _value_for(HOTKEYS,   self._hotkey_dd.get())
        self.cfg["model"]                = _value_for(MODELS,    self._model_dd.get())
        self.cfg["language"]             = _value_for(LANGUAGES, self._lang_dd.get())
        self.cfg["max_duration"]         = dur
        self.cfg["ai_cleanup"]           = self._ai_var.get()
        self.cfg["sound_feedback"]       = self._snd_var.get()
        self.cfg["launch_at_login"]      = self._login_var.get()
        self.cfg["punctuation_commands"] = True
        mic = self._mic_dd.get()
        self.cfg["device"] = None if mic == "System default" else mic

        config.save(self.cfg)
        self._root.destroy()
        sys.exit(0)   # signal to main process: config was saved


if __name__ == "__main__":
    SettingsWindow()
