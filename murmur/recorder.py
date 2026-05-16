import wave
import tempfile
import threading
import numpy as np
import sounddevice as sd


class Recorder:
    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate
        self._frames = []
        self._recording = False
        self._lock = threading.Lock()
        self._stream = None

    def start(self, on_level=None):
        with self._lock:
            self._frames = []
            self._recording = True

        def callback(indata, frame_count, time_info, status):
            with self._lock:
                if self._recording:
                    self._frames.append(indata.copy())
            if on_level:
                rms = np.sqrt(np.mean(indata.astype(np.float32) ** 2)) / 32768.0
                on_level(min(1.0, rms * 12))   # scale so normal speech hits 0.5–0.9

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            callback=callback,
        )
        self._stream.start()

    def stop(self):
        with self._lock:
            self._recording = False

        if self._stream:
            self._stream.stop()
            self._stream.close()
            self._stream = None

        with self._lock:
            frames = list(self._frames)

        if not frames:
            return None

        audio = np.concatenate(frames, axis=0)
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        return tmp.name
