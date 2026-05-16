"""
Applies AI cleanup and vocabulary corrections to transcribed text.
Requires Ollama running locally with qwen2.5:1.5b pulled.
Falls back silently (returns original text) if Ollama is unavailable.
"""
import re
import json
import urllib.request
import urllib.error

_CLEANUP_PROMPT = (
    "You are a text cleanup assistant. The user dictated the following text using "
    "speech recognition. Clean it up: remove filler words (um, uh, like, you know, "
    "sort of, basically), fix grammar and capitalization, and make it sound natural "
    "as written text. Output ONLY the cleaned text, no explanation, no quotes.\n\n"
    "Raw text: {text}"
)

_VOCAB_PROMPT = (
    "You are a text correction assistant. The user has a custom vocabulary list of "
    "ambiguous words with multiple possible forms. Based on context, correct any words "
    "that should use a different form from the list. Only change a word if you are "
    "confident the context calls for it. Output ONLY the corrected text, no explanation.\n\n"
    "Text: {text}\n"
    "Vocabulary groups (pick the right form per group based on context): {vocab}"
)


def _call_ollama(url, model, prompt):
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request(
        f"{url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())["response"].strip()


def clean(text, cfg, vocabulary=None):
    """
    Returns cleaned/corrected text.
    Steps (each is a no-op if disabled or unavailable):
      1. Definite replacements — applied without LLM
      2. AI filler/grammar cleanup — requires ai_cleanup=True + Ollama
      3. Context-aware vocab — requires context_words + ai_cleanup=True + Ollama
    """
    if not text:
        return text

    result = text
    url = cfg.get("ollama_url", "http://localhost:11434")
    model = cfg.get("ollama_model", "qwen2.5:1.5b")
    vocab = vocabulary or {}

    # Step 1: definite replacements (case-insensitive, whole-word)
    for wrong, right in vocab.get("replacements", {}).items():
        result = re.sub(
            rf"\b{re.escape(wrong)}\b", right, result, flags=re.IGNORECASE
        )

    if not cfg.get("ai_cleanup", False):
        return result

    # Step 2: filler/grammar cleanup
    try:
        result = _call_ollama(url, model, _CLEANUP_PROMPT.format(text=result))
    except Exception:
        pass

    # Step 3: context-aware vocabulary corrections
    context_words = vocab.get("context_words", [])
    if context_words:
        vocab_str = "; ".join(
            "/".join(entry["forms"]) for entry in context_words if entry.get("forms")
        )
        if vocab_str:
            try:
                result = _call_ollama(url, model, _VOCAB_PROMPT.format(
                    text=result, vocab=vocab_str
                ))
            except Exception:
                pass

    return result
