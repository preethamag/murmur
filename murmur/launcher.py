"""
Cross-platform login-item management.
macOS  — writes/removes a LaunchAgent plist in ~/Library/LaunchAgents/
Windows — writes/removes a registry value under HKCU Run key

When running as a .app bundle (PyInstaller), the LaunchAgent uses `open`
to launch the app bundle. When running as a CLI script, it falls back to
`python -m murmur`.
"""
import os
import sys
import subprocess
import plistlib
from pathlib import Path

_PLIST = Path.home() / "Library" / "LaunchAgents" / "com.murmur.app.plist"
_REG_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_REG_NAME = "Murmur"


def _is_app_bundle() -> bool:
    """Return True if we are running inside a PyInstaller .app bundle."""
    return getattr(sys, "frozen", False)


def _get_app_path() -> str | None:
    """Return the path to the .app bundle if running inside one."""
    if not _is_app_bundle():
        return None
    # PyInstaller sets sys._MEIPASS to the temp extraction dir, but the actual
    # .app bundle path can be found by walking up from sys.executable.
    # sys.executable -> Murmur.app/Contents/MacOS/Murmur
    exe = Path(sys.executable).resolve()
    # Walk up to find .app
    for parent in [exe] + list(exe.parents):
        if parent.suffix == ".app":
            return str(parent)
    return None


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
        app_path = _get_app_path()
        if app_path:
            # Running as .app bundle — launch via `open`
            plist = {
                "Label": "com.murmur.app",
                "ProgramArguments": ["/usr/bin/open", app_path],
                "RunAtLoad": True,
                "KeepAlive": False,
            }
        else:
            # Check for an installed .app in known locations
            installed_app = _find_installed_app()
            if installed_app:
                plist = {
                    "Label": "com.murmur.app",
                    "ProgramArguments": ["/usr/bin/open", installed_app],
                    "RunAtLoad": True,
                    "KeepAlive": False,
                }
            else:
                # Running as CLI script — fall back to python -m murmur
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


def _find_installed_app() -> str | None:
    """Look for Murmur.app in standard macOS application directories."""
    candidates = [
        Path.home() / "Applications" / "Murmur.app",
        Path("/Applications") / "Murmur.app",
    ]
    for path in candidates:
        if path.is_dir():
            return str(path)
    return None


def _uid() -> int:
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
