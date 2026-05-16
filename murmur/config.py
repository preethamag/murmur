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
    "input_mode": "hold",       # "hold" = push-to-talk | "tap" = tap-to-start + auto-stop
    "silence_threshold": 200,   # RMS energy below this = silence
    "silence_duration": 1.5,    # seconds of silence before auto-stop
}


def load():
    if not CONFIG_FILE.exists():
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        save(DEFAULTS)
        return DEFAULTS.copy()
    try:
        with open(CONFIG_FILE) as f:
            data = yaml.safe_load(f) or {}
        if not isinstance(data, dict):
            data = {}
    except (yaml.YAMLError, OSError):
        # Corrupt or unreadable — fall back to defaults rather than crashing.
        data = {}
    return {**DEFAULTS, **data}


def save(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        yaml.dump(cfg, f, default_flow_style=False)
    if sys.platform != "win32":
        try:
            os.chmod(CONFIG_FILE, 0o600)
        except OSError:
            pass
