#!/bin/bash
set -e

echo "Installing Murmur (macOS)..."

# Check Python
if ! command -v python3 &>/dev/null; then
  echo "Error: Python 3.10+ required. Install from https://python.org"
  exit 1
fi

PYTHON=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "Python $PYTHON detected"

pip3 install -r requirements-mac.txt -q
pip3 install -e . -q

echo ""
echo "✓ Murmur installed!"
echo ""
echo "Run:  murmur"
echo ""
echo "First launch:"
echo "  • Grant Microphone access in System Settings → Privacy"
echo "  • Grant Accessibility access in System Settings → Privacy"
echo ""
echo "Default hotkey: hold Right Option (⌥) to record, release to transcribe."
