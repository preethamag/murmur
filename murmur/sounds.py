"""
Earcon sounds for recording start/stop.
Generates tones in-process using numpy + sounddevice — no audio files needed.
Plays on a daemon thread so it never blocks the hotkey path.
"""
import threading
import numpy as np
import sounddevice as sd

_SR = 44100


def _tone(freq: float, duration: float = 0.09, volume: float = 0.25) -> np.ndarray:
    t = np.linspace(0, duration, int(_SR * duration), endpoint=False)
    wave = np.sin(2 * np.pi * freq * t)
    fade = max(1, int(_SR * 0.012))
    wave[:fade] *= np.linspace(0, 1, fade)
    wave[-fade:] *= np.linspace(1, 0, fade)
    return (wave * volume).astype(np.float32)


def _gap(ms: float = 30) -> np.ndarray:
    return np.zeros(int(_SR * ms / 1000), dtype=np.float32)


def _play(wave: np.ndarray):
    try:
        sd.play(wave, _SR)
        sd.wait()
    except Exception:
        pass


def play_start():
    """Two ascending tones — C5 → E5."""
    audio = np.concatenate([_tone(523), _gap(25), _tone(659)])
    threading.Thread(target=_play, args=(audio,), daemon=True).start()


def play_stop():
    """Two descending tones — E5 → C5."""
    audio = np.concatenate([_tone(659), _gap(25), _tone(523)])
    threading.Thread(target=_play, args=(audio,), daemon=True).start()
