"""
Checks for macOS Accessibility permission on first launch.
If missing, shows a guided onboarding window that deep-links to the right
System Settings pane and auto-detects when the user grants access.
"""

import sys
import subprocess
import tkinter as tk

SETTINGS_URL = (
    "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
)


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
        return True   # can't check — assume granted so we don't block forever


def _show_onboarding():
    root = tk.Tk()
    root.title("Murmur — Setup")
    root.resizable(False, False)
    root.attributes("-topmost", True)

    W, H = 420, 340
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")

    # ── header ────────────────────────────────────────────────────────────────
    tk.Label(
        root, text="Murmur — First Launch",
        font=("SF Pro Display", 15, "bold"),
    ).pack(pady=(28, 4))

    tk.Label(
        root,
        text="One permission is needed so Murmur can type into other apps.",
        font=("SF Pro Display", 11), fg="#555555", wraplength=360,
    ).pack(pady=(0, 22))

    # ── steps ─────────────────────────────────────────────────────────────────
    steps_frame = tk.Frame(root, padx=40)
    steps_frame.pack(fill="x")

    for i, text in enumerate([
        "Click the button below",
        'Click the lock icon  "Click to make changes"',
        "Find  Murmur  in the list and toggle it  ON",
        "Come back here — Murmur starts automatically",
    ], 1):
        tk.Label(
            steps_frame, text=f"{i}.   {text}",
            anchor="w", justify="left",
            font=("SF Pro Display", 11),
        ).pack(fill="x", pady=3)

    tk.Frame(root, height=20).pack()

    # ── button ────────────────────────────────────────────────────────────────
    def _open():
        subprocess.run(["open", SETTINGS_URL])

    tk.Button(
        root, text="Open Accessibility Settings  →",
        command=_open, padx=16, pady=7,
        font=("SF Pro Display", 11, "bold"),
        cursor="hand2",
    ).pack()

    tk.Frame(root, height=18).pack()

    # ── status ────────────────────────────────────────────────────────────────
    status = tk.StringVar(value="⏳   Waiting for permission…")
    lbl = tk.Label(root, textvariable=status,
                   font=("SF Pro Display", 11), fg="#888888")
    lbl.pack()

    def _poll():
        if _has_access():
            status.set("✓   Permission granted! Starting Murmur…")
            lbl.config(fg="#34c759")          # green
            root.after(1200, root.destroy)    # short pause so user sees it
        else:
            root.after(2000, _poll)

    root.after(2000, _poll)
    root.mainloop()
