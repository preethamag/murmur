"""
Earcon sounds for recording start/stop.
Generates tones as WAV in-memory, plays via afplay (macOS) or sounddevice
(other platforms) to avoid PortAudio conflicts with the recording stream.
"""
import io
import sys
import wave
import subprocess
import tempfile
import threading
import numpy as np

_SR = 44100
_lock = threading.Lock()


def _tone(freq: float, duration: float = 0.09, volume: float = 0.25) -> np.ndarray:
    t = np.linspace(0, duration, int(_SR * duration), endpoint=False)
    w = np.sin(2 * np.pi * freq * t)
    fade = max(1, int(_SR * 0.012))
    w[:fade] *= np.linspace(0, 1, fade)
    w[-fade:] *= np.linspace(1, 0, fade)
    return (w * volume).astype(np.float32)


def _gap(ms: float = 30) -> np.ndarray:
    return np.zeros(int(_SR * ms / 1000), dtype=np.float32)


def _to_wav_bytes(audio: np.ndarray) -> bytes:
    """Convert float32 audio array to WAV file bytes."""
    int16 = (audio * 32767).astype(np.int16)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SR)
        wf.writeframes(int16.tobytes())
    return buf.getvalue()


# Pre-generate tones at import time
_START_WAV = _to_wav_bytes(np.concatenate([_tone(523), _gap(25), _tone(659)]))
_STOP_WAV = _to_wav_bytes(np.concatenate([_tone(659), _gap(25), _tone(523)]))

# Write to persistent temp files so afplay can read them
_start_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
_start_file.write(_START_WAV)
_start_file.close()

_stop_file = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
_stop_file.write(_STOP_WAV)
_stop_file.close()


def _play_mac(path: str):
    """Play via afplay — uses CoreAudio directly, no PortAudio conflict."""
    try:
        subprocess.Popen(
            ["afplay", path],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except OSError:
        pass


def _play_other(path: str):
    """Fallback: play via sounddevice (Windows/Linux)."""
    import sounddevice as sd
    try:
        import soundfile as sf
        data, sr = sf.read(path)
        sd.play(data, sr)
        sd.wait()
    except Exception:
        pass


def _play(path: str):
    if sys.platform == "darwin":
        _play_mac(path)
    else:
        threading.Thread(target=_play_other, args=(path,), daemon=True).start()


def play_start():
    """Two ascending tones — C5 → E5."""
    _play(_start_file.name)


def play_stop():
    """Two descending tones — E5 → C5."""
    _play(_stop_file.name)
