# -*- mode: python ; coding: utf-8 -*-
import sys
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['../murmur/main.py'],
    pathex=['..'],
    binaries=[],
    datas=collect_data_files('mlx_whisper') + collect_data_files('faster_whisper'),
    hiddenimports=[
        'murmur.config',
        'murmur.recorder',
        'murmur.transcriber',
        'murmur.injector',
        'murmur.hotkey',
        'murmur.tray',
        'rumps',
        'pynput',
        'sounddevice',
        'mlx_whisper',
        'faster_whisper',
        'numpy',
        'wave',
        'yaml',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Murmur',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    name='Murmur',
)

app = BUNDLE(
    coll,
    name='Murmur.app',
    bundle_identifier='com.murmur.app',
    info_plist={
        'LSUIElement': True,          # hide from dock (menu bar app)
        'NSMicrophoneUsageDescription': 'Murmur needs microphone access to transcribe your speech.',
        'NSAccessibilityUsageDescription': 'Murmur needs accessibility access to type text into other apps.',
        'CFBundleShortVersionString': '0.1.0',
    },
)
