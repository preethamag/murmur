"""
"Fix last transcription" window — runs as subprocess.
Shows the last injected text for editing. On save, compares word-by-word
with the original and auto-adds changed words to Vocabulary Replacements.
"""
import sys
import json
import tkinter as tk
from tkinter import ttk

from . import vocabulary as vocab_store
from .config import CONFIG_DIR

_LAST_FILE = CONFIG_DIR / ".last.json"


def _load_last():
    try:
        data = json.loads(_LAST_FILE.read_text(encoding="utf-8"))
        return data.get("raw", ""), data.get("final", "")
    except Exception:
        return "", ""


def _diff_words(original: str, corrected: str) -> list[tuple[str, str]]:
    """Return (wrong, right) pairs for words that changed."""
    orig_words = original.split()
    corr_words = corrected.split()
    pairs = []
    for o, c in zip(orig_words, corr_words):
        o_clean = o.strip(".,!?;:\"'")
        c_clean = c.strip(".,!?;:\"'")
        if o_clean and c_clean and o_clean.lower() != c_clean.lower():
            pairs.append((o_clean, c_clean))
    return pairs


class FixWindow:
    W, H = 480, 260

    def __init__(self):
        self._raw, self._final = _load_last()
        if not self._final:
            sys.exit(1)

        root = tk.Tk()
        root.title("Fix Last Transcription")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}")

        self._root = root
        self._build(root)
        root.mainloop()

    def _build(self, root):
        tk.Label(root, text="Correct the transcription — changed words are auto-added to vocabulary.",
                 fg="gray", font=("", 11)).pack(anchor="w", padx=14, pady=(12, 4))

        self._text = tk.Text(root, height=5, wrap="word", font=("", 13),
                             relief="solid", bd=1)
        self._text.insert("1.0", self._final)
        self._text.pack(fill="x", padx=14, pady=(0, 8))
        self._text.focus()
        self._text.mark_set("insert", "end")

        self._status = tk.Label(root, text="", fg="gray", font=("", 10))
        self._status.pack(anchor="w", padx=14)

        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=(8, 0))

        btn_frame = tk.Frame(root)
        btn_frame.pack(pady=8)
        tk.Button(btn_frame, text="  Save & Learn  ", command=self._save,
                  padx=10, pady=4).pack(side="left", padx=6)
        tk.Button(btn_frame, text="Cancel", command=root.destroy,
                  padx=10, pady=4).pack(side="left", padx=6)

    def _save(self):
        corrected = self._text.get("1.0", "end").strip()
        if not corrected or corrected == self._final:
            self._root.destroy()
            sys.exit(0)

        # Find changed words and add to vocabulary replacements
        pairs = _diff_words(self._final, corrected)
        if pairs:
            vocab = vocab_store.load()
            for wrong, right in pairs:
                vocab["replacements"][wrong] = right
            vocab_store.save(vocab)
            self._status.config(
                text=f"✓ Added {len(pairs)} correction(s) to vocabulary.", fg="green"
            )
            self._root.after(1200, lambda: (self._root.destroy(), sys.exit(0)))
        else:
            self._root.destroy()
            sys.exit(0)


if __name__ == "__main__":
    FixWindow()
