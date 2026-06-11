import sys

_MODIFIER_KEYS = {
    "right_option": (61, 0x80000),
    "left_option":  (58, 0x80000),
    "right_ctrl":   (62, 0x40000),
    "left_ctrl":    (59, 0x40000),
    "right_cmd":    (54, 0x100000),
}

_FUNCTION_KEYS = {
    "f4": 118,
    "f5": 96,
    "f6": 97,
}


class HotkeyListener:
    def __init__(self, key_name: str, on_press, on_release):
        self._key_name = key_name
        self._on_press = on_press
        self._on_release = on_release
        self._pressed = False
        self._cleanup = None

    def start(self):
        if sys.platform == "darwin":
            try:
                self._start_nsevent()
                return
            except Exception:
                pass
        self._start_pynput()

    def stop(self):
        if self._cleanup:
            self._cleanup()
            self._cleanup = None
        self._pressed = False

    def _start_nsevent(self):
        from AppKit import NSEvent

        monitors = []

        if self._key_name in _MODIFIER_KEYS:
            target_code, flag_mask = _MODIFIER_KEYS[self._key_name]

            def on_flags(event):
                if event.keyCode() == target_code:
                    is_down = bool(event.modifierFlags() & flag_mask)
                    if is_down and not self._pressed:
                        self._pressed = True
                        self._on_press()
                    elif not is_down and self._pressed:
                        self._pressed = False
                        self._on_release()

            m = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(1 << 12, on_flags)
            if m:
                monitors.append(m)

        elif self._key_name in _FUNCTION_KEYS:
            target_code = _FUNCTION_KEYS[self._key_name]

            def on_key(event):
                if event.keyCode() == target_code:
                    etype = event.type()
                    if etype == 10 and not self._pressed:
                        self._pressed = True
                        self._on_press()
                    elif etype == 11 and self._pressed:
                        self._pressed = False
                        self._on_release()

            m = NSEvent.addGlobalMonitorForEventsMatchingMask_handler_(
                (1 << 10) | (1 << 11), on_key
            )
            if m:
                monitors.append(m)

        def cleanup():
            for m in monitors:
                NSEvent.removeMonitor_(m)
            monitors.clear()

        self._cleanup = cleanup

    def _start_pynput(self):
        from pynput import keyboard

        KEY_MAP = {
            "right_option": keyboard.Key.alt_r,
            "left_option": keyboard.Key.alt,
            "right_ctrl": keyboard.Key.ctrl_r,
            "left_ctrl": keyboard.Key.ctrl_l,
            "right_cmd": keyboard.Key.cmd_r,
            "f4": keyboard.Key.f4,
            "f5": keyboard.Key.f5,
            "f6": keyboard.Key.f6,
        }

        target = KEY_MAP.get(self._key_name, keyboard.Key.alt_r)

        def _press(key):
            if key == target and not self._pressed:
                self._pressed = True
                self._on_press()

        def _release(key):
            if key == target and self._pressed:
                self._pressed = False
                self._on_release()

        listener = keyboard.Listener(on_press=_press, on_release=_release)
        listener.daemon = True
        listener.start()

        self._cleanup = listener.stop
