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
from . import theme


class VocabularyWindow:
    W, H = 560, 500

    def __init__(self):
        self._vocab = vocab_store.load()

        root = tk.Tk()
        theme.setup_window(root, "Murmur — Vocabulary", self.W)

        self._root = root
        self._build(root)

        sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
        root.geometry(f"{self.W}x{self.H}+{(sw-self.W)//2}+{(sh-self.H)//2}")
        root.mainloop()

    def _build(self, root):
        theme.header(root, "Vocabulary",
                     "Teach Murmur your terminology and preferred spellings.")
        theme.separator(root, top=10, bottom=4)

        # ── Custom tabs ──────────────────────────────────────────────────
        tab_bar = tk.Frame(root, bg=theme.BG)
        tab_bar.pack(fill="x", padx=theme.PAD, pady=(0, 8))

        self._tab_frames = {}
        self._tab_buttons = {}

        for name in ("Replacements", "Context Words"):
            btn = tk.Label(
                tab_bar, text=f"  {name}  ", bg=theme.FIELD_BG, fg=theme.TEXT,
                font=theme.LABEL, padx=12, pady=6, cursor="hand2",
            )
            btn.pack(side="left", padx=(0, 4))
            btn.bind("<Button-1>", lambda e, n=name: self._switch_tab(n))
            self._tab_buttons[name] = btn

        # Tab content frames
        self._content = tk.Frame(root, bg=theme.BG)
        self._content.pack(fill="both", expand=True, padx=theme.PAD)

        f1 = tk.Frame(self._content, bg=theme.BG)
        self._tab_frames["Replacements"] = f1
        self._build_replacements(f1)

        f2 = tk.Frame(self._content, bg=theme.BG)
        self._tab_frames["Context Words"] = f2
        self._build_context(f2)

        self._switch_tab("Replacements")

        # ── Save ─────────────────────────────────────────────────────────
        theme.separator(root, top=4, bottom=12)
        btn = theme.dark_button(root, "Save Vocabulary", self._save)
        btn.pack(fill="x", padx=theme.PAD, pady=(0, theme.PAD))

    def _switch_tab(self, name):
        for n, frame in self._tab_frames.items():
            if n == name:
                frame.pack(fill="both", expand=True)
                self._tab_buttons[n].config(bg=theme.BTN_BG, fg=theme.BTN_FG)
            else:
                frame.pack_forget()
                self._tab_buttons[n].config(bg=theme.FIELD_BG, fg=theme.TEXT)

    # ── Replacements ──────────────────────────────────────────────────────────

    def _build_replacements(self, parent):
        tk.Label(
            parent, text="Always replace a heard word with an exact substitute.",
            bg=theme.BG, fg=theme.MUTED, font=theme.SUBTITLE,
        ).pack(anchor="w", pady=(4, 6))

        # Treeview with styled header
        style = ttk.Style()
        style.configure("Vocab.Treeview", font=theme.BODY, rowheight=26,
                        background=theme.BG, fieldbackground=theme.BG,
                        foreground=theme.TEXT)
        style.configure("Vocab.Treeview.Heading", font=theme.LABEL)

        self._rep_tree = ttk.Treeview(
            parent, columns=("hear", "replace"), show="headings", height=8,
            style="Vocab.Treeview",
        )
        self._rep_tree.heading("hear", text="Murmur hears")
        self._rep_tree.heading("replace", text="Type instead")
        self._rep_tree.column("hear", width=220)
        self._rep_tree.column("replace", width=220)
        self._rep_tree.pack(fill="both", expand=True, pady=(0, 6))

        for wrong, right in self._vocab["replacements"].items():
            self._rep_tree.insert("", "end", values=(wrong, right))

        btn_frame = tk.Frame(parent, bg=theme.BG)
        btn_frame.pack(pady=(0, 4))
        add = theme.outline_button(btn_frame, "  + Add  ", self._add_replacement)
        add.pack(side="left", padx=4)
        rem = theme.outline_button(btn_frame, "  - Remove  ",
                                   lambda: self._remove(self._rep_tree))
        rem.pack(side="left", padx=4)

    def _add_replacement(self):
        _Dialog(
            self._root, "Add Replacement",
            [("Murmur hears:", "e.g.  dont"), ("Type instead:", "e.g.  don't")],
            lambda vals: self._rep_tree.insert("", "end", values=vals),
        )

    # ── Context Words ─────────────────────────────────────────────────────────

    def _build_context(self, parent):
        tk.Label(
            parent,
            text="List possible forms — the AI picks the right one based on context.",
            bg=theme.BG, fg=theme.MUTED, font=theme.SUBTITLE,
        ).pack(anchor="w", pady=(4, 2))
        tk.Label(
            parent,
            text='"lamps, LAMS"  |  "claude, Claude, CLAUDE"',
            bg=theme.BG, fg=theme.SUBTLE, font=theme.SMALL,
        ).pack(anchor="w", pady=(0, 6))

        self._ctx_tree = ttk.Treeview(
            parent, columns=("forms",), show="headings", height=8,
            style="Vocab.Treeview",
        )
        self._ctx_tree.heading("forms", text="Possible forms (comma-separated)")
        self._ctx_tree.column("forms", width=460)
        self._ctx_tree.pack(fill="both", expand=True, pady=(0, 6))

        for entry in self._vocab["context_words"]:
            forms = entry.get("forms", [])
            self._ctx_tree.insert("", "end", values=(", ".join(forms),))

        btn_frame = tk.Frame(parent, bg=theme.BG)
        btn_frame.pack(pady=(0, 4))
        add = theme.outline_button(btn_frame, "  + Add  ", self._add_context)
        add.pack(side="left", padx=4)
        rem = theme.outline_button(btn_frame, "  - Remove  ",
                                   lambda: self._remove(self._ctx_tree))
        rem.pack(side="left", padx=4)

    def _add_context(self):
        _Dialog(
            self._root, "Add Context Word Group",
            [("Possible forms:", "e.g.  lamps, LAMS, Lams")],
            lambda vals: self._ctx_tree.insert("", "end", values=vals),
        )

    # ── Shared ────────────────────────────────────────────────────────────────

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


