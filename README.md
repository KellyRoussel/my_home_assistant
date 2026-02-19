# Personal AI Home Assistant 🤖✨

Welcome to the repository for my Personal AI Home Assistant project. This README provides a detailed technical overview of the project's components, setup, and usage.

## Table of Contents

1. [Vision](#vision)
2. [Hardware](#hardware)
3. [Software](#software)
4. [Architecture](#architecture)
    - [Wake Word Listener](#wake-word-listener)
    - [Real-Time Engine](#real-time-engine)
    - [Tools](#tools)
    - [Assistant Coordinator](#assistant-coordinator)
5. [Usage](#usage)

## Vision

The goal of this project is to create a personal AI assistant that operates on a dedicated, always-on device, such as a Raspberry Pi 4 in my case. The assistant listens for a wake word, then engages in a natural voice conversation, and can take actions based on the user's requests.

*This is a personal project I'm pursuing out of sheer enthusiasm. I hope you enjoy following along and maybe find some inspiration or useful tips along the way!*

## Hardware

- Always-on device: I've been developing on my PC, later running it on Raspberry Pi 4 for personal experience and easy use
- Microphone
- Speaker (for audio output)

## Software

- The project is in Python 🐍
- **Wake Word Detection**: [OpenWakeWord](https://github.com/dscripka/openWakeWord) with a custom "Hey Jarvis" TFLite model and a retrained scikit-learn verifier
- **Real-Time Voice Interaction**: [OpenAI Realtime API](https://platform.openai.com/docs/guides/realtime) — a single WebSocket session that handles speech recognition, LLM reasoning, and speech synthesis simultaneously
- **Weather**: [Open-Meteo](https://open-meteo.com/) (free, no API key required)
- **Todo list**: Microsoft To Do via OAuth

## Architecture

### Wake Word Listener

The `WakeWordListener` continuously monitors the microphone and fires a callback when the wake word "Hey Jarvis" is detected.

- Uses OpenWakeWord with a TFLite model (`hey_jarvis_v0.1.tflite`) and a custom-trained scikit-learn verifier (`hey_jarvis_retrained.pkl`) for reduced false positives
- Detection requires both a high per-frame score (> 0.8) and a sliding 3-frame average (> 0.6)
- Pauses the microphone stream while the assistant is responding, then resumes and reloads the model

### Real-Time Engine

The `RealTimeEngine` is the core of the voice interaction. Once triggered, it opens a bidirectional WebSocket connection to the OpenAI Realtime API and coordinates three sub-components:

- **AudioRecorder**: Captures microphone input in real time and streams base64-encoded PCM chunks to the session. Includes a silence timeout to automatically commit the audio buffer when the user stops speaking.
- **RealtimeSession**: Manages the OpenAI Realtime API connection, session configuration (model, tools, voice), and audio buffer operations.
- **EventHandler**: Processes server-sent events — streams audio delta chunks to the player as they arrive, collects user and assistant transcripts, and signals when the response is complete.
- **AudioPlayer**: Plays the streamed audio response in real time using PyAudio.

A notification sound plays as soon as the session is ready to record, giving audible feedback to the user.

### Tools

The assistant can call tools during a conversation. Tools are registered in `src/tools/tools_library.py` and passed into the Realtime session config.

Currently available tools:

| Tool | Description |
|------|-------------|
| `check_weather` | Fetches hourly weather data (temperature, precipitation, wind) for a given city and date using Open-Meteo |
| `add_todo_item_to_list` | Adds an item to a Microsoft To Do list (currently supports the `shopping` list) |

### Assistant Coordinator

The `Assistant` class in `src/assistant.py` manages the overall flow:

- **States**: `OFF`, `IDLE`, `THINKING`
- On wake word detection: pauses the listener, runs the real-time session, then resumes listening
- Conversation history (user and assistant transcripts) is persisted in the `AssistantContext` across interactions

## Usage

1. **Set up environment variables** — create a `.env` file at the project root:
    ```
    OPENAI_API_KEY=your_openai_api_key
    ```

2. **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

3. **Start the assistant:**
    ```bash
    python src/main.py
    ```

4. **Interact with the assistant:**
    - Say **"Hey Jarvis"** to wake the assistant.
    - Wait for the notification sound, then speak your request.
    - The assistant will respond in real time via audio.
    - It returns to listening mode automatically after responding.
