import wave
import tempfile
import threading
import numpy as np
import sounddevice as sd


def list_input_devices() -> list[dict]:
    """Returns input devices as [{"name": str, "index": int}, ...]."""
    import sounddevice as sd
    devices = []
    for i, d in enumerate(sd.query_devices()):
        if d["max_input_channels"] > 0:
            devices.append({"name": d["name"], "index": i})
    return devices


class Recorder:
    def __init__(self, sample_rate=16000, device=None, max_duration=60):
        self.sample_rate = sample_rate
        self.device = device   # None = system default; str = device name
        self.max_duration = max_duration
        self._frames = []
        self._frame_count = 0
        self._max_frames = int(sample_rate * max_duration)
        self._recording = False
        self._lock = threading.Lock()
        self._stream = None

    def start(self):
        with self._lock:
            self._frames = []
            self._frame_count = 0
            self._recording = True

        def callback(indata, frame_count, time_info, status):
            with self._lock:
                if not self._recording:
                    return
                # Hard cap on memory: drop frames past max_duration
                if self._frame_count >= self._max_frames:
                    self._recording = False
                    return
                self._frames.append(indata.copy())
                self._frame_count += frame_count

        # Resolve device name → index if specified
        device_idx = None
        if self.device:
            for d in list_input_devices():
                if d["name"] == self.device:
                    device_idx = d["index"]
                    break

        self._stream = sd.InputStream(
            samplerate=self.sample_rate,
            channels=1,
            dtype="int16",
            device=device_idx,
            callback=callback,
        )
        self._stream.start()

    def current_energy(self) -> float:
        """RMS energy of the most recent audio chunk. Used for silence detection."""
        with self._lock:
            if not self._frames:
                return 0.0
            chunk = self._frames[-1].astype(np.float32)
            return float(np.sqrt(np.mean(chunk ** 2)))

    def stop(self):
        with self._lock:
            self._recording = False

        if self._stream:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

        with self._lock:
            frames = list(self._frames)

        if not frames:
            return None

        audio = np.concatenate(frames, axis=0)

        # Skip if no chunk ever exceeded the speech threshold — prevents
        # Whisper hallucinations on silence/ambient noise.  We check the
        # *peak* RMS across 0.25 s chunks rather than the whole-file average
        # so that a long initial pause doesn't drown out real speech.
        chunk_size = max(1, self.sample_rate // 4)  # 0.25 s chunks
        peak_rms = 0.0
        for i in range(0, len(audio), chunk_size):
            chunk = audio[i:i + chunk_size].astype(np.float32)
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms > peak_rms:
                peak_rms = rms
        if peak_rms < 300:
            return None

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        with wave.open(tmp.name, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(self.sample_rate)
            wf.writeframes(audio.tobytes())
        return tmp.name
