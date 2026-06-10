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

_PYTHON_BINARY = os.path.basename(sys.executable)


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


def _show_onboarding():
    BG       = "#ffffff"
    TITLEBAR = "#f5f5f7"
    BORDER   = "#e5e5ea"
    TEXT     = "#1c1c1e"
    MUTED    = "#8e8e93"
    SUBTLE   = "#c7c7cc"
    BADGE_BG = "#f2f2f7"
    BADGE_FG = "#6e6e73"
    CODE_BG  = "#f2f2f7"
    CODE_FG  = "#3a3a3c"
    NUM_BD   = "#d1d1d6"
    WARN_BG  = "#fffbeb"
    WARN_BD  = "#fde68a"
    WARN_FG  = "#92400e"
    BTN_BG   = "#1c1c1e"

    root = tk.Tk()
    root.title("Murmur — Setup")
    root.resizable(False, False)
    root.configure(bg=BG)
    root.attributes("-topmost", True)

    W, H = 480, 530
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    PAD = 32

    # ── title bar ─────────────────────────────────────────────────────────────
    bar = tk.Frame(root, bg=TITLEBAR, height=38,
                   highlightthickness=1, highlightbackground=BORDER)
    bar.pack(fill="x")
    bar.pack_propagate(False)
    tk.Label(bar, text="Murmur — Setup", bg=TITLEBAR, fg=MUTED,
             font=("SF Pro Display", 13)).place(relx=0.5, rely=0.5, anchor="center")

    # ── badge ─────────────────────────────────────────────────────────────────
    badge = tk.Frame(root, bg=BADGE_BG,
                     highlightthickness=1, highlightbackground=BORDER)
    badge.pack(anchor="w", padx=PAD, pady=(24, 0))
    tk.Label(badge, text="🔒  One-time setup", bg=BADGE_BG, fg=BADGE_FG,
             font=("SF Pro Display", 11, "bold"), padx=10, pady=4).pack()

    # ── title + subtitle ──────────────────────────────────────────────────────
    tk.Label(root, text="Accessibility access needed",
             bg=BG, fg=TEXT, font=("SF Pro Display", 20, "bold"),
             anchor="w").pack(fill="x", padx=PAD, pady=(12, 0))

    tk.Label(root,
             text="Required so Murmur can type into other apps.\nTakes about 30 seconds.",
             bg=BG, fg=MUTED, font=("SF Pro Display", 13),
             anchor="w", justify="left").pack(fill="x", padx=PAD, pady=(6, 20))

    # ── timeline steps ────────────────────────────────────────────────────────
    steps = [
        ("Open Accessibility Settings",
         "Click the button below — it opens the right pane directly."),
        ("Add an application",
         "Click  +  in the Accessibility list."),
        ("Navigate to Python",
         f"Press Cmd+Shift+G, type  /opt/homebrew/bin\nthen select  \"{_PYTHON_BINARY}\"."),
        ("Enable the toggle",
         f"Switch  \"{_PYTHON_BINARY}\"  to ON."),
    ]

    num_labels = []
    outer = tk.Frame(root, bg=BG)
    outer.pack(fill="x", padx=PAD)

    for i, (title, desc) in enumerate(steps):
        is_last = i == len(steps) - 1
        row = tk.Frame(outer, bg=BG)
        row.pack(fill="x")

        left = tk.Frame(row, bg=BG, width=36)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        circle = tk.Frame(left, bg=BG, width=28, height=28,
                          highlightthickness=1, highlightbackground=NUM_BD)
        circle.pack(pady=(2, 0))
        circle.pack_propagate(False)
        lbl = tk.Label(circle, text=str(i + 1), bg=BG, fg=TEXT,
                       font=("SF Pro Display", 12, "bold"))
        lbl.place(relx=0.5, rely=0.5, anchor="center")
        num_labels.append((circle, lbl))

        if not is_last:
            tk.Frame(left, bg=BORDER, width=1).pack(fill="y", expand=True)

        right = tk.Frame(row, bg=BG)
        right.pack(side="left", fill="x", expand=True, padx=(10, 0),
                   pady=(2, 18 if not is_last else 0))

        tk.Label(right, text=title, bg=BG, fg=TEXT,
                 font=("SF Pro Display", 13, "bold"), anchor="w").pack(fill="x")
        tk.Label(right, text=desc, bg=BG, fg=MUTED,
                 font=("SF Pro Display", 12), anchor="w",
                 justify="left", wraplength=380).pack(fill="x")

    # ── warning callout ───────────────────────────────────────────────────────
    warn = tk.Frame(root, bg=WARN_BG,
                    highlightthickness=1, highlightbackground=WARN_BD)
    warn.pack(fill="x", padx=PAD, pady=(20, 0))
    tk.Label(warn,
             text=f"⚠   Murmur appears as \"{_PYTHON_BINARY}\" in the list — not as Murmur.",
             bg=WARN_BG, fg=WARN_FG, font=("SF Pro Display", 12),
             anchor="w", justify="left", wraplength=390, padx=14, pady=10).pack(fill="x")

    # ── button ────────────────────────────────────────────────────────────────
    btn = tk.Button(
        root,
        text="Open Accessibility Settings  →",
        command=lambda: subprocess.run(["open", SETTINGS_URL]),
        bg=BTN_BG, fg="white",
        activebackground="#3a3a3c", activeforeground="white",
        font=("SF Pro Display", 13, "bold"),
        bd=0, padx=18, pady=11, cursor="hand2", relief="flat",
    )
    btn.pack(fill="x", padx=PAD, pady=(16, 0))

    # ── status ────────────────────────────────────────────────────────────────
    status_var = tk.StringVar(value="Waiting for permission…")
    status_lbl = tk.Label(root, textvariable=status_var,
                          bg=BG, fg=SUBTLE, font=("SF Pro Display", 11))
    status_lbl.pack(pady=(10, 24))

    def _poll():
        if _has_access():
            # update badge
            badge_lbl = badge.winfo_children()[0]
            badge_lbl.config(text="✓  Permission granted")

            # check all circles
            for circle, lbl in num_labels:
                circle.config(bg=BADGE_BG, highlightbackground=NUM_BD)
                lbl.config(text="✓", bg=BADGE_BG, fg=CODE_FG)

            btn.config(text="Starting Murmur…", bg="#3a3a3c",
                       activebackground="#3a3a3c", state="disabled")
            status_var.set("Permission confirmed — launching")
            status_lbl.config(fg=MUTED)
            root.after(1200, root.destroy)
        else:
            root.after(2000, _poll)

    root.after(2000, _poll)
    root.mainloop()
