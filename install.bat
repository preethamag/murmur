@echo off
setlocal enabledelayedexpansion

echo.
echo   888b     d888 888     888 8888888b.  888b     d888 888     888 8888888b.
echo   8888b   d8888 888     888 888   Y88b 8888b   d8888 888     888 888   Y88b
echo   88888b.d88888 888     888 888    888 88888b.d88888 888     888 888    888
echo   888Y88888P888 888     888 888   d88P 888Y88888P888 888     888 888   d88P
echo   888 Y888P 888 888     888 8888888P"  888 Y888P 888 888     888 8888888P"
echo   888  Y8P  888 888     888 888 T88b   888  Y8P  888 888     888 888 T88b
echo   888   "   888 Y88b. .d88P 888  T88b  888   "   888 Y88b. .d88P 888  T88b
echo   888       888  "Y88888P"  888   T88b 888       888  "Y88888P"  888   T88b
echo.
echo   Open-source voice dictation -- powered by local Whisper
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python 3.10+ required. Install from https://python.org
    pause & exit /b 1
)

echo   Choose a Whisper model to download:
echo.
echo   +----+-------------+----------+--------------------------------------------+
echo   ^|  # ^| Model       ^| Size     ^| Notes                                      ^|
echo   +----+-------------+----------+--------------------------------------------+
echo   ^|  1 ^| tiny        ^|  75 MB   ^| Fastest. Basic accuracy. Quick tasks.      ^|
echo   ^|  2 ^| base        ^| 145 MB   ^| Fast with good accuracy. Great start.      ^|
echo   ^|  3 ^| small       ^| 466 MB   ^| Solid balance of speed and accuracy.       ^|
echo   ^|  4 ^| turbo       ^| 809 MB   ^| Near large-v3 accuracy, 8x faster. * Best ^|
echo   ^|  5 ^| medium      ^|  1.5 GB  ^| High accuracy. Slower on older hardware.   ^|
echo   ^|  6 ^| large-v3    ^|  3.0 GB  ^| Best accuracy. Great for modern hardware.  ^|
echo   +----+-------------+----------+--------------------------------------------+
echo.
echo   Tip: 'turbo' gives the best bang for the buck -- highly recommended.
echo   Models are stored in %%USERPROFILE%%\.cache\huggingface\ after download.
echo.

set /p CHOICE="  Enter number [default: 4 (turbo)]: "

if "%CHOICE%"=="1" set MODEL=tiny
if "%CHOICE%"=="2" set MODEL=base
if "%CHOICE%"=="3" set MODEL=small
if "%CHOICE%"=="4" set MODEL=turbo
if "%CHOICE%"==""  set MODEL=turbo
if "%CHOICE%"=="5" set MODEL=medium
if "%CHOICE%"=="6" set MODEL=large-v3
if not defined MODEL set MODEL=turbo

echo.
echo   Selected: %MODEL%
echo.

echo   Installing dependencies...
pip install -r requirements-win.txt -q
pip install -e . -q

:: Write config
set CFG=%APPDATA%\Murmur\config.yaml
if not exist "%APPDATA%\Murmur" mkdir "%APPDATA%\Murmur"
(
echo hotkey: right_ctrl
echo model: %MODEL%
echo language: en
echo sample_rate: 16000
echo inject_method: clipboard
echo sound_feedback: false
echo max_duration: 60
echo ai_cleanup: false
) > "%CFG%"

:: Download model
echo   Downloading %MODEL% model (this happens once)...
echo.

if "%MODEL%"=="turbo" (
    set FW_MODEL=large-v3-turbo
) else (
    set FW_MODEL=%MODEL%
)

python -c "from faster_whisper import WhisperModel; print('  Downloading...'); WhisperModel('%FW_MODEL%', compute_type='int8'); print('  Model ready.')"

echo.
echo   Murmur installed with model: %MODEL%
echo.
echo   Run:     murmur
echo.
echo   Default hotkey: hold Right Ctrl to record, release to transcribe.
echo   Config: %APPDATA%\Murmur\config.yaml
echo.
pause
