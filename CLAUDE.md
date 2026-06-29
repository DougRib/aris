# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is ARIS

ARIS is a Portuguese-language voice assistant desktop app for Windows. It uses a Tkinter GUI, speech recognition (Google Speech API via `SpeechRecognition`), and two TTS backends: `edge-tts` (online, preferred) and `pyttsx3` (offline fallback). Responses are always in Brazilian Portuguese and addressed to "senhor".

## Running the App

```bash
# Activate venv first (Windows)
venv\Scripts\activate

# Run
python aris.py
```

There are no automated tests and no build step.

## Environment Variables

Copy `.env` (not committed) to the repo root. All settings live in [app/config.py](app/config.py):

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_KEY` | Yes | Google Gemini 2.0 Flash (AI fallback for all unrecognised commands) |
| `OPENWEATHER_KEY` | Yes | Current weather and forecast |
| `CIDADE_PADRAO` | No | Default city for startup weather greeting (default: São Paulo) |
| `TTS_ENGINE` | No | `edge` (default) or `pyttsx3` |
| `EDGE_TTS_VOICE` | No | e.g. `pt-BR-AntonioNeural` |
| `WORD_PATH` | No | Absolute path to `WINWORD.EXE` if auto-detection fails |
| `YOUTUBE_VOLUME_APPS` | No | Comma-separated browser process names for per-app volume |
| `PLAYLIST_MUSICA/ESTUDO/TREINO` | No | YouTube URLs for the three built-in playlists |

## Architecture

```
aris.py              ← entry point, calls app.main.main()
app/
  config.py          ← all env-var loading; Config.validar() called at startup
  logging_setup.py   ← loguru: INFO to stderr, DEBUG to data/logs/aris_<date>.log
  main.py            ← wires Config → Gemini → Tkinter root → ArisApp

  ui/app.py          ← ArisApp (Tkinter); owns the main thread; spawns one daemon
                        thread for the voice loop (executar_assistente)
  core/
    command_processor.py  ← CommandProcessor; pure keyword matching (no regex);
                             falls back to GeminiService for unrecognised input
  managers/
    memory.py        ← MemoryManager; circular deque (max 20 items); persists to
                        data/memoria.json; thread-safe; disabled in private mode
    notes.py         ← NotesManager; appends timestamped lines to data/notas_aris.txt
  services/
    gemini.py        ← GeminiService; single chat session per app launch;
                        model: gemini-2.0-flash-exp; max ~40 words per reply
    weather.py       ← WeatherService; OpenWeather v2.5 (Kelvin → Celsius)
    music.py         ← MusicService; opens YouTube playlist URLs in default browser
    volume.py        ← VolumeService; Windows-only; tries pycaw Core Audio first,
                        falls back to winmm waveOut; per-app YouTube volume via pycaw
    tts.py           ← EdgeTTS; async edge-tts → MP3 → MCI (Windows) or playsound
  utils/
    dates.py         ← format_date_pt_br(); Portuguese month names
```

### Key design decisions

- **Single daemon thread**: the entire voice loop (TTS + STT + command processing) runs in one background thread; all UI updates go through `root.after()` or direct widget calls (Tkinter is not thread-safe but the app avoids concurrent widget writes).
- **Command matching is positional/substring**: `CommandProcessor.processar()` uses `in` checks on lowercased, unicode-normalised text; order of checks matters — more specific patterns come first.
- **TTS fallback chain**: EdgeTTS (requires internet) → pyttsx3 (offline). If `edge_tts.is_ready()` returns False at startup, the app switches to pyttsx3 for the session.
- **Wake word modes**: `always_active=True` (default) processes every utterance as a command. When False, the wake word "Aris"/"Aries" must precede commands.
- **Private mode**: set via voice command; suppresses both `MemoryManager` and `NotesManager` writes for the session.

## Data Files

Runtime data is written to `data/` (auto-created):
- `data/memoria.json` — conversation history (JSON, up to 20 entries)
- `data/notas_aris.txt` — append-only notes log
- `data/logs/aris_YYYY-MM-DD.log` — 7-day rolling debug log
- `data/tts/` — temporary MP3 files (deleted after playback)
