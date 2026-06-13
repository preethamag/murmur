"""
"Fix last transcription" window — runs as subprocess.
Shows the last injected text for editing. On save, compares word-by-word
with the original and auto-adds changed words to Vocabulary Replacements.
"""
import sys
import json
import difflib
import tkinter as tk

from . import vocabulary as vocab_store
from . import theme
from .config import CONFIG_DIR

_LAST_FILE = CONFIG_DIR / ".last.json"
_STRIP_CHARS = ".,!?;:\"'()[]{}"


def _load_last():
    try:
        data = json.loads(_LAST_FILE.read_text(encoding="utf-8"))
        return data.get("raw", ""), data.get("final", "")
    except Exception:
        return "", ""


def _diff_words(original: str, corrected: str) -> list[tuple[str, str]]:
    """Return (wrong, right) pairs for words that changed.

    Uses SequenceMatcher so single-word inserts/deletes don't cascade-misalign
    every subsequent word (which a naive zip would do).
    """
    orig = original.split()
    corr = corrected.split()
    pairs = []
    matcher = difflib.SequenceMatcher(a=orig, b=corr, autojunk=False)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        # Only treat 1-to-1 replacements as a "correction" — multi-word edits
        # are too ambiguous to safely auto-add as vocabulary rules.
        if tag == "replace" and (i2 - i1) == 1 and (j2 - j1) == 1:
            o_clean = orig[i1].strip(_STRIP_CHARS)
            c_clean = corr[j1].strip(_STRIP_CHARS)
            if o_clean and c_clean and o_clean.lower() != c_clean.lower():
                pairs.append((o_clean, c_clean))
    return pairs


class FixWindow:
    W = 520

    def __init__(self):
        self._raw, self._final = _load_last()
        if not self._final:
            sys.exit(1)

        root = tk.Tk()
        theme.setup_window(root, "Murmur — Fix Last Transcription", self.W)

        self._root = root
        self._build(root)

        theme.center_window(root, self.W)
        root.mainloop()

    def _build(self, root):
        theme.header(root, "Fix Transcription",
                     "Edit the text below — changed words are auto-added\n"
                     "to your vocabulary for future transcriptions.")
        theme.separator(root, top=10, bottom=8)

        # ── Text editor ──────────────────────────────────────────────────
        self._text = tk.Text(root, height=6, wrap="word", font=theme.BODY,
                             bg=theme.FIELD_BG, fg=theme.TEXT,
                             relief="solid", bd=1, padx=8, pady=8,
                             highlightthickness=0,
                             insertbackground=theme.TEXT)
        self._text.insert("1.0", self._final)
        self._text.pack(fill="x", padx=theme.PAD, pady=(0, 4))
        self._text.focus()
        self._text.mark_set("insert", "end")

        # ── Status ───────────────────────────────────────────────────────
        self._status = tk.Label(root, text="", bg=theme.BG, fg=theme.MUTED,
                                font=theme.SMALL)
        self._status.pack(anchor="w", padx=theme.PAD, pady=(0, 4))

        # ── Buttons ──────────────────────────────────────────────────────
        theme.separator(root, top=4, bottom=12)

        btn_frame = tk.Frame(root, bg=theme.BG)
        btn_frame.pack(fill="x", padx=theme.PAD, pady=(0, theme.PAD))

        save = theme.dark_button(btn_frame, "Save & Learn", self._save)
        save.pack(side="left", fill="x", expand=True, padx=(0, 6))

        cancel = theme.outline_button(btn_frame, "  Cancel  ",
                                      self._root.destroy)
        cancel.pack(side="left")

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
                text=f"Added {len(pairs)} correction(s) to vocabulary.",
                fg=theme.GREEN,
            )
            self._root.after(1200, lambda: (self._root.destroy(), sys.exit(0)))
        else:
            self._root.destroy()
            sys.exit(0)


if __name__ == "__main__":
    FixWindow()
