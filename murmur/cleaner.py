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
        out = json.loads(resp.read()).get("response", "").strip()
    # Strip wrapping quotes/code-fence the model sometimes adds.
    if len(out) >= 2 and out[0] == out[-1] and out[0] in ('"', "'", "`"):
        out = out[1:-1].strip()
    return out


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

    # Step 1: definite replacements (case-insensitive, whole-word).
    # Sort by length descending so longer phrases match before their substrings
    # (e.g. "new york city" before "new york").
    replacements = vocab.get("replacements", {})
    for wrong, right in sorted(replacements.items(), key=lambda kv: -len(kv[0])):
        result = re.sub(
            rf"\b{re.escape(wrong)}\b", right, result, flags=re.IGNORECASE
        )

    if not cfg.get("ai_cleanup", False):
        return result

    # Step 2: filler/grammar cleanup. Keep the previous value if the model
    # returns empty / fails — never replace good text with nothing.
    try:
        cleaned = _call_ollama(url, model, _CLEANUP_PROMPT.format(text=result))
        if cleaned:
            result = cleaned
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
                corrected = _call_ollama(url, model, _VOCAB_PROMPT.format(
                    text=result, vocab=vocab_str
                ))
                if corrected:
                    result = corrected
            except Exception:
                pass

    return result
