import os
import sys
import yaml
from pathlib import Path

if sys.platform == "win32":
    CONFIG_DIR = Path(os.environ.get("APPDATA", Path.home())) / "Murmur"
else:
    CONFIG_DIR = Path.home() / ".murmur"

CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "hotkey": "right_option",
    "model": "base",
    "language": "en",
    "sample_rate": 16000,
    "inject_method": "clipboard",
    "sound_feedback": False,
    "max_duration": 60,
    "ai_cleanup": False,
    "ollama_model": "qwen2.5:1.5b",
    "ollama_url": "http://localhost:11434",
    "device": None,
    "launch_at_login": False,
    "sound_feedback": True,
    "punctuation_commands": True,
}


def load():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        save(DEFAULTS)
        return DEFAULTS.copy()
    with open(CONFIG_FILE) as f:
        data = yaml.safe_load(f) or {}
    return {**DEFAULTS, **data}


def save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
