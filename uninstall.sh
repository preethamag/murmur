#!/bin/bash
# Murmur — full uninstaller
# Finds every trace of Murmur on this machine and removes it.

set -euo pipefail

RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[1;33m'
CYN='\033[0;36m'
BLD='\033[1m'
RST='\033[0m'

echo ""
echo "  Murmur Uninstaller"
echo "  ──────────────────────────────────────────"
echo ""

confirm() {
    local msg="$1"
    local ans
    read -rp "  ${msg} [y/N]: " ans
    [[ "$ans" =~ ^[Yy]$ ]]
}

# Prompts: [r]emove / [k]eep (show usage instructions) / [s]kip
# Returns: "remove", "keep", or "skip"
ask_keep_or_remove() {
    local msg="$1"
    local ans
    while true; do
        read -rp "  ${msg}  [r=remove / k=keep + show usage / s=skip]: " ans
        case "$ans" in
            r|R) echo "remove"; return ;;
            k|K) echo "keep";   return ;;
            s|S|"") echo "skip"; return ;;
            *) echo "  Please type r, k, or s." ;;
        esac
    done
}

show_whisper_instructions() {
    local model_id="${1:-<your-model-id>}"
    echo ""
    echo -e "  ${CYN}── Whisper  (speech → text) — standalone usage ──────────────${RST}"
    echo ""
    echo "  Apple Silicon — mlx-whisper (fastest):"
    echo ""
    echo "      import mlx_whisper"
    echo "      result = mlx_whisper.transcribe("
    echo "          \"audio.wav\","
    echo "          path_or_hf_repo=\"$model_id\","
    echo "      )"
    echo "      print(result[\"text\"])"
    echo ""
    echo "  Any Mac / Intel — faster-whisper:"
    echo ""
    echo "      from faster_whisper import WhisperModel"
    echo "      model = WhisperModel(\"$model_id\", compute_type=\"int8\")"
    echo "      segments, _ = model.transcribe(\"audio.wav\")"
    echo "      print(\" \".join(s.text for s in segments))"
    echo ""
    echo "  Models are cached in: ~/.cache/huggingface/"
    echo ""
    read -rp "  Press Enter to continue… "
    echo ""
}

show_ollama_instructions() {
    echo ""
    echo -e "  ${CYN}── Ollama / qwen2.5:1.5b  (LLM) — standalone usage ─────────${RST}"
    echo ""
    echo "  Terminal:"
    echo "      ollama run qwen2.5:1.5b \"Your prompt here\""
    echo ""
    echo "  Python:"
    echo "      import urllib.request, json"
    echo "      payload = json.dumps({"
    echo "          \"model\": \"qwen2.5:1.5b\","
    echo "          \"prompt\": \"Your prompt here\","
    echo "          \"stream\": False,"
    echo "      }).encode()"
    echo "      req = urllib.request.Request("
    echo "          \"http://localhost:11434/api/generate\","
    echo "          data=payload,"
    echo "          headers={\"Content-Type\": \"application/json\"},"
    echo "      )"
    echo "      with urllib.request.urlopen(req) as r:"
    echo "          print(json.loads(r.read())[\"response\"])"
    echo ""
    echo "  curl:"
    echo "      curl http://localhost:11434/api/generate \\"
    echo "        -H \"Content-Type: application/json\" \\"
    echo "        -d '{\"model\":\"qwen2.5:1.5b\",\"prompt\":\"Hello\",\"stream\":false}'"
    echo ""
    echo "  Note: start Ollama first with:  ollama serve"
    echo ""
    read -rp "  Press Enter to continue… "
    echo ""
}

removed=0
skipped=0

remove_path() {
    local path="$1"
    local label="$2"
    if [ -e "$path" ] || [ -L "$path" ]; then
        echo -e "  ${YLW}Found${RST}  $label"
        echo "         $path"
        if confirm "Remove?"; then
            rm -rf "$path"
            echo -e "  ${GRN}✓ Removed${RST}"
            removed=$((removed + 1))
        else
            echo "  Skipped."
            skipped=$((skipped + 1))
        fi
        echo ""
    fi
}

