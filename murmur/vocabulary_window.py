"""
Vocabulary manager — runs as a subprocess.
Tab 1 — Replacements: definite substitutions, always applied.
Tab 2 — Context Words: give Murmur a list of possible forms; the LLM picks the right one.
Exits with code 0 on Save so the main process can reload vocabulary.
"""
import sys
import tkinter as tk
from tkinter import ttk

from . import vocabulary as vocab_store


class VocabularyWindow:
    W, H = 560, 440

    def __init__(self):
        self._vocab = vocab_store.load()

        root = tk.Tk()
        root.title("Murmur — Vocabulary")
        root.resizable(False, False)
        root.attributes("-topmost", True)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}")

        self._root = root
        self._build(root)
        root.mainloop()

    def _build(self, root):
        nb = ttk.Notebook(root)
        nb.pack(fill="both", expand=True, padx=16, pady=(12, 4))

        f1 = tk.Frame(nb)
        nb.add(f1, text="  Replacements  ")
        self._build_replacements(f1)

        f2 = tk.Frame(nb)
        nb.add(f2, text="  Context Words  ")
        self._build_context(f2)

        ttk.Separator(root, orient="horizontal").pack(fill="x", pady=(4, 0))
        tk.Button(root, text="  Save  ", command=self._save,
                  padx=12, pady=4).pack(pady=(8, 14))

    # ── Replacements ───────────────────────────────────────────────────────────

    def _build_replacements(self, parent):
        tk.Label(
            parent,
            text="Always replace a heard word with an exact substitute.",
            fg="gray", font=("", 11),
        ).pack(anchor="w", padx=16, pady=(8, 2))

        self._rep_tree = ttk.Treeview(
            parent, columns=("hear", "replace"), show="headings", height=9
        )
        self._rep_tree.heading("hear", text="Murmur hears")
        self._rep_tree.heading("replace", text="Type instead")
        self._rep_tree.column("hear", width=220)
        self._rep_tree.column("replace", width=220)
        self._rep_tree.pack(fill="both", expand=True, padx=16, pady=4)

        for wrong, right in self._vocab["replacements"].items():
            self._rep_tree.insert("", "end", values=(wrong, right))

        btn = tk.Frame(parent)
        btn.pack(pady=4)
        tk.Button(btn, text="+ Add", command=self._add_replacement, padx=8).pack(side="left", padx=4)
        tk.Button(btn, text="− Remove", command=lambda: self._remove(self._rep_tree), padx=8).pack(side="left", padx=4)

    def _add_replacement(self):
        _Dialog(
            self._root, "Add Replacement",
            [("Murmur hears:", "e.g.  dont"), ("Type instead:", "e.g.  don't")],
            lambda vals: self._rep_tree.insert("", "end", values=vals),
        )

    # ── Context Words ──────────────────────────────────────────────────────────

    def _build_context(self, parent):
        tk.Label(
            parent,
            text="List possible forms — the AI picks the right one based on context.",
            fg="gray", font=("", 11),
        ).pack(anchor="w", padx=16, pady=(8, 2))
        tk.Label(
            parent,
            text='Example: "lamps, LAMS"  |  "claude, Claude, CLAUDE"',
            fg="gray", font=("", 10),
        ).pack(anchor="w", padx=16)

        self._ctx_tree = ttk.Treeview(
            parent, columns=("forms",), show="headings", height=9
        )
        self._ctx_tree.heading("forms", text="Possible forms (comma-separated)")
        self._ctx_tree.column("forms", width=460)
        self._ctx_tree.pack(fill="both", expand=True, padx=16, pady=4)

        for entry in self._vocab["context_words"]:
            forms = entry.get("forms", [])
            self._ctx_tree.insert("", "end", values=(", ".join(forms),))

        btn = tk.Frame(parent)
        btn.pack(pady=4)
        tk.Button(btn, text="+ Add", command=self._add_context, padx=8).pack(side="left", padx=4)
        tk.Button(btn, text="− Remove", command=lambda: self._remove(self._ctx_tree), padx=8).pack(side="left", padx=4)

    def _add_context(self):
        _Dialog(
            self._root, "Add Context Word Group",
            [("Possible forms:", "e.g.  lamps, LAMS, Lams")],
            lambda vals: self._ctx_tree.insert("", "end", values=vals),
        )

    # ── Shared ─────────────────────────────────────────────────────────────────

    def _remove(self, tree):
        for item in tree.selection():
            tree.delete(item)

    def _save(self):
        replacements = {}
        for item in self._rep_tree.get_children():
            wrong, right = self._rep_tree.item(item)["values"]
            replacements[str(wrong)] = str(right)

        context_words = []
        for item in self._ctx_tree.get_children():
            raw = self._ctx_tree.item(item)["values"][0]
            forms = [f.strip() for f in str(raw).split(",") if f.strip()]
            if forms:
                context_words.append({"forms": forms})

        self._vocab["replacements"] = replacements
        self._vocab["context_words"] = context_words
        vocab_store.save(self._vocab)
        self._root.destroy()
        sys.exit(0)


# ── Generic add dialog ─────────────────────────────────────────────────────────

class _Dialog(tk.Toplevel):
    """Generic 1-or-2-field add dialog. Calls on_save(tuple_of_values) on confirm."""

    def _fg_color(self):
        try:
            bg = self.winfo_rgb(self.cget("bg"))
            luminance = (bg[0] * 0.299 + bg[1] * 0.587 + bg[2] * 0.114) / 65535
            return "white" if luminance < 0.5 else "black"
        except Exception:
            return "black"

    def __init__(self, parent, title, fields, on_save):
        super().__init__(parent)
        self._on_save = on_save
        self._entries = []

        self.title(title)
        self.resizable(False, False)
        self.attributes("-topmost", True)
        self.grab_set()

        for i, (label, placeholder) in enumerate(fields):
            tk.Label(self, text=label, anchor="w").grid(
                row=i, column=0, padx=(16, 8), pady=(14 if i == 0 else 6, 6), sticky="w"
            )
            e = tk.Entry(self, width=28)
            e.insert(0, "")
            e.grid(row=i, column=1, padx=(0, 16), pady=(14 if i == 0 else 6, 6))
            # show placeholder hint in gray; clear on focus
            e.insert(0, placeholder)
            e.config(fg="gray")
            e.bind("<FocusIn>", lambda ev, entry=e, ph=placeholder: (
                entry.delete(0, "end") if entry.get() == ph else None,
                entry.config(fg=self._fg_color()),
            ))
            self._entries.append((e, placeholder))

        tk.Button(self, text="Add", command=self._add, padx=10).grid(
            row=len(fields), column=0, columnspan=2, pady=12
        )
        if self._entries:
            self._entries[0][0].focus()

    def _add(self):
        vals = tuple(
            e.get().strip() for e, ph in self._entries
            if e.get().strip() and e.get().strip() != ph
        )
        if len(vals) == len(self._entries):
            self._on_save(vals)
            self.destroy()


if __name__ == "__main__":
    VocabularyWindow()
