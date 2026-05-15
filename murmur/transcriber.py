import sys
import platform


def _is_apple_silicon():
    return sys.platform == "darwin" and platform.machine() == "arm64"


def transcribe(audio_path: str, model: str = "base", language: str = "en") -> str:
    lang = language if language != "auto" else None

    if _is_apple_silicon():
        try:
            return _transcribe_mlx(audio_path, model, lang)
        except ImportError:
            pass

    try:
        return _transcribe_faster(audio_path, model, lang)
    except ImportError:
        pass

    return _transcribe_openai(audio_path, model, lang)


# Maps friendly model names to their HuggingFace / faster-whisper IDs
_MLX_IDS = {
    "turbo": "mlx-community/whisper-large-v3-turbo-mlx",
}
_FASTER_IDS = {
    "turbo": "large-v3-turbo",
}

def _mlx_model_id(model):
    return _MLX_IDS.get(model, f"mlx-community/whisper-{model}-mlx")

def _faster_model_id(model):
    return _FASTER_IDS.get(model, model)


def _transcribe_mlx(audio_path, model, lang):
    import mlx_whisper
    model_id = _mlx_model_id(model)
    result = mlx_whisper.transcribe(
        audio_path,
        path_or_hq_model=model_id,
        language=lang,
    )
    return result["text"].strip()


def _transcribe_faster(audio_path, model, lang):
    from faster_whisper import WhisperModel
    wm = WhisperModel(_faster_model_id(model), compute_type="int8")
    segments, _ = wm.transcribe(audio_path, language=lang)
    return " ".join(s.text for s in segments).strip()


def _transcribe_openai(audio_path, model, lang):
    import whisper
    wm = whisper.load_model(model)
    kwargs = {"language": lang} if lang else {}
    result = wm.transcribe(audio_path, **kwargs)
    return result["text"].strip()
