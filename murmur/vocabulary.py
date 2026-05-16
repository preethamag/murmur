"""
Loads and saves ~/.murmur/vocabulary.yaml.

Schema:
  replacements:          # always applied, no LLM needed
    "hears": "here's"
    "dont": "don't"
  context_words:         # LLM picks the right form based on sentence context
    - forms: [lamps, LAMS]
    - forms: [claude, Claude, CLAUDE]
"""
import os
import sys
import yaml
from .config import CONFIG_DIR

VOCAB_FILE = CONFIG_DIR / "vocabulary.yaml"

_EMPTY = {
    "replacements": {},
    "context_words": [],
}


def load():
    empty = {k: v.copy() if isinstance(v, dict) else list(v) for k, v in _EMPTY.items()}
    if not VOCAB_FILE.exists():
        return empty
    try:
        with open(VOCAB_FILE) as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            data = {}
    except (yaml.YAMLError, OSError):
        return empty
    return {**empty, **data}


def save(vocab):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(VOCAB_FILE, "w") as f:
        yaml.dump(vocab, f, default_flow_style=False, allow_unicode=True)
    if sys.platform != "win32":
        try:
            os.chmod(VOCAB_FILE, 0o600)
        except OSError:
            pass
