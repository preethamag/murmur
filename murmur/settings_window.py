"""
Settings window — runs as a subprocess, reads/writes ~/.murmur/config.yaml directly.
Exits with code 0 when the user saves, so the main process knows to reload config.
"""

import sys
import tkinter as tk
from tkinter import ttk

from . import config, launcher
from .recorder import list_input_devices

# ── option maps ───────────────────────────────────────────────────────────────

INPUT_MODES = [
    ("Hold to talk  — hold hotkey while speaking, release to transcribe", "hold"),
    ("Tap to talk   — tap once to start, silence auto-stops (Mode B)",   "tap"),
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
    ("tiny     —  75 MB   fastest, basic accuracy",       "tiny"),
    ("base     — 145 MB   fast, good accuracy",           "base"),
    ("small    — 466 MB   balanced speed & accuracy",     "small"),
    ("turbo    — 809 MB   near-best accuracy, 8× faster ★", "turbo"),
    ("medium   —  1.5 GB  high accuracy",                 "medium"),
    ("large-v3 —  3.0 GB  best accuracy",                 "large-v3"),
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
    W, H = 480, 460

    def __init__(self):
        self.cfg = config.load()

        root = tk.Tk()
        root.title("Murmur Settings")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        # Center on screen
        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        x = (sw - self.W) // 2
        y = (sh - self.H) // 2
        root.geometry(f"{self.W}x{self.H}+{x}+{y}")

        self._root = root
        self._build(root)
        root.mainloop()

    def _row(self, parent, label, row):
        tk.Label(parent, text=label, anchor="w", width=14).grid(
            row=row, column=0, sticky="w", padx=(16, 8), pady=10
        )

    def _combo(self, parent, options, current_val, row):
        labels = [lbl for lbl, _ in options]
        var = tk.StringVar(value=_label_for(options, current_val))
        cb = ttk.Combobox(parent, textvariable=var, values=labels,
                          state="readonly", width=42)
        cb.grid(row=row, column=1, sticky="w", padx=(0, 16), pady=10)
        return var

    def _build(self, root):
        frame = tk.Frame(root, padx=8, pady=8)
        frame.pack(fill="both", expand=True)

        self._row(frame, "Input mode", 0)
        self._mode_var = self._combo(frame, INPUT_MODES, self.cfg.get("input_mode", "hold"), 0)

        self._row(frame, "Hotkey", 1)
        self._hotkey_var = self._combo(frame, HOTKEYS, self.cfg["hotkey"], 1)

        self._row(frame, "Model", 2)
        self._model_var = self._combo(frame, MODELS, self.cfg["model"], 2)

        self._row(frame, "Language", 3)
        self._lang_var = self._combo(frame, LANGUAGES, self.cfg["language"], 3)

        # Microphone selector
        self._row(frame, "Microphone", 4)
        self._devices = [{"name": "System default", "index": None}] + list_input_devices()
        mic_labels = [d["name"] for d in self._devices]
        current_mic = self.cfg.get("device") or "System default"
        self._mic_var = tk.StringVar(value=current_mic if current_mic in mic_labels else "System default")
        mic_cb = ttk.Combobox(frame, textvariable=self._mic_var, values=mic_labels,
                              state="readonly", width=42)
        mic_cb.grid(row=4, column=1, sticky="w", padx=(0, 16), pady=10)

        self._row(frame, "Max duration", 5)
        dur_frame = tk.Frame(frame)
        dur_frame.grid(row=5, column=1, sticky="w", pady=10)
        self._dur_var = tk.StringVar(value=str(self.cfg.get("max_duration", 60)))
        tk.Entry(dur_frame, textvariable=self._dur_var, width=6).pack(side="left")
        tk.Label(dur_frame, text=" seconds").pack(side="left")

        self._row(frame, "AI Cleanup", 6)
        ai_frame = tk.Frame(frame)
        ai_frame.grid(row=6, column=1, sticky="w", pady=10)
        self._ai_var = tk.BooleanVar(value=self.cfg.get("ai_cleanup", False))
        tk.Checkbutton(
            ai_frame, variable=self._ai_var,
            text="Remove fillers & fix grammar  (requires Ollama)",
        ).pack(side="left")

        self._row(frame, "Sound feedback", 7)
        snd_frame = tk.Frame(frame)
        snd_frame.grid(row=7, column=1, sticky="w", pady=10)
        self._snd_var = tk.BooleanVar(value=self.cfg.get("sound_feedback", True))
        tk.Checkbutton(snd_frame, variable=self._snd_var,
                       text="Play tones on record start/stop").pack(side="left")

        self._row(frame, "Launch at login", 8)
        login_frame = tk.Frame(frame)
        login_frame.grid(row=8, column=1, sticky="w", pady=10)
        self._login_var = tk.BooleanVar(value=launcher.is_enabled())
        tk.Checkbutton(login_frame, variable=self._login_var,
                       text="Start Murmur automatically at login").pack(side="left")

        # Divider + Save
        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=(0, 10))
        btn_frame = tk.Frame(root)
        btn_frame.pack()
        tk.Button(btn_frame, text="  Save  ", command=self._save,
                  padx=12, pady=4).pack()

    def _save(self):
        try:
            dur = int(self._dur_var.get())
        except ValueError:
            dur = 60

        self.cfg["input_mode"]           = _value_for(INPUT_MODES, self._mode_var.get())
        self.cfg["hotkey"]               = _value_for(HOTKEYS,   self._hotkey_var.get())
        self.cfg["model"]                = _value_for(MODELS,    self._model_var.get())
        self.cfg["language"]             = _value_for(LANGUAGES, self._lang_var.get())
        self.cfg["max_duration"]         = dur
        self.cfg["ai_cleanup"]           = self._ai_var.get()
        self.cfg["sound_feedback"]       = self._snd_var.get()
        self.cfg["launch_at_login"]      = self._login_var.get()
        self.cfg["punctuation_commands"] = True
        mic = self._mic_var.get()
        self.cfg["device"] = None if mic == "System default" else mic

        config.save(self.cfg)
        self._root.destroy()
        sys.exit(0)   # signal to main process: config was saved


if __name__ == "__main__":
    SettingsWindow()
