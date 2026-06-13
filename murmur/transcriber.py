import sys
import platform

_MLX_IDS = {
    "turbo": "mlx-community/whisper-large-v3-turbo",
}
_FASTER_IDS = {
    "turbo": "large-v3-turbo",
}

# Known Whisper hallucinations — phantom phrases generated from silence/noise
_HALLUCINATIONS = {
    "thank you", "thanks for watching", "thanks for listening",
    "to do", "todo", "you", "bye", "goodbye", "the end",
    "subscribe", "like and subscribe", "see you next time",
    "so", "okay", "oh",
}

# Cached model instances — keyed by (backend, model_name)
_cache: dict = {}


def _is_apple_silicon():
    return sys.platform == "darwin" and platform.machine() == "arm64"

def _mlx_model_id(model):
    return _MLX_IDS.get(model, f"mlx-community/whisper-{model}-mlx")

def _faster_model_id(model):
    return _FASTER_IDS.get(model, model)


def _is_hallucination(text: str) -> bool:
    """Check if transcription is a known Whisper hallucination."""
    cleaned = text.strip().rstrip(".,!?").lower()
    return cleaned in _HALLUCINATIONS


def transcribe(audio_path: str, model: str = "base", language: str = "en") -> str:
    lang = language if language != "auto" else None

    if _is_apple_silicon():
        try:
            result = _transcribe_mlx(audio_path, model, lang)
            return "" if _is_hallucination(result) else result
        except ImportError:
            pass

    try:
        result = _transcribe_faster(audio_path, model, lang)
        return "" if _is_hallucination(result) else result
    except ImportError:
        pass

    result = _transcribe_openai(audio_path, model, lang)
    return "" if _is_hallucination(result) else result


def _evict(backend: str):
    """Drop any cached models from other model sizes for the same backend."""
    for k in list(_cache.keys()):
        if k[0] == backend:
            del _cache[k]


def _transcribe_mlx(audio_path, model, lang):
    import mlx_whisper
    # mlx_whisper.transcribe → load_model() is @lru_cache'd internally
    kwargs = {"language": lang} if lang else {}
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hf_repo=_mlx_model_id(model),
        **kwargs,
    )
    return result["text"].strip()


def _transcribe_faster(audio_path, model, lang):
    from faster_whisper import WhisperModel
    key = ("faster", model)
    if key not in _cache:
        _evict("faster")
        _cache[key] = WhisperModel(_faster_model_id(model), compute_type="int8")
    segments, _ = _cache[key].transcribe(audio_path, language=lang)
    return " ".join(s.text for s in segments).strip()


def _transcribe_openai(audio_path, model, lang):
    import whisper
    key = ("openai", model)
    if key not in _cache:
        _evict("openai")
        _cache[key] = whisper.load_model(model)
    kwargs = {"language": lang} if lang else {}
    result = _cache[key].transcribe(audio_path, **kwargs)
    return result["text"].strip()
