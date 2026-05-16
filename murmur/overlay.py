"""
Overlay subprocess — reads commands from stdin, renders floating waveform pill.

Commands (newline-terminated):
  recording       → show window, animate bars with voice
  level:0.72      → update mic amplitude (0.0–1.0)
  processing      → switch to transcribing pulse animation
  hide            → hide window
"""

import sys
import math
import threading
import tkinter as tk

PILL_W = 260
PILL_H = 60
BAR_COUNT = 5
BAR_W = 7
BAR_GAP = 5
BAR_MAX_H = 32
BAR_MIN_H = 4
RADIUS = 18

BG = "#1c1c1e"
BAR_IDLE_COLOR = "#ffffff"
BAR_PROC_COLOR = "#666666"

if sys.platform == "darwin":
    FONT = ("SF Pro Display", 11)
else:
    FONT = ("Segoe UI", 10)
LABEL_COLOR = "#aeaeb2"


class Overlay:
    def __init__(self):
        self._state = "hidden"
        self._level = 0.0
        self._phase = 0.0

        root = tk.Tk()
        root.overrideredirect(True)
        root.attributes("-topmost", True)
        root.attributes("-alpha", 0.93)
        root.withdraw()

        if sys.platform == "darwin":
            root.attributes("-transparent", True)
            root.config(bg="systemTransparent")
            canvas_bg = "systemTransparent"
        else:
            root.config(bg=BG)
            canvas_bg = BG

        # Position: bottom of screen, shifted left of center
        sw = root.winfo_screenwidth()
        sh = root.winfo_screenheight()
        x = sw // 2 - PILL_W // 2 - 120   # 120px left of center
        y = sh - 90
        root.geometry(f"{PILL_W}x{PILL_H}+{x}+{y}")

        canvas = tk.Canvas(
            root, width=PILL_W, height=PILL_H,
            bg=canvas_bg, highlightthickness=0,
        )
        canvas.pack()

        self._root = root
        self._canvas = canvas
        self._draw_pill()
        self._build_bars()
        self._label = canvas.create_text(
            PILL_W - 16, PILL_H // 2,
            text="Recording...", fill=LABEL_COLOR,
            font=FONT, anchor="e",
        )

        threading.Thread(target=self._read_stdin, daemon=True).start()
        self._tick()
        root.mainloop()

    # ── drawing ───────────────────────────────────────────────────────────────

    def _draw_pill(self):
        c, x1, y1, x2, y2 = self._canvas, 3, 3, PILL_W - 3, PILL_H - 3
        r = RADIUS
        for args in [
            (x1, y1, x1+2*r, y1+2*r, 90,  90),
            (x2-2*r, y1, x2, y1+2*r, 0,   90),
            (x1, y2-2*r, x1+2*r, y2, 180, 90),
            (x2-2*r, y2-2*r, x2, y2, 270, 90),
        ]:
            c.create_arc(*args[:4], start=args[4], extent=args[5], fill=BG, outline="")
        c.create_rectangle(x1+r, y1, x2-r, y2, fill=BG, outline="")
        c.create_rectangle(x1, y1+r, x2, y2-r, fill=BG, outline="")

    def _build_bars(self):
        cy = PILL_H // 2
        total = BAR_COUNT * BAR_W + (BAR_COUNT - 1) * BAR_GAP
        sx = 20  # left margin inside pill
        self._bars = []
        for i in range(BAR_COUNT):
            x = sx + i * (BAR_W + BAR_GAP)
            item = self._canvas.create_rectangle(
                x, cy - BAR_MIN_H // 2,
                x + BAR_W, cy + BAR_MIN_H // 2,
                fill=BAR_IDLE_COLOR, outline="",
            )
            self._bars.append((x, item))

    # ── animation ─────────────────────────────────────────────────────────────

    def _tick(self):
        if self._state == "recording":
            self._animate_recording()
        elif self._state == "processing":
            self._animate_processing()
        self._phase += 0.25
        self._root.after(40, self._tick)   # ~25 fps

    def _animate_recording(self):
        cy = PILL_H // 2
        for i, (x, item) in enumerate(self._bars):
            wave = math.sin(self._phase + i * 0.9) * 0.35 + 0.65
            h = int((self._level * wave + 0.08) * BAR_MAX_H)
            h = max(BAR_MIN_H, min(h, BAR_MAX_H))
            self._canvas.coords(item, x, cy - h//2, x + BAR_W, cy + h//2)
            self._canvas.itemconfig(item, fill=BAR_IDLE_COLOR)
        self._canvas.itemconfig(self._label, text="Recording...")

    def _animate_processing(self):
        cy = PILL_H // 2
        for i, (x, item) in enumerate(self._bars):
            pulse = abs(math.sin(self._phase * 0.8 + i * 0.6)) * 0.25 + 0.05
            h = max(3, int(pulse * BAR_MAX_H))
            self._canvas.coords(item, x, cy - h//2, x + BAR_W, cy + h//2)
            self._canvas.itemconfig(item, fill=BAR_PROC_COLOR)
        self._canvas.itemconfig(self._label, text="Transcribing...")

    # ── stdin reader ──────────────────────────────────────────────────────────

    def _read_stdin(self):
        for raw in sys.stdin:
            cmd = raw.strip()
            if cmd == "recording":
                self._state = "recording"
                self._root.deiconify()
            elif cmd.startswith("level:"):
                try:
                    self._level = float(cmd[6:])
                except ValueError:
                    pass
            elif cmd == "processing":
                self._state = "processing"
            elif cmd == "hide":
                self._state = "hidden"
                self._root.withdraw()


if __name__ == "__main__":
    Overlay()
