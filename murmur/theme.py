"""
Shared visual theme for Murmur tkinter windows.
Matches the permissions dialog's Obsidian design language.
Uses only plain tk widgets (no ttk) for full color control on macOS dark mode.
"""
import tkinter as tk

# ── Colors ────────────────────────────────────────────────────────────────────
BG       = "#ffffff"
TEXT     = "#1c1c1e"
MUTED    = "#8e8e93"
SUBTLE   = "#c7c7cc"
BORDER   = "#e5e5ea"
FIELD_BG = "#f2f2f7"
BADGE_FG = "#6e6e73"
BTN_BG   = "#1c1c1e"
BTN_FG   = "#ffffff"
BTN_HOVER = "#3a3a3c"
GREEN    = "#34c759"
HOVER_BG = "#eaeaee"

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
    return root


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


# ── Custom Dropdown ───────────────────────────────────────────────────────────

class Dropdown(tk.Frame):
    """Custom dropdown selector — pure tk, no ttk, full color control.

    Looks like a light gray rounded field with current value + ▼ arrow.
    Clicking opens a floating list of options.
    """

    def __init__(self, parent, options, current=None, width=None):
        super().__init__(parent, bg=FIELD_BG, highlightthickness=1,
                         highlightbackground=BORDER, cursor="hand2")
        self._options = options
        self._var = tk.StringVar(value=current or (options[0] if options else ""))
        self._popup = None

        self._label = tk.Label(
            self, textvariable=self._var, bg=FIELD_BG, fg=TEXT,
            font=BODY, anchor="w", padx=10, pady=7, cursor="hand2",
        )
        self._label.pack(side="left", fill="x", expand=True)

        self._arrow = tk.Label(
            self, text="▾", bg=FIELD_BG, fg=MUTED,
            font=(FONT, 14), padx=8, cursor="hand2",
        )
        self._arrow.pack(side="right")

        self.bind("<Button-1>", self._toggle)
        self._label.bind("<Button-1>", self._toggle)
        self._arrow.bind("<Button-1>", self._toggle)

    def get(self):
        return self._var.get()

    def set(self, value):
        self._var.set(value)

    def _toggle(self, event=None):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
            self._popup = None
            return
        self._show_popup()

    def _show_popup(self):
        self._popup = popup = tk.Toplevel(self)
        popup.withdraw()
        popup.overrideredirect(True)
        popup.configure(bg=BORDER)
        popup.attributes("-topmost", True)

        inner = tk.Frame(popup, bg=BG)
        inner.pack(fill="both", expand=True, padx=1, pady=1)

        current = self._var.get()
        for opt in self._options:
            is_selected = (opt == current)
            item_bg = FIELD_BG if is_selected else BG
            item = tk.Label(
                inner, text=opt, bg=item_bg, fg=TEXT,
                font=BODY, anchor="w", padx=10, pady=5,
                cursor="hand2",
            )
            item.pack(fill="x")
            item.bind("<Enter>", lambda e, w=item: w.config(bg=HOVER_BG))
            item.bind("<Leave>", lambda e, w=item, sel=is_selected:
                      w.config(bg=FIELD_BG if sel else BG))
            item.bind("<Button-1>", lambda e, v=opt: self._select(v))

        # Position below the dropdown field
        popup.update_idletasks()
        x = self.winfo_rootx()
        y = self.winfo_rooty() + self.winfo_height() + 2
        w = self.winfo_width()
        h = popup.winfo_reqheight()

        # Keep popup on screen
        screen_h = self.winfo_screenheight()
        if y + h > screen_h - 40:
            y = self.winfo_rooty() - h - 2

        popup.geometry(f"{w}x{h}+{x}+{y}")
        popup.deiconify()

        # Close on click outside
        popup.bind("<FocusOut>", lambda e: self._close_popup())
        popup.focus_set()

    def _select(self, value):
        self._var.set(value)
        self._close_popup()

    def _close_popup(self):
        if self._popup and self._popup.winfo_exists():
            self._popup.destroy()
        self._popup = None


# ── Custom Checkbox ───────────────────────────────────────────────────────────

def checkbox(parent, var, title, description=None):
    """Styled checkbox with title and optional description."""
    frame = tk.Frame(parent, bg=BG)
    frame.pack(fill="x", padx=PAD, pady=(4, 4))

    cb = tk.Checkbutton(frame, variable=var, bg=BG,
                        activebackground=BG, highlightthickness=0)
    cb.pack(side="left", padx=(0, 6))

    text_frame = tk.Frame(frame, bg=BG)
    text_frame.pack(side="left", fill="x")
    tk.Label(text_frame, text=title, bg=BG, fg=TEXT,
             font=LABEL, anchor="w").pack(fill="x")
    if description:
        tk.Label(text_frame, text=description, bg=BG, fg=MUTED,
                 font=SMALL, anchor="w").pack(fill="x")
    return frame
