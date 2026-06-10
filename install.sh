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

# ── Install mode selection ───────────────────────────────────────────────────
echo "  How would you like to install Murmur?"
echo ""
echo "  1) App bundle (recommended)"
echo "     Builds Murmur.app and installs it to ~/Applications."
echo "     Shows as \"Murmur\" in Accessibility permissions."
echo "     Can be set to launch at login."
echo ""
echo "  2) Developer mode"
echo "     Installs as an editable Python package (pip install -e .)."
echo "     Run via the 'murmur' CLI command."
echo "     Best for contributors and development."
echo ""
read -rp "  Enter choice [default: 1]: " install_mode </dev/tty
echo ""

case "$install_mode" in
  2) INSTALL_MODE="dev" ;;
  *) INSTALL_MODE="app" ;;
esac

# ── Python check (must pass before anything else runs) ────────────────────────
PYTHON=""
for candidate in python3.13 python3.12 python3.11 python3.10 python3; do
  if command -v "$candidate" &>/dev/null; then
    if "$candidate" -c "import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)" 2>/dev/null; then
      PYTHON="$candidate"
      break
    fi
  fi
done

if [ -z "$PYTHON" ]; then
  FOUND_VER=$(python3 --version 2>&1 || echo "Python not found")
  echo "  ✗  Python 3.10 or newer is required."
  echo "     Found: $FOUND_VER"
  echo ""
  echo "  Install Python 3.13 and re-run this installer:"
  echo ""
  echo "     Option A — Homebrew (recommended):"
  echo "         brew install python@3.13"
  echo ""
  echo "     Option B — Download from python.org:"
  echo "         https://www.python.org/downloads/"
  echo ""
  exit 1
fi

echo "  ✓ Python $($PYTHON --version | awk '{print $2}')"
echo ""

# ── tkinter check (required for UI windows; separate package on Homebrew) ─────
if ! "$PYTHON" -c "import tkinter" 2>/dev/null; then
  PY_VER=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
  echo "  tkinter not found — installing python-tk@${PY_VER}…"
  if command -v brew &>/dev/null; then
    brew install "python-tk@${PY_VER}"
  else
    echo "  ✗  tkinter is required but not installed."
    echo "     Install it with:  brew install python-tk@${PY_VER}"
    exit 1
  fi
fi

# ── Install location ──────────────────────────────────────────────────────────
INSTALL_DIR="$HOME/Applications/Murmur"

if [ ! -f "$(dirname "$0")/pyproject.toml" ]; then
  echo "  Installing Murmur to: $INSTALL_DIR"
  echo ""
  if [ -d "$INSTALL_DIR/.git" ]; then
    echo "  Existing installation found — updating…"
    git -C "$INSTALL_DIR" pull --ff-only
  else
    mkdir -p "$HOME/Applications"
    git clone https://github.com/preethamag/murmur.git "$INSTALL_DIR"
  fi
  cd "$INSTALL_DIR"
else
  cd "$(dirname "$0")"
  INSTALL_DIR="$(pwd)"
  echo "  Installing from: $INSTALL_DIR"
  echo ""
fi

# ── Virtual environment ────────────────────────────────────────────────────────
VENV_DIR="$INSTALL_DIR/.venv"
VENV_NEEDS_CREATE=true
if [ -d "$VENV_DIR" ] && "$VENV_DIR/bin/python" -c "import setuptools, pip" 2>/dev/null; then
  VENV_NEEDS_CREATE=false
fi
if $VENV_NEEDS_CREATE; then
  echo "  Creating virtual environment…"
  rm -rf "$VENV_DIR"
  "$PYTHON" -m venv "$VENV_DIR"
  echo ""
fi
PYTHON="$VENV_DIR/bin/python"
PIP="$VENV_DIR/bin/pip"

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

read -rp "  Enter number [default: 4 (turbo)]: " choice </dev/tty
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
echo "  Upgrading pip…"
$PIP install --upgrade pip setuptools wheel -q

echo "  Installing dependencies…"
$PIP install -r requirements-mac.txt -q
$PIP install -e . -q

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
  read -rp "  Install Ollama now? [Y/n]: " install_ollama </dev/tty
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

ARCH=$($PYTHON -c "import platform; print(platform.machine())")

if [ "$ARCH" = "arm64" ]; then
  # Apple Silicon — use mlx-whisper
  if [ "$MODEL" = "turbo" ]; then
    MLX_ID="mlx-community/whisper-large-v3-turbo"
  else
    MLX_ID="mlx-community/whisper-${MODEL}-mlx"
  fi
  $PYTHON - <<PYEOF
