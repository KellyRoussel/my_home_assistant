# Home Assistant Project: Key components & Orchestration

## Introduction

This part of the project focuses on creating the structural foundation of the Home Assistant with all necessary key components and the orchestrator to arrange those and run the magic. For now, the assistant is designed to trigger audio recording via the space bar and process the recorded data to provide meaningful responses.

## Components Overview

### 1. KeyboardActionListener
This component detects keyboard events, specifically the pressing and releasing of the space bar, to control the recording.
In the future, we could image other ways of starting/stopping the audio record. The idea here is to simulate an intercom.

#### Key Methods:
- `_on_press(key)`: Triggers the recording start function when the space bar is pressed.
- `_on_release(key)`: Triggers the recording stop function when the space bar is released.
- `start_listening()`: Starts the listener thread to monitor keyboard events.
- `set_press_callback(callback)`: Sets the callback function for the press event.
- `set_release_callback(callback)`: Sets the callback function for the release event.

### 2. Recorder
The `Recorder` component is responsible for capturing audio streams from the microphone. It utilizes the PyAudio library and the Record class to manage the recording process.

#### Key Methods:
- `start_recording(output_filename)`: Initializes the recording process and opens the audio stream.
- `stop_recording()`: Stops the recording, saves the audio to a file, and returns the record object.
- `record(output_filename)`: Initiates a continuous recording loop and appends audio chunks until `is_recording` is set to `False`.
- `reset_record()`: Resets the current recording session.

### 5. Transcriber
The `Transcriber` class transcribes recorded audio files. For now, it is using Whisper, an ASR (Automatic Speech Recognition) model from OpenAI.
We could have used some streaming model, taking an audio-stream as input and starting to transcribe from this byte. Maybe this could speed a little bit the process but the choice of whisper was in the idea to one day make it run locally. However, for now, the API online version quality is much higher than a "base" whisper model running on my PC and the price is really low so I think it's a good fit. Moreover, the next steps (LLM engine call) requires the full transcription to start so I'm not sure the time gain would be that interesting... to be tested!

#### Key Methods:
- `transcribe_online(audio_filename)`: Utilizes the OpenAI API to produce real-time transcription of the audio file.
- `transcribe_local(audio_filename)`: Uses a local instance of Whisper to transcribe audio without internet dependency. (not used for now)


### 6. LLM Engine
The LLM Engine handles the interaction with an LLM to generate responses based on the recorded and transcribed conversation. For now, I choose to use GPT-4o which is actually the best model I know to test my architecture at its best. However, for privacy, pricing, tech-curiosity and ecological reasons, I plan to try other smaller, local, open-source models like Mistral's or Llamas.

#### Key Methods:
- `gpt_call(conversation)`: Sends the current conversation context to GPT and retrieves the response. This method uses a predefined prompt template to maintain consistency in responses.


### 7. Speaker
The `Speaker` component converts text responses to speech using DeepGram's TTS (Text to Speech) service and plays the audio output.
DeepGram TTS is a personal choice because I really like the voices they provide, I think they sound really natural. A drawback at current time is that they do not provide french voices. Nevermind, my first assistant version will be in english.

#### Key Methods:
- `speak(text)`: Streams the audio bytes from DeepGram and directs them to a player to produce sound output.

### 8. Assistant
The `Assistant` class coordinates the previous functionalities sequences. The assistant adopts a state machine approach to manage different states during the interaction process:

- `OFF`: The assistant is inactive.
- `IDLE`: The assistant is waiting for user input.
- `RECORDING`: The assistant is in the process of recording audio.
- `TRANSCRIBING`: The assistant is transcribing the recorded audio.
- `THINKING`: The assistant is processing the transcription to generate a response.
- `SPEAKING`: The assistant is converting the text response to speech and playing it.

#### Key Methods:
- `__init__()`: Initializes components such as Recorder, KeyboardActionListener, LLMEngine, Speaker, and context. Sets up state and keyboard event callbacks.
- `_start_recording()`: Checks if the state is idle, starts recording, and initializes a new thread for recording.
- `_stop_recording()`: Stops recording, transcribes audio, and transitions to the thinking state.
- `_think()`: Generates a response using GPT based on the current conversation context.
- `_speak(response)`: Uses DeepGram to convert text responses to speech and plays the audio.
- `start()`: Initiates the assistant and begins listening for keyboard events.
- `stop()`: Terminates recording and sets the assistant state to OFF.



## Assistant Workflow
1. **Initialization**: An instance of the `Assistant` class is created and its `start()` method is called.
2. **Listening**: The `KeyboardActionListener` monitors for space bar events.
3. **Recording**: When the space bar is pressed, `_start_recording()` is triggered.
4. **Transcribing & Thinking**: Upon release of the space bar, `_stop_recording()` is called, which stops the recording, transcribes the audio, updates the conversation context, and invokes `_think()`.
5. **Responding**: `_think()` interacts with GPT to generate a response, which is then passed to `_speak()`.
6. **Speaking**: `_speak()` converts the text response to speech and plays it.

## Dependencies
- PyAudio
- pynput
- openai
- whisper
- deepgram
- jinja2

## Conclusion
This part of the project establishes the core functionalities of the Home Assistant, ensuring seamless interaction between audio recording, STT, response generation and TTS. The state management mechanisms ensure a smooth and logical flow between the different stages of interaction.