from pynput import keyboard

_KEY_MAP = {
    "right_option": keyboard.Key.alt_r,
    "left_option": keyboard.Key.alt,
    "right_ctrl": keyboard.Key.ctrl_r,
    "left_ctrl": keyboard.Key.ctrl_l,
    "right_cmd": keyboard.Key.cmd_r,
    "f4": keyboard.Key.f4,
    "f5": keyboard.Key.f5,
    "f6": keyboard.Key.f6,
}


class HotkeyListener:
    def __init__(self, key_name: str, on_press, on_release):
        self._target = _KEY_MAP.get(key_name, keyboard.Key.alt_r)
        self._on_press = on_press
        self._on_release = on_release
        self._pressed = False
        self._listener = None

    def start(self):
        def _press(key):
            if key == self._target and not self._pressed:
                self._pressed = True
                self._on_press()

        def _release(key):
            if key == self._target and self._pressed:
                self._pressed = False
                self._on_release()

        self._listener = keyboard.Listener(on_press=_press, on_release=_release)
        self._listener.daemon = True
        self._listener.start()

    def stop(self):
        if self._listener:
            self._listener.stop()