import mlx_whisper, tempfile, wave, struct
# Download by running a silent transcription on a blank audio file
import numpy as np, os, struct, wave, tempfile
tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
with wave.open(tmp.name, "wb") as wf:
    wf.setnchannels(1); wf.setsampwidth(2); wf.setframerate(16000)
    wf.writeframes(struct.pack("<h", 0) * 16000)
try:
    mlx_whisper.transcribe(tmp.name, path_or_hf_repo="$MLX_ID")
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
  $PYTHON - <<PYEOF
from faster_whisper import WhisperModel
print("  Downloading via faster-whisper...")
WhisperModel("$FW_MODEL", compute_type="int8")
print("  Model ready.")
PYEOF
fi

# Determine which Whisper ID was actually downloaded
if [ "$ARCH" = "arm64" ]; then
  if [ "$MODEL" = "turbo" ]; then
    WHISPER_ID="mlx-community/whisper-large-v3-turbo"
  else
    WHISPER_ID="mlx-community/whisper-${MODEL}-mlx"
  fi
else
  if [ "$MODEL" = "turbo" ]; then
    WHISPER_ID="large-v3-turbo"
  else
    WHISPER_ID="$MODEL"
  fi
fi

# ══════════════════════════════════════════════════════════════════════════════
# App bundle install path
# ══════════════════════════════════════════════════════════════════════════════

if [ "$INSTALL_MODE" = "app" ]; then

  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  Building Murmur.app…"
  echo "  ─────────────────────────────────────────────────────"
  echo ""

  # Install PyInstaller if needed
  if ! $PYTHON -c "import PyInstaller" 2>/dev/null; then
    echo "  Installing PyInstaller…"
    $PIP install pyinstaller -q
  fi

  # Run build_app.sh which handles the PyInstaller build + codesign
  if bash "$INSTALL_DIR/build_app.sh"; then
    echo ""
    echo "  ✓ Murmur.app built successfully."
  else
    echo ""
    echo "  ✗  App bundle build failed."
    echo "     Falling back to developer mode (CLI)."
    echo "     You can try building manually later with: ./build_app.sh"
    echo ""
    INSTALL_MODE="dev"
  fi
fi

if [ "$INSTALL_MODE" = "app" ]; then
  # ── Copy .app to ~/Applications ──────────────────────────────────────────
  APP_SRC="$INSTALL_DIR/dist/Murmur.app"
  APP_DEST="$HOME/Applications/Murmur.app"

  echo ""
  echo "  Where would you like to install Murmur.app?"
  echo ""
  echo "  1) ~/Applications/Murmur.app  (recommended — no admin needed)"
  echo "  2) /Applications/Murmur.app   (system-wide, requires password)"
  echo ""
  read -rp "  Enter choice [default: 1]: " app_dest_choice </dev/tty
  echo ""

  case "$app_dest_choice" in
    2)
      APP_DEST="/Applications/Murmur.app"
      NEEDS_SUDO=true
      ;;
    *)
      APP_DEST="$HOME/Applications/Murmur.app"
      NEEDS_SUDO=false
      ;;
  esac

  # Create destination directory if needed
  DEST_DIR="$(dirname "$APP_DEST")"
  if [ ! -d "$DEST_DIR" ]; then
    if $NEEDS_SUDO; then
      sudo mkdir -p "$DEST_DIR"
    else
      mkdir -p "$DEST_DIR"
    fi
  fi

  # Remove old version if present
  if [ -d "$APP_DEST" ]; then
    echo "  Removing previous Murmur.app…"
    if $NEEDS_SUDO; then
      sudo rm -rf "$APP_DEST"
    else
      rm -rf "$APP_DEST"
    fi
  fi

  echo "  Installing Murmur.app to: $APP_DEST"
  if $NEEDS_SUDO; then
    sudo cp -R "$APP_SRC" "$APP_DEST"
  else
    cp -R "$APP_SRC" "$APP_DEST"
  fi
  echo "  ✓ Murmur.app installed."
  echo ""

  # ── Launch at login ──────────────────────────────────────────────────────
  echo "  Would you like Murmur to start automatically at login?"
  echo ""
  read -rp "  Start at login? [Y/n]: " launch_choice </dev/tty
  echo ""

  if [[ ! "$launch_choice" =~ ^[Nn]$ ]]; then
    PLIST_DIR="$HOME/Library/LaunchAgents"
    PLIST_FILE="$PLIST_DIR/com.murmur.app.plist"
    mkdir -p "$PLIST_DIR"

    cat > "$PLIST_FILE" <<PLIST
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.murmur.app</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/open</string>
        <string>$APP_DEST</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>
