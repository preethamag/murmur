"""
Checks for macOS Accessibility permission on first launch.
If missing, shows a guided onboarding window that deep-links to the right
System Settings pane and auto-detects when the user grants access.
"""

import os
import sys
import subprocess
import tkinter as tk

SETTINGS_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)

# The name Python appears under in System Settings → Accessibility
_PYTHON_BINARY = os.path.basename(sys.executable)  # e.g. "python3", "python3.12"


def check():
    """Block until Accessibility permission is granted. No-op on Windows."""
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
        return True  # can't check — assume granted so we don't block forever


def _show_onboarding():
    BG      = "#1c1c1e"
    SURFACE = "#2c2c2e"
    BORDER  = "#3a3a3c"
    PURPLE  = "#7c6af7"
    TEXT    = "#f2f2f7"
    MUTED   = "#8e8e93"
    WARN_BG = "#2d2200"
    WARN_FG = "#ffd60a"

    root = tk.Tk()
    root.title("Murmur — Setup")
    root.resizable(False, False)
    root.configure(bg=BG)
    root.attributes("-topmost", True)

    W, H = 460, 420
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    # ── header ────────────────────────────────────────────────────────────────
    tk.Label(
        root, text="One permission needed",
        bg=BG, fg=TEXT,
        font=("SF Pro Display", 17, "bold"),
        anchor="w",
    ).pack(fill="x", padx=28, pady=(28, 4))

    tk.Label(
        root,
        text="Murmur needs Accessibility access to type into other apps.",
        bg=BG, fg=MUTED,
        font=("SF Pro Display", 12),
        anchor="w", wraplength=400, justify="left",
    ).pack(fill="x", padx=28, pady=(0, 20))

    # ── steps ─────────────────────────────────────────────────────────────────
    steps_frame = tk.Frame(root, bg=BG)
    steps_frame.pack(fill="x", padx=28)

    steps = [
        "Click  Open Accessibility Settings  below",
        "Click the  +  button to add an app",
        f'Navigate to your Python install and select it,\nor search for  "{_PYTHON_BINARY}"  in the list',
        "Toggle Murmur  ON  — it will start automatically",
    ]

    for i, text in enumerate(steps, 1):
        row = tk.Frame(steps_frame, bg=BG)
        row.pack(fill="x", pady=5)

        num = tk.Frame(row, bg=PURPLE, width=22, height=22)
        num.pack(side="left", anchor="n", pady=3)
        num.pack_propagate(False)
        tk.Label(num, text=str(i), bg=PURPLE, fg="white",
                 font=("SF Pro Display", 10, "bold")).pack(expand=True)

        tk.Label(
            row, text=text,
            bg=BG, fg=TEXT,
            font=("SF Pro Display", 12),
            anchor="w", justify="left", wraplength=375,
        ).pack(side="left", padx=10)

    # ── warning callout ───────────────────────────────────────────────────────
    warn = tk.Frame(root, bg=WARN_BG, padx=14, pady=10)
    warn.pack(fill="x", padx=28, pady=(16, 0))

    tk.Label(
        warn,
        text=f"⚠  Murmur appears as  \"{_PYTHON_BINARY}\"  in the list — not as Murmur.",
        bg=WARN_BG, fg=WARN_FG,
        font=("SF Pro Display", 11, "bold"),
        anchor="w", justify="left", wraplength=390,
    ).pack(fill="x")

    # ── button ────────────────────────────────────────────────────────────────
    btn_frame = tk.Frame(root, bg=BG)
    btn_frame.pack(fill="x", padx=28, pady=(20, 0))

    btn = tk.Button(
        btn_frame,
        text="Open Accessibility Settings  →",
        command=lambda: subprocess.run(["open", SETTINGS_URL]),
        bg=PURPLE, fg="white", activebackground="#6254d4", activeforeground="white",
        font=("SF Pro Display", 12, "bold"),
        bd=0, padx=18, pady=10, cursor="hand2", relief="flat",
    )
    btn.pack(fill="x")

    # ── status ────────────────────────────────────────────────────────────────
    status_var = tk.StringVar(value="Waiting for permission…")
    status_lbl = tk.Label(
        root, textvariable=status_var,
        bg=BG, fg=MUTED,
        font=("SF Pro Display", 11),
    )
    status_lbl.pack(pady=(14, 0))

    def _poll():
        if _has_access():
            status_var.set("✓  Permission granted — starting Murmur…")
            status_lbl.config(fg="#30d158")
            root.after(1200, root.destroy)
        else:
            root.after(2000, _poll)

    root.after(2000, _poll)
    root.mainloop()
