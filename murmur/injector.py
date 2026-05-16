import sys
import time
import subprocess
import threading

from pynput.keyboard import Controller, Key

_kb = Controller()
_lock = threading.Lock()


def inject(text: str):
    with _lock:
        if sys.platform == "darwin":
            _inject_mac(text)
        else:
            _inject_win(text)


def _inject_mac(text: str):
    try:
        original = subprocess.run(
            ["pbpaste"], capture_output=True, text=True, timeout=2
        ).stdout
    except (subprocess.SubprocessError, OSError):
        original = ""

    try:
        proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
        proc.communicate(text.encode("utf-8"), timeout=2)

        with _kb.pressed(Key.cmd):
            _kb.press("v")
            _kb.release("v")

        time.sleep(0.15)
    finally:
        # Always restore clipboard even if paste failed
        try:
            proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
            proc.communicate(original.encode("utf-8"), timeout=2)
        except (subprocess.SubprocessError, OSError):
            pass


def _inject_win(text: str):
    import pyperclip
    try:
        original = pyperclip.paste() or ""
    except Exception:
        original = ""

    try:
        pyperclip.copy(text)

        with _kb.pressed(Key.ctrl):
            _kb.press("v")
            _kb.release("v")

        time.sleep(0.15)
    finally:
        try:
            pyperclip.copy(original)
        except Exception:
            pass
