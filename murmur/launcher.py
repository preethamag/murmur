"""
Cross-platform login-item management.
macOS  — writes/removes a LaunchAgent plist in ~/Library/LaunchAgents/
Windows — writes/removes a registry value under HKCU Run key
"""
import sys
import subprocess
import plistlib
from pathlib import Path

_PLIST = Path.home() / "Library" / "LaunchAgents" / "com.murmur.app.plist"
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_NAME = "Murmur"


def set_enabled(enabled: bool):
    if sys.platform == "darwin":
        _mac_set(enabled)
    elif sys.platform == "win32":
        _win_set(enabled)


def is_enabled() -> bool:
    if sys.platform == "darwin":
        return _PLIST.exists()
    if sys.platform == "win32":
        return _win_check()
    return False


# ── macOS ──────────────────────────────────────────────────────────────────────

def _mac_set(enabled: bool):
    if enabled:
        plist = {
            "Label": "com.murmur.app",
            "ProgramArguments": [sys.executable, "-m", "murmur"],
            "RunAtLoad": True,
            "KeepAlive": False,
        }
        _PLIST.parent.mkdir(parents=True, exist_ok=True)
        with open(_PLIST, "wb") as f:
            plistlib.dump(plist, f)
        # bootstrap so it's active for this login session, not just future ones
        try:
            subprocess.run(
                ["launchctl", "bootstrap", f"gui/{_uid()}", str(_PLIST)],
                check=False, capture_output=True, timeout=3,
            )
        except (OSError, subprocess.SubprocessError):
            pass
    else:
        try:
            subprocess.run(
                ["launchctl", "bootout", f"gui/{_uid()}/com.murmur.app"],
                check=False, capture_output=True, timeout=3,
            )
        except (OSError, subprocess.SubprocessError):
            pass
        _PLIST.unlink(missing_ok=True)


def _uid() -> int:
    import os
    return os.getuid()


# ── Windows ────────────────────────────────────────────────────────────────────

def _win_set(enabled: bool):
    import winreg
    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_SET_VALUE)
    try:
        if enabled:
            winreg.SetValueEx(key, _REG_NAME, 0, winreg.REG_SZ,
                              f'"{sys.executable}" -m murmur')
        else:
            try:
                winreg.DeleteValue(key, _REG_NAME)
            except FileNotFoundError:
                pass
    finally:
        winreg.CloseKey(key)


def _win_check() -> bool:
    import winreg
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REG_KEY, 0, winreg.KEY_READ)
        winreg.QueryValueEx(key, _REG_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
