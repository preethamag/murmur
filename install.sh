#!/bin/bash
set -e

echo ""
echo "  ███╗   ███╗██╗   ██╗██████╗ ███╗   ███╗██╗   ██╗██████╗ "
echo "  ████╗ ████║██║   ██║██╔══██╗████╗ ████║██║   ██║██╔══██╗"
echo "  ██╔████╔██║██║   ██║██████╔╝██╔████╔██║██║   ██║██████╔╝"
echo "  ██║╚██╔╝██║██║   ██║██╔══██╗██║╚██╔╝██║██║   ██║██╔══██╗"
echo "  ██║ ╚═╝ ██║╚██████╔╝██║  ██║██║ ╚═╝ ██║╚██████╔╝██║  ██║"
echo "  ╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝  ╚═╝"
echo ""
echo "  Open-source voice dictation — powered by local Whisper"
echo ""

# ── Python check ──────────────────────────────────────────────────────────────
if ! command -v python3 &>/dev/null; then
  echo "Error: Python 3.10+ required. Install from https://python.org"
  exit 1
fi

# ── Model selection ───────────────────────────────────────────────────────────
echo "  Choose a Whisper model to download:"
echo ""
echo "  ┌────┬─────────────┬──────────┬────────────────────────────────────────────┐"
echo "  │ #  │ Model       │ Size     │ Notes                                      │"
echo "  ├────┼─────────────┼──────────┼────────────────────────────────────────────┤"
echo "  │ 1  │ tiny        │  75 MB   │ Fastest. Basic accuracy. Quick tasks.      │"
echo "  │ 2  │ base        │ 145 MB   │ Fast with good accuracy. Great start.      │"
echo "  │ 3  │ small       │ 466 MB   │ Solid balance of speed and accuracy.       │"
echo "  │ 4  │ turbo       │ 809 MB   │ Near large-v3 accuracy, 8x faster. ★ Best │"
echo "  │ 5  │ medium      │ 1.5 GB   │ High accuracy. Slower on older hardware.   │"
echo "  │ 6  │ large-v3    │ 3.0 GB   │ Best accuracy. Ideal for Apple Silicon.    │"
echo "  └────┴─────────────┴──────────┴────────────────────────────────────────────┘"
echo ""
echo "  Tip: 'turbo' gives the best bang for the buck — highly recommended."
echo "  Models are stored in ~/.cache/huggingface/ after download."
echo ""

read -rp "  Enter number [default: 4 (turbo)]: " choice
echo ""

case "$choice" in
  1) MODEL="tiny"     ;;
  2) MODEL="base"     ;;
  3) MODEL="small"    ;;
  4|"") MODEL="turbo" ;;
  5) MODEL="medium"   ;;
  6) MODEL="large-v3" ;;
  *) echo "Invalid choice, defaulting to turbo."; MODEL="turbo" ;;
esac

echo "  → Selected: $MODEL"
echo ""

# ── Install dependencies ───────────────────────────────────────────────────────
echo "  Installing dependencies..."
pip3 install -r requirements-mac.txt -q
pip3 install -e . -q

# ── Ollama (AI Cleanup + Vocabulary) ──────────────────────────────────────────
echo "  Checking for Ollama (used for AI cleanup and vocabulary corrections)..."
echo ""

OLLAMA_INSTALLED=false
if command -v ollama &>/dev/null; then
  OLLAMA_INSTALLED=true
  echo "  ✓ Ollama already installed."
else
  echo "  Ollama is not installed."
  echo "  AI Cleanup (#1) and Context Vocabulary (#3) require Ollama + qwen2.5:1.5b (~1 GB)."
  echo ""
  read -rp "  Install Ollama now? [Y/n]: " install_ollama
  if [[ "$install_ollama" =~ ^[Nn]$ ]]; then
    echo "  Skipping Ollama. You can install it later from https://ollama.com"
    echo "  and run: ollama pull qwen2.5:1.5b"
  else
    if command -v brew &>/dev/null; then
      echo "  Installing Ollama via Homebrew..."
      brew install --cask ollama
    else
      echo "  Homebrew not found. Downloading Ollama installer..."
      curl -fsSL https://ollama.com/install.sh | sh
    fi
    OLLAMA_INSTALLED=true
  fi
fi

if $OLLAMA_INSTALLED; then
  echo ""
  echo "  Pulling qwen2.5:1.5b (~1 GB, happens once)..."
  # Start Ollama serve in background if not already running
  if ! curl -sf http://localhost:11434/api/tags &>/dev/null; then
    ollama serve &>/dev/null &
    sleep 3
  fi
  ollama pull qwen2.5:1.5b
  echo "  ✓ qwen2.5:1.5b ready."
fi

echo ""

# ── Write config ───────────────────────────────────────────────────────────────
mkdir -p ~/.murmur
cat > ~/.murmur/config.yaml <<EOF
hotkey: right_option
model: $MODEL
language: en
sample_rate: 16000
inject_method: clipboard
sound_feedback: false
max_duration: 60
ai_cleanup: false
ollama_model: qwen2.5:1.5b
ollama_url: http://localhost:11434
EOF

# ── Download model ─────────────────────────────────────────────────────────────
echo "  Downloading $MODEL model (this happens once)..."
echo ""

ARCH=$(python3 -c "import platform; print(platform.machine())")

if [ "$ARCH" = "arm64" ]; then
  # Apple Silicon — use mlx-whisper
  if [ "$MODEL" = "turbo" ]; then
    MLX_ID="mlx-community/whisper-large-v3-turbo-mlx"
  else
    MLX_ID="mlx-community/whisper-${MODEL}-mlx"
  fi
  python3 - <<PYEOF
import mlx_whisper, tempfile, wave, struct
# Download by running a silent transcription on a blank audio file
import numpy as np, os, struct, wave, tempfile
tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
with wave.open(tmp.name, "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
    wf.writeframes(struct.pack("<h", 0) * 16000)
try:
    mlx_whisper.transcribe(tmp.name, path_or_hq_model="$MLX_ID")
except Exception:
    pass
finally:
    os.unlink(tmp.name)
print("  Model ready.")
PYEOF
else
  # Intel Mac — use faster-whisper
  if [ "$MODEL" = "turbo" ]; then
    FW_MODEL="large-v3-turbo"
  else
    FW_MODEL="$MODEL"
  fi
  python3 - <<PYEOF
from faster_whisper import WhisperModel
print("  Downloading via faster-whisper...")
WhisperModel("$FW_MODEL", compute_type="int8")
print("  Model ready.")
PYEOF
fi

echo ""
echo "  ✓ Murmur installed with model: $MODEL"
echo ""
echo "  Run:     murmur"
echo ""
echo "  First launch — grant these permissions when prompted:"
echo "    • Microphone  →  System Settings › Privacy › Microphone"
echo "    • Accessibility  →  System Settings › Privacy › Accessibility"
echo ""
echo "  Default hotkey: hold Right Option (⌥) to record, release to transcribe."
echo "  Config: ~/.murmur/config.yaml"
echo ""
