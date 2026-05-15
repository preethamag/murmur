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
    # Save current clipboard
    original = subprocess.run(["pbpaste"], capture_output=True, text=True).stdout

    # Set text
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(text.encode("utf-8"))

    # Cmd+V paste
    with _kb.pressed(Key.cmd):
        _kb.press("v")
        _kb.release("v")

    time.sleep(0.15)

    # Restore clipboard
    proc = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
    proc.communicate(original.encode("utf-8"))


def _inject_win(text: str):
    import pyperclip
    original = pyperclip.paste()
    pyperclip.copy(text)

    with _kb.pressed(Key.ctrl):
        _kb.press("v")
        _kb.release("v")

    time.sleep(0.15)
    pyperclip.copy(original)
