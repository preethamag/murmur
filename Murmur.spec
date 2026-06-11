# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building Murmur.app

Usage:
    pyinstaller Murmur.spec

Or use the build_app.sh wrapper script.

This builds a macOS .app bundle that:
  - Shows as "Murmur" in the Accessibility permissions list
  - Lives in the menu bar (LSUIElement: true hides it from the Dock)
  - Bundles all Python dependencies including ML backends
  - Uses ~/.cache/huggingface/ for Whisper model storage
"""

import importlib
import os
import sys
from pathlib import Path

block_cipher = None

# ── Detect available optional packages ────────────────────────────────────────

def _is_importable(name):
    try:
        importlib.import_module(name)
        return True
    except ImportError:
        return False


# Hidden imports that PyInstaller can't discover via static analysis.
# These are all lazily imported at runtime.
hidden_imports = [
    # Core murmur modules
    "murmur",
    "murmur.main",
    "murmur.tray",
    "murmur.config",
    "murmur.recorder",
    "murmur.hotkey",
    "murmur.injector",
    "murmur.transcriber",
    "murmur.permissions",
    "murmur.cleaner",
    "murmur.vocabulary",
    "murmur.sounds",
    "murmur.punctuation",
    "murmur.launcher",
    "murmur.settings_window",
    "murmur.vocabulary_window",
    "murmur.fix_window",
    # Dependencies
    "rumps",
    "pynput",
    "pynput.keyboard",
    "pynput.keyboard._darwin",
    "pynput.mouse",
    "pynput.mouse._darwin",
    "sounddevice",
    "_sounddevice_data",
    "numpy",
    "yaml",
    "pyyaml",
    # tkinter for sub-windows
    "tkinter",
    "tkinter.ttk",
    # macOS-specific
    "ApplicationServices",
    # stdlib that might be needed
    "wave",
    "ctypes",
    "plistlib",
]

# Optional ML packages -- add only if installed
_optional = [
    ("mlx", ["mlx", "mlx.core", "mlx.nn"]),
    ("mlx_whisper", ["mlx_whisper"]),
    ("faster_whisper", ["faster_whisper"]),
    ("ctranslate2", ["ctranslate2"]),
    ("huggingface_hub", ["huggingface_hub"]),
    ("tokenizers", ["tokenizers"]),
]

for pkg, modules in _optional:
    if _is_importable(pkg):
        hidden_imports.extend(modules)
        print(f"  [+] Including {pkg}")
    else:
        print(f"  [-] Skipping {pkg} (not installed)")


# ── Collect data files ────────────────────────────────────────────────────────

# sounddevice needs its portaudio dylib
datas = []

# Collect _sounddevice_data (contains libportaudio)
try:
    import _sounddevice_data
    sd_data_dir = os.path.dirname(_sounddevice_data.__file__)
    datas.append((sd_data_dir, "_sounddevice_data"))
except ImportError:
    pass

# Collect sounddevice's _portaudio module
try:
    import sounddevice
    sd_dir = os.path.dirname(sounddevice.__file__)
    # Include the whole sounddevice package directory
    for f in os.listdir(sd_dir):
        fpath = os.path.join(sd_dir, f)
        if f.endswith(('.dylib', '.so')):
            datas.append((fpath, "sounddevice"))
except ImportError:
    pass


# ── Analysis ──────────────────────────────────────────────────────────────────

a = Analysis(
    ["murmur_app_entry.py"],
    pathex=["."],
    binaries=[],
    datas=datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "test",
        "unittest",
        "setuptools",
        "pip",
        "wheel",
        # Windows-only modules
        "pystray",
        "pyperclip",
        "PIL",
        "winreg",
        # Reduce bundle size
        "matplotlib",
        "scipy",
        "pandas",
        "pytest",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Murmur",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # No terminal window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file="Murmur.entitlements",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="Murmur",
)

app = BUNDLE(
    coll,
    name="Murmur.app",
    icon="assets/Murmur.icns",
    bundle_identifier="com.murmur.app",
    info_plist={
        "CFBundleName": "Murmur",
        "CFBundleDisplayName": "Murmur",
        "CFBundleIdentifier": "com.murmur.app",
        "CFBundleVersion": "0.1.0",
        "CFBundleShortVersionString": "0.1.0",
        # Hide from Dock -- menu-bar-only app (rumps)
        "LSUIElement": True,
        # Permission prompt descriptions
        "NSMicrophoneUsageDescription": (
            "Murmur needs microphone access to record your voice for dictation."
        ),
        # Minimum macOS version
        "LSMinimumSystemVersion": "11.0",
        "LSBackgroundOnly": False,
    },
)
