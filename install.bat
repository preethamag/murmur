@echo off
echo Installing Murmur (Windows)...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.10+ required. Install from https://python.org
    exit /b 1
)

pip install -r requirements-win.txt -q
pip install -e . -q

echo.
echo  Murmur installed!
echo.
echo Run:  murmur
echo.
echo Default hotkey: hold Right Ctrl to record, release to transcribe.
pause
