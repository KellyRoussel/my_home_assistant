# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A personal AI voice assistant designed to run on a Raspberry Pi 4 (developed on Windows). It listens for the wake word "Hey Jarvis", opens a bidirectional WebSocket to the OpenAI Realtime API for simultaneous speech recognition + LLM reasoning + speech synthesis, and can invoke tools during conversations.

## Running the Assistant

```bash
# Install dependencies
pip install -r requirements.txt

# CLI mode (primary)
python src/main.py

# API mode (FastAPI server on port 8000, with /json and /restart endpoints)
python src/app.py
```

**Required**: A `.env` file at the project root. See `env.example` for all variables. `OPENAI_API_KEY` is mandatory. Personal info variables (`age`, `city`, etc.) are used to personalize the system prompt via Jinja2 templating.

**Runtime dependency**: `ffplay` must be installed and on PATH (used for notification sound and audio playback).

## Source Layout

All runnable code is under `src/`. The project runs with `src/` as the working directory, so imports are relative to `src/` (e.g., `from tools.tool import Tool`, not `from src.tools.tool import Tool`).

Key files:
- [src/assistant.py](src/assistant.py) — top-level coordinator (`Assistant` class); the only place that wires all components together
- [src/config.py](src/config.py) — centralized file paths (`Config.LOGS_FILE`, `Config.NOTIFICATION_SOUND`, etc.)
- [src/logger.py](src/logger.py) — JSON file logger; use `logger.log(AppMessage(...))` / `logger.log(ErrorMessage(...))`
- [src/session/assistant_context.py](src/session/assistant_context.py) — `AssistantState` enum and `AssistantContext` (conversation memory across interactions)
- [src/session/conversation.py](src/session/conversation.py) — Jinja2-templated system prompt + per-turn message history

## Architecture

```
WakeWordListener  ──(callback)──►  Assistant._real_time_listening()
                                         │
                              RealTimeEngine.start()
                              ┌───────────────────────────────┐
                              │  RealtimeSession (WebSocket)  │
                              │  AudioRecorder (sounddevice)  │
                              │  EventHandler (events/tools)  │
                              │  AudioPlayer (ffplay/PyAudio) │
                              └───────────────────────────────┘
```

**Flow**: Wake word detected → listener paused → notification sound plays → WebSocket opened to OpenAI Realtime API → microphone streamed as base64 PCM → events processed (transcripts, audio deltas, tool calls) → audio response streamed back → WebSocket closed → listener resumed.

**Audio specs**: 24kHz, 1 channel PCM. Silence timeout: 1000ms to auto-commit buffer.

**Wake word detection**: OpenWakeWord TFLite model (`hey_jarvis_v0.1.tflite`) + scikit-learn verifier (`hey_jarvis_retrained.pkl`). Requires per-frame score > 0.8 AND 3-frame sliding average > 0.6.

## Adding a New Tool

1. Create a new class inheriting from `Tool` ([src/tools/tool.py](src/tools/tool.py)):
   - Implement `tool_name` (str), `description` (str), `parameters` (list of `ToolParameter`), and `execute(**kwargs)`
   - `json_definition` and `json_definition_flatten` are auto-generated from these
2. Register the tool in [src/tools/tools_library.py](src/tools/tools_library.py) — add an instance to the `tools` dict

The `execute()` method is synchronous and called automatically by `EventHandler` when the LLM invokes the tool.

## Deployment

```bash
# Deploy to Raspberry Pi (Linux)
./deploy.sh

# Deploy from Windows
deploy.bat
```

Both scripts use rsync/scp to sync files to the Pi over SSH.

## Logging

All runtime events are appended to `logs.json` at the project root as newline-delimited JSON. Use `GET /json` (API mode) to retrieve them. Message types: `AppMessage`, `ErrorMessage` (imported from `src/logger.py`).
