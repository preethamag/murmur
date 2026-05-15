# Murmur

Open-source voice dictation for macOS and Windows. Hold a hotkey, speak, release — text appears at your cursor in any app. Powered by local [Whisper](https://github.com/openai/whisper) models with no data ever leaving your device.

## Features

- **System-wide dictation** — works in any text field in any app
- **Push-to-talk** — hold hotkey to record, release to transcribe
- **Fully offline** — all transcription runs locally via Whisper
- **Apple Silicon optimized** — uses mlx-whisper for fast on-device inference
- **Menu bar / system tray** — minimal, always accessible
- **Configurable** — model size, language, hotkey

## Quick Install

**macOS**
```bash
git clone https://github.com/YOUR_USERNAME/murmur
cd murmur
bash install.sh
murmur
```

**Windows**
```bat
git clone https://github.com/YOUR_USERNAME/murmur
cd murmur
install.bat
murmur
```

## Download

Pre-built binaries are available on the [Releases](../../releases) page:

| Platform | Download |
|----------|----------|
| macOS (Apple Silicon + Intel) | `Murmur-mac.dmg` |
| Windows | `Murmur-win.zip` |

## Hotkeys

| Key | Action |
|-----|--------|
| Hold **Right Option (⌥)** | Start recording (macOS default) |
| Release | Transcribe + inject text at cursor |

Change via `~/.murmur/config.yaml` (macOS) or `%APPDATA%\Murmur\config.yaml` (Windows).

## Config

```yaml
hotkey: right_option   # right_option | f4 | f5 | right_ctrl
model: base            # tiny | base | small | medium | large-v3
language: en           # en | auto | es | fr | de ...
max_duration: 60       # seconds
```

Larger models are slower but more accurate. `base` is a good default.

## Permissions (macOS)

Two permissions required on first launch:
- **Microphone** — System Settings → Privacy & Security → Microphone
- **Accessibility** — System Settings → Privacy & Security → Accessibility

## Model sizes

| Model | Size | Speed | Accuracy |
|-------|------|-------|----------|
| tiny | 75 MB | fastest | good |
| base | 145 MB | fast | better |
| small | 466 MB | medium | great |
| medium | 1.5 GB | slow | excellent |
| large-v3 | 3 GB | slowest | best |

Models are downloaded automatically on first use.

## License

MIT
