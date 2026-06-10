"""
Checks for macOS Accessibility permission on first launch.
Shows a guided onboarding window that deep-links to System Settings
and auto-detects when the user grants access.
"""

import os
import sys
import subprocess
import tkinter as tk

SETTINGS_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)

# Use version tuple so we always get e.g. "python3.13" regardless of venv symlink names
_PYTHON_BINARY = f"python{sys.version_info.major}.{sys.version_info.minor}"


def check():
    """Block until Accessibility permission is granted. No-op on non-macOS."""
    if sys.platform != "darwin":
        return
    if _has_access():
        return
    _show_onboarding()


def _has_access() -> bool:
    try:
        from ApplicationServices import AXIsProcessTrusted
        return bool(AXIsProcessTrusted())
    except ImportError:
        pass
    try:
        import ctypes
        lib = ctypes.cdll.LoadLibrary(
            "/System/Library/Frameworks/ApplicationServices.framework/ApplicationServices"
        )
        lib.AXIsProcessTrusted.restype = ctypes.c_bool
        return bool(lib.AXIsProcessTrusted())
    except Exception:
        return True


def _circle(parent, text, size=26, bg="#ffffff", fg="#1c1c1e",
            border="#d1d1d6", font_size=10):
    """Draw a circular number badge using Canvas."""
    c = tk.Canvas(parent, width=size, height=size, bg=parent["bg"],
                  highlightthickness=0)
    c.create_oval(1, 1, size - 1, size - 1,
                  outline=border, width=1.5, fill=bg)
    c.create_text(size // 2, size // 2, text=text,
                  font=("Helvetica Neue", font_size, "bold"), fill=fg)
    return c