# ── 1. Kill running Murmur process ────────────────────────────────────────────
echo -e "  ${BLD}Checking for running Murmur…${RST}"
PIDS=$(pgrep -f "murmur.main|python.*murmur" 2>/dev/null || true)
if [ -n "$PIDS" ]; then
    echo -e "  ${YLW}Found${RST}  Murmur is currently running (PID $PIDS)"
    if confirm "Quit it now?"; then
        kill $PIDS 2>/dev/null || true
        sleep 1
        echo -e "  ${GRN}✓ Stopped${RST}"
    fi
    echo ""
fi

# ── 2. LaunchAgent (login item) ───────────────────────────────────────────────
PLIST="$HOME/Library/LaunchAgents/com.murmur.app.plist"
if [ -f "$PLIST" ]; then
    echo -e "  ${YLW}Found${RST}  Login item (LaunchAgent)"
    echo "         $PLIST"
    if confirm "Remove login item?"; then
        launchctl bootout "gui/$(id -u)/com.murmur.app" 2>/dev/null || true
        rm -f "$PLIST"
        echo -e "  ${GRN}✓ Removed${RST}"
        removed=$((removed + 1))
    else
        skipped=$((skipped + 1))
    fi
    echo ""
fi

# ── 3. pip package ────────────────────────────────────────────────────────────
echo -e "  ${BLD}Checking pip installation…${RST}"
if pip3 show murmur &>/dev/null 2>&1; then
    PKG_LOC=$(pip3 show murmur 2>/dev/null | grep Location | awk '{print $2}')
    echo -e "  ${YLW}Found${RST}  pip package"
    echo "         $PKG_LOC"
    if confirm "Uninstall pip package?"; then
        pip3 uninstall murmur -y
        echo -e "  ${GRN}✓ Uninstalled${RST}"
        removed=$((removed + 1))
    else
        skipped=$((skipped + 1))
    fi
    echo ""
fi

# ── 4. murmur command in PATH ─────────────────────────────────────────────────
MURMUR_CMD=$(command -v murmur 2>/dev/null || true)
if [ -n "$MURMUR_CMD" ]; then
    echo -e "  ${YLW}Found${RST}  murmur command"
    echo "         $MURMUR_CMD"
    if confirm "Remove it?"; then
        rm -f "$MURMUR_CMD"
        echo -e "  ${GRN}✓ Removed${RST}"
        removed=$((removed + 1))
    else
        skipped=$((skipped + 1))
    fi
    echo ""
fi

# ── 5. App code directories ───────────────────────────────────────────────────
echo -e "  ${BLD}Searching for Murmur code directories…${RST}"

# Collect candidates: well-known locations + anywhere pip points + find in home
CANDIDATES=(
    "$HOME/Applications/Murmur"
    "$HOME/murmur"
    "$HOME/Desktop/murmur"
    "$HOME/Downloads/murmur"
    "$HOME/Documents/murmur"
    "$HOME/Projects/murmur"
    "$HOME/code/murmur"
    "$HOME/dev/murmur"
)

# Also check wherever the script itself lives (if run from the repo)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/pyproject.toml" ] && grep -q 'name = "murmur"' "$SCRIPT_DIR/pyproject.toml" 2>/dev/null; then
    CANDIDATES+=("$SCRIPT_DIR")
fi

# Search one level deep in common parent dirs for any murmur clone
for PARENT in "$HOME" "$HOME/Applications" "$HOME/Projects" "$HOME/code" "$HOME/dev"; do
    if [ -d "$PARENT" ]; then
        while IFS= read -r dir; do
            CANDIDATES+=("$dir")
        done < <(find "$PARENT" -maxdepth 1 -type d -iname "murmur" 2>/dev/null)
    fi
done

