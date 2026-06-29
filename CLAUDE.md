# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is ARIS

ARIS is a Brazilian-Portuguese voice assistant ("JARVIS"-style). It is being rebuilt from a
Tkinter monolith into a **headless Python backend** (FastAPI + WebSocket) plus a future
**React frontend** (the futuristic HUD). The brain — skills, LLM, memory, voice — runs headless;
any client connects over a single WebSocket. Responses are always in PT-BR, addressed to "senhor".

The legacy Tkinter app (`app/`, `aris.py`) was fully ported into `backend/` and removed; its
HUD design tokens live in [docs/design/hud-tokens.md](docs/design/hud-tokens.md).

Roadmap (see [docs/superpowers/specs/](docs/superpowers/specs/)): Fase 0 núcleo ✓ · Plano 2 skills+voz ✓ ·
**Plano 3 frontend React** (next) · then intelligence / environment / vision phases.

## Running

Backend (requires `uv` — the only dependency manager; single source of truth is
`backend/pyproject.toml` + `backend/uv.lock`, no `requirements.txt`):

```bash
cd backend
uv sync                                                      # install/update backend/.venv from the lockfile
uv run uvicorn aris.api.gateway:app --port 8000              # WebSocket at ws://127.0.0.1:8000/ws
uv run pytest -q                                             # tests
uv run ruff check . && uv run black --check . && uv run mypy aris   # lint + types
uv add <pkg>                                                 # add a dependency (commit pyproject + uv.lock)
```

> `uv` is installed at `%APPDATA%\Python\Python313\Scripts\uv.exe` and may not be on PATH yet.

## Environment Variables

A single `.env` lives at the **repo root** (git-ignored, holds secrets). `config.py` reads it via
`ROOT_DIR / ".env"`; settings are typed with pydantic-settings in
[backend/aris/config.py](backend/aris/config.py).

| Variable | Required | Purpose |
|---|---|---|
| `GEMINI_KEY` | for Gemini | Google AI Studio API key (LLM fallback for unmatched commands) |
| `OPENWEATHER_KEY` | for weather | Current weather + forecast |
| `ARIS_LLM_PROVIDER` | No | `gemini` (default) or `ollama` (local, free) |
| `GEMINI_MODEL` | No | default `gemini-2.5-flash` |
| `OLLAMA_BASE_URL` / `OLLAMA_MODEL` | No | local model when provider=ollama |
| `CIDADE_PADRAO` | No | default city for weather (São Paulo) |
| `IDIOMA_STT` | No | STT language (default `pt-BR`) |
| `TTS_ENGINE` / `EDGE_TTS_VOICE` / `EDGE_TTS_*` | No | TTS backend, voice, rate/pitch/volume, echo |
| `WORD_PATH`, `INSTAGRAM_HANDLE`, `FACEBOOK_PROFILE` | No | app-launching helpers |
| `YOUTUBE_VOLUME_APPS` | No | browser process names for per-app volume |
| `PLAYLIST_MUSICA/ESTUDO/TREINO` | No | YouTube playlist URLs |

## Architecture (`backend/aris/`)

```
config.py            ← pydantic-settings; reads the single root .env
assistant.py         ← AssistantEngine + build_engine() (composition root: registers skills)
core/
  context.py         ← Context: per-interaction state + speak/listen callbacks
  skill.py           ← Skill (Protocol): matches() / handle()
  registry.py        ← Registry: ordered skills; first match wins (replaces the if/elif chain)
  orchestrator.py    ← routes a command to a skill, else to the LLM (with memory injected)
llm/
  base.py            ← PERSONA + build_prompt + LLMProvider (Protocol)
  gemini_provider.py ← Google Gemini (legacy SDK; deprecation silenced in tests)
  ollama_provider.py ← local model via http://localhost:11434
  factory.py         ← build_provider() picks gemini|ollama from settings
memory/
  short_term.py      ← ShortTermMemory: deque persisted to JSON; as_prompt_context() feeds the LLM
services/            ← external/OS wrappers: weather.py (OpenWeather), volume.py (winmm + optional pycaw)
skills/              ← one skill per file: datetime, weather, playlists, notes, memory_skill, apps, volume
voice/
  stt.py             ← SpeechToText (Protocol) + GoogleSTT (SpeechRecognition, PT-BR)
  tts.py             ← TextToSpeech (Protocol) + EdgeTTS (MCI + optional echo) + Pyttsx3TTS + build_tts()
  loop.py            ← VoiceLoop: always-active loop in a daemon thread, emits events
api/
  gateway.py         ← FastAPI WebSocket: command_text / start_voice / stop_voice; broadcasts voice events
  events.py          ← pydantic event schemas
utils/dates.py       ← format_date_pt_br()
main.py              ← uvicorn entrypoint
```

### Key design decisions

- **Headless core, clients over WebSocket**: the engine never depends on a UI. The React HUD,
  the voice loop, and future clients all talk to `api/gateway.py`. Voice events
  (`state` / `user_said` / `aris_said`) are broadcast to every connected client.
- **Skill registry, not if/elif**: add a capability = new file in `skills/` implementing the
  `Skill` protocol, registered in `build_engine()`. Registration order = priority. Anything no
  skill matches falls through to the LLM.
- **Swappable LLM**: `ARIS_LLM_PROVIDER` selects Gemini (cloud) or Ollama (local) — one `.env` line.
- **Memory feeds the prompt**: `ShortTermMemory.as_prompt_context()` is injected by the
  Orchestrator (the old app persisted memory but never reused it).
- **Voice loop in a thread**: `VoiceLoop` runs blocking STT/TTS in a daemon thread and bridges
  events to the async WebSocket via `run_coroutine_threadsafe`. Interactive skills ("which city?")
  work because the voice ctx provides real speak/listen.
- **TTS fallback**: EdgeTTS (online, neural, optional echo) → pyttsx3 (offline).

## Data Files

Runtime data is written to `backend/data/` (git-ignored, auto-created): `memoria.json`
(short-term memory), `notas_aris.txt` (notes), `tts/` (temporary MP3s, deleted after playback).
The legacy `data/` at the repo root holds the old app's personal data and is kept but unused.
