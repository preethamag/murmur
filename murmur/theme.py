"""
Shared visual theme for Murmur tkinter windows.
Matches the permissions dialog's Obsidian design language.
"""
import tkinter as tk
from tkinter import ttk

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = "#ffffff"
TEXT     = "#1c1c1e"
MUTED    = "#8e8e93"
SUBTLE   = "#c7c7cc"
BORDER   = "#e5e5ea"
BADGE_BG = "#f2f2f7"
BADGE_FG = "#6e6e73"
BTN_BG   = "#1c1c1e"
BTN_FG   = "#ffffff"
BTN_HOVER = "#3a3a3c"
GREEN    = "#34c759"

# ── Fonts ─────────────────────────────────────────────────────────────────────
FONT         = "Helvetica Neue"
TITLE        = (FONT, 15, "bold")
SUBTITLE     = (FONT, 11)
LABEL        = (FONT, 11, "bold")
BODY         = (FONT, 12)
SMALL        = (FONT, 10)
SMALL_BOLD   = (FONT, 10, "bold")

# ── Layout ────────────────────────────────────────────────────────────────────
PAD = 24


def setup_window(root, title, width=520):
    """Configure a window with the standard Murmur look."""
    root.title(title)
    root.resizable(False, False)
    root.configure(bg=BG)
    root.attributes("-topmost", True)
    _force_light_mode()
    _apply_ttk_style(root)
    return root


def _force_light_mode():
    """Force the app to render in light mode regardless of macOS dark mode."""
    try:
        from AppKit import NSApplication, NSAppearance
        app = NSApplication.sharedApplication()
        light = NSAppearance.appearanceNamed_("NSAppearanceNameAqua")
        app.setAppearance_(light)
    except Exception:
        pass


def center_window(root, width):
    """Center window on screen after building content."""
    root.update_idletasks()
    H = root.winfo_reqheight()
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{width}x{H}+{(sw - width) // 2}+{(sh - H) // 2}")


def header(parent, title_text, subtitle_text=None):
    """Add a title + optional subtitle at the top of the window."""
    tk.Label(parent, text=title_text, bg=BG, fg=TEXT, font=TITLE,
             anchor="w").pack(fill="x", padx=PAD, pady=(PAD, 0))
    if subtitle_text:
        tk.Label(parent, text=subtitle_text, bg=BG, fg=MUTED, font=SUBTITLE,
                 anchor="w", justify="left").pack(fill="x", padx=PAD, pady=(2, 0))


def separator(parent, top=12, bottom=12):
    """Horizontal separator line."""
    tk.Frame(parent, bg=BORDER, height=1).pack(fill="x", padx=PAD,
                                                pady=(top, bottom))


def field_label(parent, text):
    """Small bold label above a form field."""
    tk.Label(parent, text=text, bg=BG, fg=TEXT, font=LABEL,
             anchor="w").pack(fill="x", padx=PAD, pady=(8, 2))


def dark_button(parent, text, command):
    """Dark filled button matching the permissions dialog style."""
    frame = tk.Frame(parent, bg=BTN_BG, cursor="hand2")
    label = tk.Label(frame, text=text, bg=BTN_BG, fg=BTN_FG,
                     font=(FONT, 12, "bold"), padx=18, pady=9,
                     cursor="hand2")
    label.pack(fill="x")

    def _hover_in(e):
        frame.config(bg=BTN_HOVER)
        label.config(bg=BTN_HOVER)

    def _hover_out(e):
        frame.config(bg=BTN_BG)
        label.config(bg=BTN_BG)

    def _click(e):
        command()

    frame.bind("<Enter>", _hover_in)
    frame.bind("<Leave>", _hover_out)
    frame.bind("<Button-1>", _click)
    label.bind("<Button-1>", _click)
    return frame


def outline_button(parent, text, command):
    """Light bordered button for secondary actions."""
    wrap = tk.Frame(parent, bg=BORDER)
    label = tk.Label(wrap, text=text, bg=BG, fg=TEXT,
                     font=(FONT, 11), padx=14, pady=6,
                     cursor="hand2")
    label.pack(fill="x", padx=1, pady=1)

    def _click(e):
        command()

    wrap.bind("<Button-1>", _click)
    label.bind("<Button-1>", _click)
    return wrap


def _apply_ttk_style(root):
    """Configure ttk styles to blend with the white theme."""
    style = ttk.Style(root)
    try:
        style.theme_use("aqua")
    except tk.TclError:
        pass
    style.configure("Murmur.TCombobox", font=BODY)
    style.configure("Murmur.TCheckbutton", background=BG, font=BODY)
    style.configure("Murmur.TNotebook", background=BG)
    style.configure("Murmur.TNotebook.Tab", font=LABEL, padding=[16, 6])
    style.configure("Murmur.Treeview", font=BODY, rowheight=26)
    style.configure("Murmur.Treeview.Heading", font=LABEL)
