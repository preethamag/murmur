# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

a = Analysis(
    ['../murmur/main.py'],
    pathex=['..'],
    binaries=[],
    datas=collect_data_files('faster_whisper'),
    hiddenimports=[
        'murmur.config',
        'murmur.recorder',
        'murmur.transcriber',
        'murmur.injector',
        'murmur.hotkey',
        'murmur.tray',
        'pystray',
        'pynput',
        'sounddevice',
        'faster_whisper',
        'numpy',
        'PIL',
        'pyperclip',
        'wave',
        'yaml',
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=['mlx_whisper', 'rumps'],
    cipher=block_cipher,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='Murmur',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,          # no terminal window
    onefile=True,
    icon=None,
)
