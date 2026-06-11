"""
Checks for macOS Accessibility permission on first launch.
Shows a guided onboarding window that deep-links to System Settings
and auto-detects when the user grants access.

When running as a .app bundle (via PyInstaller), the app IS its own
responsible process — so the Accessibility dialog shows "Murmur" and
the user just needs to click + and add Murmur.app. No Finder reveal needed.

When running as a CLI script (via `python -m murmur` or `murmur`), the
responsible process is the python3.X binary, and the user must drag
the real binary into the Accessibility list.
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

# The real on-disk binary the venv symlink resolves to. macOS keys Accessibility
# permission to this resolved Mach-O binary, and — unlike the /opt/homebrew/bin
# symlink — it is selectable/draggable in the Accessibility picker.
_REAL_BIN = os.path.realpath(sys.executable)


def _is_app_bundle() -> bool:
    """Return True if we are running inside a PyInstaller .app bundle."""
    return getattr(sys, "frozen", False)


def check():
    """Block until Accessibility permission is granted. No-op on non-macOS."""
    if sys.platform != "darwin":
        return
    if _has_access():
        return
    if getattr(sys, "frozen", False):
        subprocess.run([sys.executable, "--permissions"])
    else:
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

    is_bundle = _is_app_bundle()

    root = tk.Tk()
    root.title("Murmur — Setup")
    root.resizable(False, False)
    root.configure(bg=BG)
    root.attributes("-topmost", True)


    W = 460
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
    if is_bundle:
        # .app bundle: Murmur shows up as "Murmur" in the Accessibility list
        steps = [
            ("Open Accessibility Settings",
             "Click the dark button below — it opens the right pane directly."),
            ("Click the  +  button",
             "In the Accessibility list, click the  +  button to add an app."),
            ("Select Murmur",
             "Navigate to Applications and select Murmur, then click Open."),
            ("Enable the toggle",
             'Switch "Murmur" to ON.'),
        ]
    else:
        # CLI mode: process shows as python3.X
        steps = [
            ("Open Accessibility Settings",
             "Click the dark button below — it opens the right pane directly."),
            ("Reveal Python in Finder",
             f'Click "Reveal {_PYTHON_BINARY}" below — Finder opens with the\n'
             "real binary already highlighted."),
            ("Drag it into the list",
             f'Drag the highlighted "{_PYTHON_BINARY}" from Finder onto the\n'
             "Accessibility list."),
            ("Enable the toggle",
             f'Switch  "{_PYTHON_BINARY}"  to ON.'),
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

    if is_bundle:
        warn = tk.Frame(root, bg=BADGE_BG,
                        highlightthickness=1, highlightbackground=BORDER)
        warn.pack(fill="x", padx=PAD, pady=(8, 0))
        tk.Label(warn,
                 text='Look for "Murmur" in the Accessibility list.\n'
                      "If you installed to ~/Applications, navigate there in the + dialog.",
                 bg=BADGE_BG, fg=BADGE_FG, font=("Helvetica Neue", 11),
                 anchor="w", justify="left", wraplength=370,
                 padx=12, pady=8).pack(fill="x")
    else:
        warn = tk.Frame(root, bg=WARN_BG,
                        highlightthickness=1, highlightbackground=WARN_BD)
        warn.pack(fill="x", padx=PAD, pady=(8, 0))
        tk.Label(warn,
                 text=f'⚠   Drag it in — the  +  button greys out "{_PYTHON_BINARY}". '
                      "It appears in the list as Python, not as Murmur.",
                 bg=WARN_BG, fg=WARN_FG, font=("Helvetica Neue", 11),
                 anchor="w", justify="left", wraplength=370,
                 padx=12, pady=8).pack(fill="x")

    # ── button (Frame+Label to force bg color on macOS) ───────────────────────
    btn_frame = tk.Frame(root, bg=BTN_BG, cursor="hand2")
    btn_frame.pack(fill="x", padx=PAD, pady=(12, 0))
    btn_label = tk.Label(btn_frame, text="Open Accessibility Settings  →",
                         bg=BTN_BG, fg="white",
                         font=("Helvetica Neue", 12, "bold"),
                         padx=18, pady=10, cursor="hand2")
    btn_label.pack(fill="x")

    def _open_settings(e=None):
        subprocess.run(["open", SETTINGS_URL])

    btn_frame.bind("<Button-1>", _open_settings)
    btn_label.bind("<Button-1>", _open_settings)

    # ── secondary button: reveal real binary in Finder (CLI mode only) ────────
    if not is_bundle:
        reveal_wrap = tk.Frame(root, bg=NUM_BD)  # 1px border via bg
        reveal_wrap.pack(fill="x", padx=PAD, pady=(8, 0))
        reveal_label = tk.Label(reveal_wrap, text=f"Reveal {_PYTHON_BINARY} in Finder",
                                bg=BADGE_BG, fg=TEXT,
                                font=("Helvetica Neue", 11, "bold"),
                                padx=14, pady=8, cursor="hand2")
        reveal_label.pack(fill="x", padx=1, pady=1)

        def _reveal(e=None):
            subprocess.run(["open", "-R", _REAL_BIN])

        reveal_wrap.bind("<Button-1>", _reveal)
        reveal_label.bind("<Button-1>", _reveal)

    # ── status ────────────────────────────────────────────────────────────────
    status_var = tk.StringVar(value="Waiting for permission…")
    status_lbl = tk.Label(root, textvariable=status_var,
                          bg=BG, fg=SUBTLE, font=("Helvetica Neue", 10))
    status_lbl.pack(pady=(10, 28))

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

    # Size the window to fit its content exactly, then center it.
    root.update_idletasks()
    H = root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    root.after(2000, _poll)
    root.mainloop()