PLIST

    # Attempt to bootstrap for immediate availability
    launchctl bootstrap "gui/$(id -u)" "$PLIST_FILE" 2>/dev/null || true

    echo "  ✓ Murmur will start at login."
    echo "    LaunchAgent: $PLIST_FILE"
    echo ""
    echo "    To disable later, run:"
    echo "      launchctl bootout gui/$(id -u)/com.murmur.app"
    echo "      rm $PLIST_FILE"
    echo ""
  else
    echo "  Skipped. You can enable this later in Murmur's Settings."
    echo ""
  fi

  # ── Summary (app mode) ────────────────────────────────────────────────────
  echo ""
  echo "  ✓ Murmur installed to: $APP_DEST"
  echo "  ✓ Whisper model: $MODEL"
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  Launch Murmur:"
  echo ""
  echo "      open \"$APP_DEST\""
  echo ""
  echo "  Or find \"Murmur\" in Spotlight / Launchpad."
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  First launch — a setup screen will guide you through:"
  echo ""
  echo "    1. Grant Microphone access when macOS prompts"
  echo "    2. Grant Accessibility access:"
  echo "         System Settings > Privacy & Security > Accessibility"
  echo "         Click + and add \"Murmur\""
  echo ""
  echo "  The app appears as \"Murmur\" in the Accessibility list"
  echo "  (not as python3.X — that's the benefit of the .app bundle)."
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  Default hotkey: hold Right Option while speaking"
  echo "  Config file:    ~/.murmur/config.yaml"
  echo ""

else
  # ══════════════════════════════════════════════════════════════════════════
  # Developer mode (CLI) — original behavior
  # ══════════════════════════════════════════════════════════════════════════

  PYTHON_BIN=$(basename "$($PYTHON -c "import sys; print(sys.executable)")")

  echo ""
  echo "  ✓ Murmur installed to: $INSTALL_DIR"
  echo "  ✓ Whisper model: $MODEL"
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  Run Murmur:"
  echo ""
  echo "      murmur"
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  First launch — a setup screen will guide you through:"
  echo ""
  echo "    1. Grant Microphone access when macOS prompts"
  echo "    2. Grant Accessibility access:"
  echo "         System Settings > Privacy & Security > Accessibility"
  echo ""
  echo "  ⚠  IMPORTANT: In the Accessibility list, Murmur appears"
  echo "     as \"$PYTHON_BIN\" — not as Murmur. Add that entry."
  echo ""
  echo "  ─────────────────────────────────────────────────────"
  echo "  Default hotkey: hold Right Option while speaking"
  echo "  Config file:    ~/.murmur/config.yaml"
  echo ""

  # ── PATH check ──────────────────────────────────────────────────────────
  if ! command -v murmur &>/dev/null; then
    echo "  ⚠  The 'murmur' command is not on your PATH yet."
    echo ""
    echo "     Add this line to your ~/.zshrc (or ~/.bash_profile):"
    echo ""
    echo "         export PATH=\"$VENV_DIR/bin:\$PATH\""
    echo ""
    echo "     Then restart your terminal, or run:"
    echo "         source ~/.zshrc"
    echo ""
    echo "     Alternatively, run Murmur directly with:"
    echo "         $PYTHON -m murmur"
    echo ""
  fi
fi

# ── Standalone model usage instructions ───────────────────────────────────────
echo ""
echo "  ╔═════════════════════════════════════════════════════════════╗"
echo "  ║  Your models work outside Murmur too                       ║"
echo "  ║      Copy or save the instructions below.                  ║"
echo "  ╚═════════════════════════════════════════════════════════════╝"
echo ""
echo "  ── Whisper  (speech → text) ──────────────────────────────────"
echo ""
if [ "$ARCH" = "arm64" ]; then
echo "  Apple Silicon — mlx-whisper (fastest):"
echo ""
echo "      import mlx_whisper"
echo "      result = mlx_whisper.transcribe("
echo "          \"audio.wav\","
echo "          path_or_hf_repo=\"$WHISPER_ID\","
echo "      )"
echo "      print(result[\"text\"])"
echo ""
fi
echo "  Any Mac / Intel — faster-whisper:"
echo ""
echo "      from faster_whisper import WhisperModel"
echo "      model = WhisperModel(\"$WHISPER_ID\", compute_type=\"int8\")"
echo "      segments, _ = model.transcribe(\"audio.wav\")"
echo "      print(\" \".join(s.text for s in segments))"
echo ""
echo "  Models are cached in: ~/.cache/huggingface/"
echo "  They load in seconds after the first use."
echo ""

if $OLLAMA_INSTALLED; then
echo "  ── Ollama / qwen2.5:1.5b  (LLM) ─────────────────────────────"
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
echo "  Note: Ollama must be running — start it with:  ollama serve"
echo ""
fi

echo "  ─────────────────────────────────────────────────────────────"
echo ""
read -rp "  Press Enter once you have saved the above instructions… " </dev/tty
echo ""
