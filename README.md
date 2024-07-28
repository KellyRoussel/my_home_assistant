# Personal AI Home Assistant 🤖✨

Welcome to the repository for my Personal AI Home Assistant project. This README provides a detailed technical overview of the project's components, setup, and usage.

## Table of Contents

1. [Vision](#vision)
2. [Hardware](#hardware)
3. [Software](#software)
4. [Architecture](#architecture)
    - [Action Listener](#action-listener)
    - [Recorder](#recorder)
    - [Transcriber](#transcriber)
    - [LLM Engine](#llm-engine)
    - [Text-to-Speech (TTS)](#text-to-speech-tts)
    - [Assistant Coordinator](#assistant-coordinator)
5. [Usage](#usage)

## Vision

The goal of this project is to create a personal AI assistant that operates on a dedicated, always-on device, such as a Raspberry Pi 4 in my case. The assistant is designed to listen for user commands, process them, and respond appropriately, eventually taking action based on the user's requests.

*This is a personal project I'm pursuing out of sheer enthusiasm. I hope you enjoy following along and maybe find some inspiration or useful tips along the way!

## Hardware

- Always-on device: I've been developing on my PC, later running it on Raspberry Pi 4 for personal experience and easy use
- Microphone
- Physical Raspberry GPIO button or Bluetooth button or KeyBoard (for Action Listener)
- Speaker (for Text-to-Speech output)

## Software

- The project is in Python 🐍
- **Speech-To-Text (STT)**: Whisper API used for now
- **Large Language Model (LLM)**: OpenAI's API or Groq's API implemented for now
- **Text-To-Speech (TTS)**: DeepGram, ElevenLabs, OpenAI services implemented for now


## Architecture

### Action Listener

The Action Listener captures the user's intention to interact with the assistant. It can be triggered by a physical button, a keyboard key, or a Bluetooth button.

- **Keyboard Action Listener:** Detects specific key events (e.g., space bar).
- **Button Action Listener:** Utilizes Raspberry Pi GPIOs for a wired button.
- **Bluetooth Action Listener:** Detects button press events via Bluetooth.

> Choose which one to use in `src/assistant.py`

### Recorder

The Recorder captures audio input from the microphone. It uses the `sounddevice` package for recording on the Raspberry Pi.

- **Methods:**
    - `start_recording()`: Begins the recording session.
    - `stop_recording()`: Ends the recording session and saves the audio.
    - `record()`: Continuously captures audio chunks until stopped.

### Transcriber

The Transcriber converts recorded audio into text using the OpenAI Whisper API.

- **Methods:**
    - `transcribe(audio_file)`: Sends the audio file to Whisper API and returns the transcribed text.

### LLM Engine

The LLM Engine generates responses based on the transcribed text. It uses a large language model to produce contextually relevant replies.

- **Methods:**
    - `generate_response(prompt)`: Sends the prompt to the LLM and returns the generated response.
  
> Choose model and API service in `src>llm_engine>llm_engine.py`

### Text-to-Speech (TTS)

The TTS component converts the generated text response into audible speech.

- **Methods:**
    - `speak(text)`: Sends the text to the TTS service and plays the audio.

> Deepgram, ElevenLabs and OpenAI implemented. Choose the service to use in `src/assistant.py`

### Assistant Coordinator

The Assistant Coordinator manages the overall flow and state transitions of the assistant.

- **States:**
    - `OFF`: The assistant is inactive.
    - `IDLE`: The assistant is ready and waiting for input.
    - `RECORDING`: The assistant is capturing audio.
    - `TRANSCRIBING`: The assistant is converting audio to text.
    - `THINKING`: The assistant is generating a response.
    - `SPEAKING`: The assistant is delivering the response.

## Usage

1. **Start the assistant:**
    ```bash
    python src/main.py
    ```

2. **Interact with the assistant:**
    - Press the designated button to start recording.
    - Speak your command.
    - Release the button to stop recording and wait for the response.