# ── Generic add dialog ────────────────────────────────────────────────────────

class _Dialog(tk.Toplevel):
    """Generic 1-or-2-field add dialog. Calls on_save(tuple_of_values) on confirm."""

    def __init__(self, parent, title, fields, on_save):
        super().__init__(parent)
        self._on_save = on_save
        self._entries = []

        self.title(f"Murmur — {title}")
        self.resizable(False, False)
        self.configure(bg=theme.BG)
        self.attributes("-topmost", True)
        self.grab_set()

        # Title
        tk.Label(self, text=title, bg=theme.BG, fg=theme.TEXT,
                 font=theme.TITLE, anchor="w").pack(
            fill="x", padx=theme.PAD, pady=(theme.PAD, 8))

        for label, placeholder in fields:
            tk.Label(self, text=label, bg=theme.BG, fg=theme.TEXT,
                     font=theme.LABEL, anchor="w").pack(
                fill="x", padx=theme.PAD, pady=(4, 2))
            e = tk.Entry(self, width=32, font=theme.BODY,
                         bg=theme.FIELD_BG, fg=theme.TEXT,
                         relief="solid", bd=1, highlightthickness=0,
                         insertbackground=theme.TEXT)
            e.pack(fill="x", padx=theme.PAD, pady=(0, 4))
            # Placeholder hint
            e.insert(0, placeholder)
            e.config(fg=theme.SUBTLE)
            e.bind("<FocusIn>", lambda ev, entry=e, ph=placeholder: (
                entry.delete(0, "end") if entry.get() == ph else None,
                entry.config(fg=theme.TEXT),
            ))
            self._entries.append((e, placeholder))

        # Add button
        theme.separator(self, top=8, bottom=12)
        btn = theme.dark_button(self, "Add", self._add)
        btn.pack(fill="x", padx=theme.PAD, pady=(0, theme.PAD))

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