def _show_onboarding():
    BG      = "#ffffff"
    TEXT    = "#1c1c1e"
    MUTED   = "#8e8e93"
    SUBTLE  = "#c7c7cc"
    BORDER  = "#e5e5ea"
    NUM_BD  = "#d1d1d6"
    BADGE_BG= "#f2f2f7"
    BADGE_FG= "#6e6e73"
    WARN_BG = "#fffbeb"
    WARN_BD = "#fde68a"
    WARN_FG = "#92400e"
    BTN_BG  = "#1c1c1e"

    root = tk.Tk()
    root.title("Murmur — Setup")
    root.resizable(False, False)
    root.configure(bg=BG)
    root.attributes("-topmost", True)

    W, H = 460, 560
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    PAD = 28

    # ── badge ─────────────────────────────────────────────────────────────────
    badge_frame = tk.Frame(root, bg=BADGE_BG,
                           highlightthickness=1, highlightbackground=BORDER)
    badge_frame.pack(anchor="w", padx=PAD, pady=(14, 0))
    tk.Label(badge_frame, text="One-time setup", bg=BADGE_BG, fg=BADGE_FG,
             font=("Helvetica Neue", 10, "bold"), padx=10, pady=3).pack()

    # ── title ─────────────────────────────────────────────────────────────────
    tk.Label(root, text="Accessibility access needed",
             bg=BG, fg=TEXT, font=("Helvetica Neue", 15, "bold"),
             anchor="w", justify="left").pack(fill="x", padx=PAD, pady=(10, 0))

    tk.Label(root,
             text="Required so Murmur can type into other apps.\nTakes about 30 seconds.",
             bg=BG, fg=MUTED, font=("Helvetica Neue", 11),
             anchor="w", justify="left").pack(fill="x", padx=PAD, pady=(4, 12))

    # ── separator ─────────────────────────────────────────────────────────────
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=PAD)

    # ── timeline steps ────────────────────────────────────────────────────────
    steps = [
        ("Open Accessibility Settings",
         "Click the button below — it opens the right pane directly."),
        ("Add an application",
         f"Click  +  in the Accessibility list."),
        ("Navigate to Python",
         f"Press Cmd+Shift+G, type  /opt/homebrew/bin\nthen select  \"{_PYTHON_BINARY}\"."),
        ("Enable the toggle",
         f"Switch  \"{_PYTHON_BINARY}\"  to ON."),
    ]

    circles = []
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="x", padx=PAD, pady=(10, 0))

    for i, (title, desc) in enumerate(steps):
        is_last = i == len(steps) - 1
        row = tk.Frame(outer, bg=BG)
        row.pack(fill="x")

        # left: circle + connector line
        left = tk.Frame(row, bg=BG, width=34)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        circ = _circle(left, str(i + 1), bg=BG, border=NUM_BD, fg=TEXT)
        circ.pack(pady=(2, 0))
        circles.append(circ)

        if not is_last:
            tk.Frame(left, bg=BORDER, width=1).pack(fill="y", expand=True)

        # right: step text
        right = tk.Frame(row, bg=BG)
        right.pack(side="left", fill="x", expand=True,
                   padx=(10, 0), pady=(2, 12 if not is_last else 0))

        tk.Label(right, text=title, bg=BG, fg=TEXT,
                 font=("Helvetica Neue", 12, "bold"),
                 anchor="w").pack(fill="x")
        tk.Label(right, text=desc, bg=BG, fg=MUTED,
                 font=("Helvetica Neue", 11),
                 anchor="w", justify="left", wraplength=360).pack(fill="x")

    # ── warning ───────────────────────────────────────────────────────────────
    tk.Frame(root, bg=BORDER, height=1).pack(fill="x", padx=PAD, pady=(8, 0))

    warn = tk.Frame(root, bg=WARN_BG,
                    highlightthickness=1, highlightbackground=WARN_BD)
    warn.pack(fill="x", padx=PAD, pady=(8, 0))
    tk.Label(warn,
             text=f"⚠   Murmur appears as \"{_PYTHON_BINARY}\" in the list — not as Murmur.",
             bg=WARN_BG, fg=WARN_FG, font=("Helvetica Neue", 11),
             anchor="w", justify="left", wraplength=370,
             padx=12, pady=8).pack(fill="x")

    # ── button (Frame+Label to force bg color on macOS) ───────────────────────
    btn_frame = tk.Frame(root, bg=BTN_BG, cursor="hand2")
    btn_frame.pack(fill="x", padx=PAD, pady=(14, 0))
    btn_label = tk.Label(btn_frame, text="Open Accessibility Settings  →",
                         bg=BTN_BG, fg="white",
                         font=("Helvetica Neue", 12, "bold"),
                         padx=18, pady=10, cursor="hand2")
    btn_label.pack(fill="x")

    def _open_settings(e=None):
        subprocess.run(["open", SETTINGS_URL])

    btn_frame.bind("<Button-1>", _open_settings)
    btn_label.bind("<Button-1>", _open_settings)

    # ── status ────────────────────────────────────────────────────────────────
    status_var = tk.StringVar(value="Waiting for permission…")
    status_lbl = tk.Label(root, textvariable=status_var,
                          bg=BG, fg=SUBTLE, font=("Helvetica Neue", 10))
    status_lbl.pack(pady=(10, 20))

    def _poll():
        if _has_access():
            badge_frame.winfo_children()[0].config(text="✓  Permission granted")
            for circ in circles:
                circ.delete("all")
                circ.create_oval(1, 1, 25, 25, outline=NUM_BD, width=1.5, fill=BADGE_BG)
                circ.create_text(13, 13, text="✓",
                                 font=("Helvetica Neue", 10, "bold"), fill=MUTED)
            btn_frame.config(bg="#3a3a3c")
            btn_label.config(text="Starting Murmur…", bg="#3a3a3c", state="disabled",
                             cursor="arrow")
            btn_frame.unbind("<Button-1>")
            btn_label.unbind("<Button-1>")
            status_var.set("Permission confirmed — launching")
            root.after(1200, root.destroy)
        else:
            root.after(2000, _poll)

    root.after(2000, _poll)
    root.mainloop()