# Deduplicate and check each
declare -A SEEN
for DIR in "${CANDIDATES[@]}"; do
    # Resolve symlinks / normalise path
    REAL=$(python3 -c "import os; print(os.path.realpath('$DIR'))" 2>/dev/null || echo "$DIR")
    if [ -n "${SEEN[$REAL]:-}" ]; then continue; fi
    SEEN[$REAL]=1

    if [ -d "$REAL" ] && [ -f "$REAL/pyproject.toml" ] && grep -q 'name = "murmur"' "$REAL/pyproject.toml" 2>/dev/null; then
        echo ""
        remove_path "$REAL" "Murmur code directory"
    fi
done

# ── 6. Config & data ──────────────────────────────────────────────────────────
echo -e "  ${BLD}User data…${RST}"
echo ""
remove_path "$HOME/.murmur" "Config & vocabulary  (~/.murmur)"

# ── 7. Whisper model cache ────────────────────────────────────────────────────
HF_CACHE="$HOME/.cache/huggingface"
if [ -d "$HF_CACHE" ]; then
    WHISPER_DIRS=()
    while IFS= read -r d; do
        WHISPER_DIRS+=("$d")
    done < <(find "$HF_CACHE" -maxdepth 4 \( \
        -path "*/mlx-community/whisper*" \
        -o -path "*/openai/whisper*" \
        -o -path "*/models--Systran*" \
    \) -type d 2>/dev/null | sort -u)

    if [ ${#WHISPER_DIRS[@]} -gt 0 ]; then
        TOTAL=$(du -sh "$HF_CACHE" 2>/dev/null | awk '{print $1}' || echo "?")
        echo -e "  ${YLW}Found${RST}  Whisper model cache (~$TOTAL on disk)"
        echo "         $HF_CACHE"
        echo -e "  ${BLD}These models work in any Python app — not just Murmur.${RST}"
        echo ""

        WHISPER_CHOICE=$(ask_keep_or_remove "What would you like to do with the Whisper models?")
        case "$WHISPER_CHOICE" in
            remove)
                for d in "${WHISPER_DIRS[@]}"; do rm -rf "$d"; done
                rm -rf "$HOME/.cache/whisper" 2>/dev/null || true
                echo -e "  ${GRN}✓ Removed${RST}"
                removed=$((removed + 1))
                ;;
            keep)
                # Grab first found model id for the instructions
                SAMPLE_ID=$(basename "$(dirname "${WHISPER_DIRS[0]}")")/$(basename "${WHISPER_DIRS[0]}")
                show_whisper_instructions "$SAMPLE_ID"
                echo -e "  ${GRN}✓ Kept${RST} — models remain in ~/.cache/huggingface/"
                skipped=$((skipped + 1))
                ;;
            skip)
                skipped=$((skipped + 1))
                ;;
        esac
        echo ""
    fi
fi

# ── 8. Ollama model ───────────────────────────────────────────────────────────
if command -v ollama &>/dev/null; then
    if ollama list 2>/dev/null | grep -q "qwen2.5:1.5b"; then
        echo -e "  ${YLW}Found${RST}  Ollama model  qwen2.5:1.5b"
        echo -e "  ${BLD}This model works with any app via the Ollama REST API.${RST}"
        echo ""

        OLLAMA_CHOICE=$(ask_keep_or_remove "What would you like to do with qwen2.5:1.5b?")
        case "$OLLAMA_CHOICE" in
            remove)
                ollama rm qwen2.5:1.5b
                echo -e "  ${GRN}✓ Removed${RST}"
                removed=$((removed + 1))
                ;;
            keep)
                show_ollama_instructions
                echo -e "  ${GRN}✓ Kept${RST} — model remains available via Ollama"
                skipped=$((skipped + 1))
                ;;
            skip)
                skipped=$((skipped + 1))
                ;;
        esac
        echo ""
    fi
fi

# ── Summary ───────────────────────────────────────────────────────────────────
echo "  ──────────────────────────────────────────"
if [ $removed -eq 0 ] && [ $skipped -eq 0 ]; then
    echo -e "  Nothing to remove — Murmur was not found on this machine."
else
    echo -e "  ${GRN}Removed: $removed item(s)${RST}   Skipped: $skipped item(s)"
fi
echo ""
